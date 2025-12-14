import json
import requests
import re
from html import unescape
import os

REST_COUNTRIES_URL = (
    "https://restcountries.com/v3.1/all"
    "?fields=name,cca2,region,subregion,population,capital"
)

TRAVEL_ADVISORY_URL = "https://cadataapi.state.gov/api/TravelAdvisories"

TOURISM_CODES = [
    # Europe
    "FR",
    "IT",
    "ES",
    "DE",
    "GB",
    "CH",
    "AT",
    "NL",
    "BE",
    "PT",
    "GR",
    "CZ",
    "HU",
    "PL",
    "HR",
    "TR",
    "IE",
    "DK",
    "NO",
    "SE",
    "FI",
    # Asia
    "JP",
    "KR",
    "CN",
    "TH",
    "SG",
    "MY",
    "VN",
    "ID",
    "PH",
    "AE",
    "IN",
    # North America
    "US",
    "CA",
    "MX",
    # South America
    "BR",
    "AR",
    "CL",
    "PE",
    "CO",
    # Oceania
    "AU",
    "NZ",
    # Middle East / Africa
    "IL",
    "SA",
    "EG",
    "MA",
    "ZA",
]

RISK_KEYWORDS = {
    "unrest": "unrest / protests",
    "crime": "violent or petty crime",
    "kidnapping": "kidnapping risk",
    "landmine": "landmines / unexploded ordnance",
    "terrorism": "terrorism risk",
    "health": "limited health facilities",
    "disease": "infectious disease / outbreaks",
    "epidemic": "epidemics / outbreaks",
    "natural disaster": "natural hazards",
}

MANUAL_SAFETY_PRESETS = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def html_to_text(html: str) -> str:
    """Convert advisory HTML summary into normalized plain text."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    text = " ".join(text.split())
    return text.lower()


def extract_top_risks_from_summary(summary_html: str):
    """Extract up to 3 risk tags from an advisory summary."""
    text = html_to_text(summary_html)
    if not text:
        return []
    tags = []
    for kw, label in RISK_KEYWORDS.items():
        if kw in text:
            tags.append(label)
    seen = set()
    deduped = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped[:3]


def get_advisory_excerpt(summary_html: str, max_len: int = 260) -> str:
    """Create a short excerpt suitable for UI display."""
    text = html_to_text(summary_html)
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def default_risk_scores_from_level(overall: str):
    """Default 1–5 risk scores based on overall advisory level."""
    overall = (overall or "").strip().lower()
    if overall == "low":
        return {"crime": 2, "political": 2, "health": 2, "natural_disaster": 2}
    elif overall == "medium":
        return {"crime": 3, "political": 3, "health": 2, "natural_disaster": 3}
    elif overall == "high":
        return {"crime": 4, "political": 4, "health": 3, "natural_disaster": 3}
    else:  # unknown
        return {"crime": 3, "political": 3, "health": 3, "natural_disaster": 3}


def fetch_rest_countries():
    print("Fetching REST Countries data...")
    resp = requests.get(REST_COUNTRIES_URL, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    by_code = {}
    for item in data:
        code = item.get("cca2")
        if not code:
            continue
        name = item.get("name", {}).get("common", "")
        region = item.get("region", "")
        subregion = item.get("subregion", "")
        by_code[code.upper()] = {
            "code": code.upper(),
            "name": name,
            "region": region,
            "subregion": subregion,
            "population": item.get("population"),
            "capital": (
                item.get("capital") or ["N/A"]
            )[0],
        }
    print(f"Got {len(by_code)} countries from REST Countries.")
    return by_code


def fetch_travel_advisories():
    try:
        print("Fetching US travel advisory data...")
        resp = requests.get(TRAVEL_ADVISORY_URL, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        print(f"Got {len(data)} advisory records.")
        return data
    except Exception as e:
        print(f"[WARN] Failed to fetch advisory API: {e}")
        return []


def build_advisory_index(records, rest_countries):
    """Build an index: {ISO2: {overall, raw, summary, link}}."""
    index = {}

    name_to_code = {}
    for code, c in rest_countries.items():
        name_lower = (c["name"] or "").strip().lower()
        if name_lower:
            name_to_code[name_lower] = code
    
    aliases = {
        "burma": "MM",  # Myanmar
        "myanmar": "MM",
        "east timor": "TL",  # Timor-Leste
        "timor-leste": "TL",
        "czech republic": "CZ",
        "czechia": "CZ",
        "russia": "RU",
        "russian federation": "RU",
        "south korea": "KR",
        "republic of korea": "KR",
        "north korea": "KP",
        "democratic people's republic of korea": "KP",
        "ivory coast": "CI",
        "cote d'ivoire": "CI",
        "cote d ivoire": "CI",
        "cabo verde": "CV",
        "cape verde": "CV",
        "the bahamas": "BS",
        "bahamas": "BS",
        "the gambia": "GM",
        "gambia": "GM",
        "mexico": "MX",
    }
    for alias, code in aliases.items():
        if code in rest_countries:
            name_to_code[alias.lower()] = code

    def normalize_country_name(name):
        """Normalize country name for matching."""
        if not name:
            return ""
        name = name.replace("Travel Advisory", "").strip()
        name = re.sub(r"\s*\([^)]*\)", "", name)
        name = re.sub(r"^the\s+", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\s+", " ", name).strip()
        return name.lower()

    matched_count = 0
    unmatched = []

    for item in records:
        title = item.get("Title") or ""
        if not title:
            continue

        if " - Level" in title:
            parts = title.split(" - Level")
            country_name = parts[0].strip()
            level_part = "Level" + parts[1]  # "Level 4: Do Not Travel"
        else:
            continue

        level_num = None
        for n in ["1", "2", "3", "4"]:
            if f"Level {n}" in level_part:
                level_num = int(n)
                break

        if level_num is None:
            continue

        if level_num == 1:
            overall = "low"
        elif level_num == 2:
            overall = "medium"
        else:
            overall = "high"

        normalized_name = normalize_country_name(country_name)
        
        if "," in normalized_name or "&" in normalized_name:
            first_part = normalized_name.split(",")[0].split("&")[0].strip()
            first_part = re.sub(r'\bmainland\b', '', first_part, flags=re.IGNORECASE).strip()
            first_part = re.sub(r'\bsee summaries\b', '', first_part, flags=re.IGNORECASE).strip()
            if first_part:
                normalized_name = first_part
        
        code = name_to_code.get(normalized_name)
        
        if not code:
            for key, val in aliases.items():
                if normalized_name == key or normalized_name in key or key in normalized_name:
                    code = val
                    break
            
            if not code:
                for key, val in name_to_code.items():
                    if normalized_name in key or key in normalized_name:
                        code = val
                        break
        
        if not code:
            unmatched.append(country_name)
            continue

        matched_count += 1
        index[code] = {
            "raw": level_part.strip(),
            "overall": overall,
            "summary": item.get("Summary") or "",
            "link": item.get("Link") or "",
        }

    print(f"Built advisory index for {len(index)} countries.")
    if unmatched:
        print(f"Unmatched ({len(unmatched)}): {', '.join(unmatched[:10])}")
    return index


def merge_country_safety():
    rest_countries = fetch_rest_countries()
    advisory_records = fetch_travel_advisories()
    advisory_index = build_advisory_index(advisory_records, rest_countries)

    result = {}

    for code, base in rest_countries.items():
        preset = MANUAL_SAFETY_PRESETS.get(code, {})
        advisory = advisory_index.get(code)
        is_core = code in TOURISM_CODES

        if advisory and advisory.get("overall"):
            overall_risk = advisory["overall"]
        elif "overall_risk" in preset:
            overall_risk = preset["overall_risk"]
        else:
            overall_risk = "unknown"

        base_scores = default_risk_scores_from_level(overall_risk)
        merged_scores = {
            **base_scores,
            **preset.get("risk_scores", {}),
        }

        summary_html = advisory["summary"] if advisory else ""
        auto_risks = extract_top_risks_from_summary(summary_html)
        if "top_risks" in preset:
            top_risks = preset["top_risks"]
        elif auto_risks:
            top_risks = auto_risks
        else:
            top_risks = [
                "keep valuables close in busy areas",
                "check local news if something feels unusual",
            ]

        excerpt = get_advisory_excerpt(summary_html) if summary_html else ""
        advisory_link = advisory["link"] if advisory else ""

        emergency_contacts = preset.get(
            "emergency_contacts",
            {
                "police": "Local police emergency number",
                "ambulance": "Local medical emergency number",
                "fire": "Local fire emergency number",
                "note": "Look up these numbers before or right after arrival.",
            },
        )

        merged = {
            "code": code,
            "name": base["name"],
            "region": base["region"] or preset.get("region", ""),
            "subregion": base.get("subregion", ""),
            "overall_risk": overall_risk,
            "risk_scores": merged_scores,
            "top_risks": top_risks,
            "emergency_contacts": emergency_contacts,
            "mindset_tip": preset.get(
                "mindset_tip",
                "Most trips go well. Keep a basic safety routine and share your itinerary with someone you trust.",
            ),
            "playbook": preset.get("playbook", {}),
            "advisory_excerpt": preset.get("advisory_excerpt", excerpt),
            "advisory_link": advisory_link or preset.get("advisory_link", ""),
            "is_core_country": is_core,
        }

        result[code] = merged

    return result


def main():
    data = merge_country_safety()

    subset = data

    out_path = os.path.join(BASE_DIR, "data", "processed.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(subset, f, ensure_ascii=False, indent=2)

    print("Written processed safety JSON with", len(subset), "countries:", out_path)


if __name__ == "__main__":
    main()
