import json
import time
import requests
import re
from html import unescape

REST_COUNTRIES_URL = (
    "https://restcountries.com/v3.1/all"
    "?fields=name,cca2,region,subregion,population,capital"
)

# 美国 Travel Advisory API（字段名字可能会变，跑一次 print 看）
TRAVEL_ADVISORY_URL = "https://cadataapi.state.gov/api/TravelAdvisories"

# 你的手动 safety preset（可逐步扩展）
MANUAL_SAFETY_PRESETS = {
    "FR": {
        "overall_risk": "medium",
        "risk_scores": {
            "crime": 3,
            "political": 2,
            "health": 1,
            "natural_disaster": 2,
        },
        "top_risks": [
            "petty theft in crowded areas",
            "transport strikes & delays",
            "tourist scams around landmarks",
        ],
        "emergency_contacts": {
            "police": "17 (or 112 EU emergency)",
            "ambulance": "15 (or 112)",
            "fire": "18 (or 112)",
            "note": "In practice, 112 works across the EU for any emergency.",
        },
        "mindset_tip": (
            "Most trips to France are smooth. Stay aware in busy tourist spots, "
            "keep valuables close, and give yourself extra time for transport disruptions."
        ),
        "playbook": {
            "lost_passport": {
                "label": "Lost passport or stolen bag",
                "steps": [
                    "Move to a safe, well-lit place away from the incident area.",
                    "Call your card providers to freeze cards and secure online accounts.",
                    "File a police report and get a written statement.",
                    "Contact your embassy or consulate with the police report.",
                    "Use printed or offline copies of bookings and IDs while things are being reissued.",
                ],
            },
            "protest_or_strike": {
                "label": "Protests, strikes or sudden disruption",
                "steps": [
                    "Avoid crowds and demonstrations, even if they look peaceful.",
                    "Check transport apps and airline / train notifications.",
                    "Have one backup way to reach your accommodation.",
                    "Keep a calm distance from police lines.",
                    "Let someone you trust know where you are.",
                ],
            },
        },
    },
    "JP": {
        "overall_risk": "low",
        "risk_scores": {
            "crime": 1,
            "political": 1,
            "health": 1,
            "natural_disaster": 3,
        },
        "top_risks": [
            "earthquakes and typhoons",
            "language barrier in emergencies",
            "lost items on crowded trains",
        ],
        "emergency_contacts": {
            "police": "110",
            "ambulance": "119",
            "fire": "119",
            "note": "Point to a map or use simple English; many officers have basic English.",
        },
        "mindset_tip": (
            "Japan is generally very safe. Stay weather-aware and know basic earthquake reactions."
        ),
        "playbook": {
            "earthquake": {
                "label": "Earthquake while you’re outside or on transport",
                "steps": [
                    "Stay calm and protect your head.",
                    "Hold onto straps or poles on trains and wait for staff instructions.",
                    "Avoid elevators right after a quake.",
                    "Follow official announcements and signage.",
                ],
            },
            "lost_items": {
                "label": "Lost phone, wallet or bag",
                "steps": [
                    "Retrace your last steps and ask staff at the nearest station / shop.",
                    "Use device locator features if available.",
                    "File a lost item report at a police box (kōban) or station office.",
                    "Note time, place and train details if relevant.",
                ],
            },
        },
    },
    "IT": {
        "overall_risk": "medium",
        "risk_scores": {
            "crime": 3,
            "political": 2,
            "health": 1,
            "natural_disaster": 2,
        },
        "top_risks": [
            "pickpocketing in tourist hubs",
            "heat waves in summer",
            "transport delays or strikes",
        ],
        "emergency_contacts": {
            "police": "112",
            "ambulance": "118 (or 112)",
            "fire": "115",
            "note": "112 is the general EU emergency number.",
        },
        "mindset_tip": (
            "Enjoy the streets and food, but keep your bag closed and in front of you in crowded places."
        ),
        "playbook": {
            "theft": {
                "label": "Pickpocketing or bag theft",
                "steps": [
                    "Move somewhere calmer, away from the immediate crowd.",
                    "Lock or wipe your phone remotely if possible.",
                    "Report the theft and obtain a written report.",
                    "Contact your bank to block cards.",
                ],
            },
            "heat_wave": {
                "label": "Heat wave or heat exhaustion",
                "steps": [
                    "Get into shade or an air-conditioned space.",
                    "Drink water slowly and avoid alcohol.",
                    "Use wet cloths on neck and wrists to cool down.",
                    "Seek medical help if you feel confused or very weak.",
                ],
            },
        },
    },
}


def fetch_rest_countries():
    print("Fetching REST Countries data…")
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
    """
    拉美国旅行预警。这里无法在线测试字段名，
    所以建议你第一次跑完之后，print 一条样例看结构，再稍微改一下解析。
    """
    try:
        print("Fetching US travel advisory data…")
        resp = requests.get(TRAVEL_ADVISORY_URL, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        print(f"Got {len(data)} advisory records.")
        return data
    except Exception as e:
        print(f"[WARN] Failed to fetch advisory API: {e}")
        return []


def build_advisory_index(records, rest_countries):
    """
    把 Travel Advisory 列表转成：
      {countryCode: {overall, raw, summary, link}}
    """
    index = {}

    # name -> code 索引，方便用“France” 找到 "FR"
    name_to_code = {}
    for code, c in rest_countries.items():
        name_lower = (c["name"] or "").strip().lower()
        if name_lower:
            name_to_code[name_lower] = code

    for item in records:
        title = item.get("Title") or ""
        if not title:
            continue

        # 例："South Sudan - Level 4: Do Not Travel"
        parts = title.split(" - Level")
        if len(parts) < 2:
            continue

        country_name = parts[0].strip()
        level_part = "Level" + parts[1]  # "Level 4: Do Not Travel"

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

        code = name_to_code.get(country_name.lower())
        if not code:
            continue

        index[code] = {
            "raw": level_part.strip(),
            "overall": overall,
            "summary": item.get("Summary") or "",
            "link": item.get("Link") or "",
        }

    print(f"Built advisory index for {len(index)} countries.")
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

        # 1. overall_risk：官方 Level > preset > unknown
        if advisory and advisory.get("overall"):
            overall_risk = advisory["overall"]
        elif "overall_risk" in preset:
            overall_risk = preset["overall_risk"]
        else:
            overall_risk = "unknown"

        # 2. risk_scores：先用 Level 默认，再让 preset 覆盖
        base_scores = default_risk_scores_from_level(overall_risk)
        merged_scores = {
            **base_scores,
            **preset.get("risk_scores", {}),
        }

        # 3. top_risks：preset 优先，否则从 Summary 抽关键词，否则 generic
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

        # 4. advisory 摘要 & 链接
        excerpt = get_advisory_excerpt(summary_html) if summary_html else ""
        advisory_link = advisory["link"] if advisory else ""

        # 5. 紧急联系方式：核心国家用 preset，非核心用 generic fallback
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

    # 方案 1：导出全量 250 个国家（推荐现在先这样，前端再做 Rich/Basic）
    subset = data

    # 如果你以后想只导出 tourism subset，可以用：
    # subset = {code: data[code] for code in TOURISM_CODES if code in data}

    with open("country_safety.json", "w", encoding="utf-8") as f:
        json.dump(subset, f, ensure_ascii=False, indent=2)

    print("Written country_safety.json with", len(subset), "countries.")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()

TOURISM_CODES = [
    # Europe
    "FR","IT","ES","DE","GB","CH","AT","NL","BE","PT","GR","CZ","HU","PL","HR","TR","IE","DK","NO","SE","FI",
    # Asia
    "JP","KR","CN","TH","SG","MY","VN","ID","PH","AE","IN",
    # North America
    "US","CA","MX",
    # South America
    "BR","AR","CL","PE","CO",
    # Oceania
    "AU","NZ",
    # Middle East / Africa (可按需删减或增加)
    "IL","SA","EG","MA","ZA",
]

# 从 Summary 里抽风控标签用的关键词
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


def html_to_text(html: str) -> str:
    """把 advisory Summary 的 HTML 粗略转成纯文本、小写。"""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    text = " ".join(text.split())
    return text.lower()


def extract_top_risks_from_summary(summary_html: str):
    """根据关键字从 Summary 里抽取最多 3 个 risk tag。"""
    text = html_to_text(summary_html)
    if not text:
        return []
    tags = []
    for kw, label in RISK_KEYWORDS.items():
        if kw in text:
            tags.append(label)
    # 去重并截取前三个
    seen = set()
    deduped = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped[:3]


def get_advisory_excerpt(summary_html: str, max_len: int = 260) -> str:
    """从 Summary 里截一小段摘要，用于 Crisis 页面展示。"""
    text = html_to_text(summary_html)
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def default_risk_scores_from_level(overall: str):
    """根据 overall_risk 给出一个有区分度的默认 risk_scores。"""
    overall = (overall or "").strip().lower()
    if overall == "low":
        return {"crime": 2, "political": 2, "health": 2, "natural_disaster": 2}
    elif overall == "medium":
        return {"crime": 3, "political": 3, "health": 2, "natural_disaster": 3}
    elif overall == "high":
        return {"crime": 4, "political": 4, "health": 3, "natural_disaster": 3}
    else:  # unknown
        return {"crime": 3, "political": 3, "health": 3, "natural_disaster": 3}
