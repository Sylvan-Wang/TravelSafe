import json
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import re
from html import unescape
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import os
import warnings
import unicodedata

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _here(*parts: str) -> str:
    return os.path.join(BASE_DIR, *parts)


def _safe_float(x):
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    try:
        return float(x)
    except Exception:
        return None


def _safe_int(x):
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    try:
        return int(x)
    except Exception:
        return None


def _strip_accents(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)
    )


def load_gpi_2025_scores(pdf_path: str, cache_csv_path: str = None) -> pd.DataFrame:
    """
    Extract 2025 Global Peace Index (GPI) overall scores from the official PDF report.

    Returns a DataFrame with columns:
      - country_gpi: country name as written in the PDF ranking table
      - gpi_score: numeric score (lower is more peaceful)
      - gpi_rank: numeric rank (ties share the same rank; gaps may exist)

    Notes:
    - The PDF contains a ranking table where each row is roughly:
        RANK COUNTRY SCORE CHANGE ...
      Some country names wrap across lines; we parse the token stream instead of line-by-line.
    - If cache_csv_path is provided and exists, it will be loaded instead of re-parsing the PDF.
    """
    if cache_csv_path and os.path.exists(cache_csv_path):
        df_cache = pd.read_csv(cache_csv_path)
        if (
            {"country_gpi", "gpi_score"}.issubset(set(df_cache.columns))
            and 150 <= df_cache["country_gpi"].nunique() <= 170
        ):
            return df_cache

    try:
        from pypdf import PdfReader
    except Exception as e:
        raise RuntimeError(
            "Missing dependency 'pypdf'. Install with: pip install pypdf"
        ) from e

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"GPI PDF not found: {pdf_path}. Provide the PDF or a cached CSV."
        )

    reader = PdfReader(pdf_path)

    # The overall ranking table is adjacent to pages that contain the header:
    # "RANK COUNTRY SCORE CHANGE" (multi-column table).
    # We parse the header page plus its immediate previous page (where the top ranks are listed).
    score_token_re = re.compile(r"^\d\.\d{3}$")
    rank_token_re = re.compile(r"^=?\d{1,3}$")

    header_pages = []
    for i, page in enumerate(reader.pages):
        t = (page.extract_text() or "")
        if "RANK COUNTRY SCORE CHANGE" in t:
            header_pages.append(i)

    if header_pages:
        pages_to_parse = sorted(
            set(header_pages + [p - 1 for p in header_pages if p > 0])
        )
    else:
        pages_to_parse = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            tokens = text.replace("\n", " ").split()
            score_hits = sum(1 for t in tokens if score_token_re.match(t))
            rank_hits = sum(1 for t in tokens if rank_token_re.match(t))
            if score_hits >= 60 and rank_hits >= 60:
                pages_to_parse.append(i)

        if not pages_to_parse:
            raise RuntimeError("Could not locate ranking pages in the GPI PDF.")

    rows = []
    for i in pages_to_parse:
        text = reader.pages[i].extract_text() or ""
        cleaned = " ".join(text.replace("\n", " ").split())
        tokens = cleaned.split()

        j = 0
        while j < len(tokens):
            tok = tokens[j]
            if not rank_token_re.match(tok):
                j += 1
                continue

            rank = int(tok.lstrip("="))
            j += 1

            country_parts = []
            while j < len(tokens) and not score_token_re.match(tokens[j]):
                if rank_token_re.match(tokens[j]) and country_parts:
                    break
                country_parts.append(tokens[j])
                j += 1

            if j >= len(tokens) or not score_token_re.match(tokens[j]):
                continue

            score = float(tokens[j])
            j += 1

            country = " ".join(country_parts).strip()
            country = country.replace("Y emen", "Yemen")
            country = re.sub(r"\s+", " ", country).strip()
            if country and country.upper() != "COUNTRY":
                rows.append(
                    {"country_gpi": country, "gpi_score": score, "gpi_rank": rank}
                )

            if j < len(tokens):
                change_tok = tokens[j]
                if change_tok in {"↔", "UP-LONG", "DOWN-LONG", "UP", "DOWN", "NEW"}:
                    j += 1
                    if (
                        change_tok in {"UP-LONG", "DOWN-LONG", "UP", "DOWN"}
                        and j < len(tokens)
                        and rank_token_re.match(tokens[j])
                    ):
                        j += 1

    df = pd.DataFrame(rows)
    if df.empty or df["country_gpi"].nunique() < 150:
        raise RuntimeError(
            f"GPI extraction seems incomplete (rows={len(df)}, unique_countries={df['country_gpi'].nunique()})."
        )

    df = df.drop_duplicates(subset=["country_gpi"], keep="first").copy()

    if cache_csv_path:
        try:
            df.to_csv(cache_csv_path, index=False)
        except Exception:
            pass

    return df


def run_analysis():
    print("Starting TravelSafe Analysis...")

    print("1. Fetching REST Countries data...")
    REST_COUNTRIES_URL = (
        "https://restcountries.com/v3.1/all"
        "?fields=name,cca2,cca3,region,subregion,population,capital"
    )
    try:
        resp = requests.get(REST_COUNTRIES_URL, timeout=20)
        resp.raise_for_status()
        countries_data = resp.json()

        countries_list = []
        for item in countries_data:
            code = item.get("cca2")
            if not code:
                continue
            name = item.get("name", {}).get("common", "")
            countries_list.append(
                {
                    "code_2": code.upper(),
                    "code_3": item.get("cca3", ""),
                    "country": name,
                    "region": item.get("region", ""),
                    "subregion": item.get("subregion", ""),
                    "population": item.get("population", 0),
                    "capital": (item.get("capital") or ["N/A"])[0],
                }
            )
        df_countries = pd.DataFrame(countries_list)
        print(f"   Loaded {len(df_countries)} countries.")
    except Exception as e:
        print(f"   Error fetching REST Countries: {e}")
        return

    print("2. Scraping Wikipedia Homicide Rates...")
    WIKIPEDIA_URL = (
        "https://en.wikipedia.org/wiki/List_of_countries_by_intentional_homicide_rate"
    )
    df_homicide = pd.DataFrame(columns=["country_wiki", "homicide_rate"])
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        }
        resp = requests.get(WIKIPEDIA_URL, timeout=30, headers=headers)
        resp.raise_for_status()

        from io import StringIO

        tables = pd.read_html(StringIO(resp.text))

        target_table = None
        for table in tables:
            cols = str(table.columns).lower()
            if (
                len(table) > 50
                and ("country" in cols or "location" in cols)
                and ("rate" in cols)
            ):
                target_table = table
                break

        if target_table is None and len(tables) > 0:
            target_table = max(tables, key=len)

        if target_table is not None:
            target_table.columns = [str(c).lower() for c in target_table.columns]

            country_col = next(
                (c for c in target_table.columns if "country" in c or "location" in c),
                target_table.columns[0],
            )
            rate_col = next((c for c in target_table.columns if "rate" in c), None)

            if rate_col:
                df_homicide = target_table[[country_col, rate_col]].copy()
                df_homicide.columns = ["country_wiki", "homicide_rate"]
                df_homicide["homicide_rate"] = pd.to_numeric(
                    df_homicide["homicide_rate"], errors="coerce"
                )
                df_homicide.dropna(subset=["homicide_rate"], inplace=True)
                df_homicide["country_wiki"] = (
                    df_homicide["country_wiki"]
                    .astype(str)
                    .apply(lambda x: re.sub(r"[*\d\[\]]", "", x).strip())
                )
                print(f"   Loaded {len(df_homicide)} homicide records.")
    except Exception as e:
        print(f"   Error scraping Wikipedia: {e}")

    print("3. Loading Global Peace Index (GPI) 2025 from PDF...")
    GPI_PDF = _here("Global-Peace-Index-2025-web.pdf")
    GPI_CACHE = _here("gpi_2025_extracted.csv")

    df_gpi = pd.DataFrame(columns=["country_gpi", "gpi_score", "gpi_rank"])
    try:
        pdf_path = GPI_PDF if os.path.exists(GPI_PDF) else GPI_PDF
        df_gpi = load_gpi_2025_scores(pdf_path=pdf_path, cache_csv_path=GPI_CACHE)
        df_gpi["gpi_score"] = pd.to_numeric(df_gpi["gpi_score"], errors="coerce")
        print(f"   Loaded {len(df_gpi)} GPI records.")
    except Exception as e:
        print(f"   Error loading GPI PDF: {e}")

    print("4. Loading US Advisories...")
    ADVISORY_FILE = _here("us_advisories_manual.csv")

    df_advisory = pd.DataFrame(columns=["code_2", "advisory_level"])
    if os.path.exists(ADVISORY_FILE):
        try:
            df_advisory = pd.read_csv(ADVISORY_FILE)
            if "country_code" in df_advisory.columns:
                df_advisory = df_advisory.rename(
                    columns={"country_code": "code_2", "advisory_level": "advisory_level"}
                )
            df_advisory = df_advisory[["code_2", "advisory_level"]]
            print(f"   Loaded {len(df_advisory)} advisory records.")
        except Exception as e:
            print(f"   Error loading advisories: {e}")

    print("5. Merging Data...")

    def normalize_name(name):
        if pd.isna(name):
            return ""
        name = _strip_accents(str(name)).lower().strip()
        name = re.sub(r"\s*\(.*\)", "", name)
        name = re.sub(r"[*†]", "", name)
        name = name.replace("the ", "")
        name = name.replace("republic of ", "")
        name = name.replace("kingdom of ", "")
        name = name.replace("state of ", "")
        return name.strip()

    df_master = df_countries.copy()
    df_master = df_master.drop_duplicates(subset=["code_2"])

    df_master["name_norm"] = df_master["country"].apply(normalize_name)

    if not df_homicide.empty:
        df_homicide["name_norm"] = df_homicide["country_wiki"].apply(normalize_name)
        df_homicide = df_homicide.drop_duplicates(subset=["name_norm"])
        df_master = df_master.merge(
            df_homicide[["name_norm", "homicide_rate"]], on="name_norm", how="left"
        )
    else:
        df_master["homicide_rate"] = np.nan

    if not df_gpi.empty:
        df_gpi["name_norm"] = df_gpi["country_gpi"].apply(normalize_name)
        df_gpi = df_gpi.drop_duplicates(subset=["name_norm"])
        df_master = df_master.merge(
            df_gpi[["name_norm", "gpi_score", "gpi_rank"]], on="name_norm", how="left"
        )
    else:
        df_master["gpi_score"] = np.nan
        df_master["gpi_rank"] = np.nan

    df_advisory = df_advisory.drop_duplicates(subset=["code_2"])
    df_master = df_master.merge(
        df_advisory[["code_2", "advisory_level"]], on="code_2", how="left"
    )

    print("6. Calculating TSI...")

    df_model = df_master.copy()

    hom_median = df_model["homicide_rate"].median()
    df_model["homicide_log"] = np.log1p(df_model["homicide_rate"].fillna(hom_median))

    scaler_hom = MinMaxScaler((0, 100))
    hom_scaled = scaler_hom.fit_transform(df_model[["homicide_log"]])
    df_model["homicide_norm"] = 100 - hom_scaled

    gpi_median = df_model["gpi_score"].median()
    df_model["gpi_filled"] = df_model["gpi_score"].fillna(gpi_median)
    scaler_gpi = MinMaxScaler((0, 100))
    gpi_scaled = scaler_gpi.fit_transform(df_model[["gpi_filled"]])
    df_model["gpi_norm"] = 100 - gpi_scaled

    def advisory_to_score(level):
        if pd.isna(level):
            return 50
        mapping = {1: 100, 2: 66, 3: 33, 4: 0}
        return mapping.get(int(level), 50)

    df_model["advisory_norm"] = df_model["advisory_level"].apply(advisory_to_score)

    df_model["TSI"] = (
        0.4 * df_model["homicide_norm"]
        + 0.3 * df_model["gpi_norm"]
        + 0.3 * df_model["advisory_norm"]
    )

    print("7. Running Clustering...")
    features = ["homicide_norm", "gpi_norm", "advisory_norm"]
    X = df_model[features].fillna(50)

    kmeans = KMeans(n_clusters=4, random_state=42)
    df_model["cluster"] = kmeans.fit_predict(X)

    cluster_means = (
        df_model.groupby("cluster")["TSI"].mean().sort_values(ascending=False)
    )
    cluster_map = {}
    labels = ["Safe", "Moderate", "Caution", "High Risk"]
    for i, cluster_id in enumerate(cluster_means.index):
        cluster_map[cluster_id] = labels[i]

    df_model["risk_tier"] = df_model["cluster"].map(cluster_map)

    out_file = _here("results", "TravelSafe_Final_Analysis.csv")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    df_model.to_csv(out_file, index=False)
    print(f"✓ Analysis complete. Saved to {out_file}")

    summary = {
        "total_countries": _safe_int(len(df_model)),
        "countries_with_homicide_data": _safe_int(df_model["homicide_rate"].notna().sum()),
        "countries_with_safety_data": _safe_int(df_model["TSI"].notna().sum()),
        "mean_homicide_rate": _safe_float(pd.to_numeric(df_model["homicide_rate"], errors="coerce").mean()),
        "regions_covered": _safe_int(df_model["region"].nunique(dropna=True)),
    }

    mean_crime_score = None
    try:
        safety_path = _here("data", "processed.json")
        if os.path.exists(safety_path):
            with open(safety_path, "r", encoding="utf-8") as f:
                safety = json.load(f) or {}
            crime_scores = []
            for v in safety.values():
                rs = (v or {}).get("risk_scores") or {}
                c = rs.get("crime")
                if c is None:
                    continue
                try:
                    crime_scores.append(float(c))
                except Exception:
                    pass
            if crime_scores:
                mean_crime_score = float(np.mean(crime_scores))
    except Exception:
        mean_crime_score = None

    summary["mean_crime_score"] = _safe_float(mean_crime_score)

    summary_path = _here("results", "analysis_summary.json")
    try:
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"✓ Summary updated. Saved to {summary_path}")
    except Exception as e:
        print(f"Warning: could not write summary JSON: {e}")

    print("\nTop 10 Safest Countries (by TSI):")
    print(
        df_model[["country", "TSI", "risk_tier"]]
        .sort_values("TSI", ascending=False)
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    run_analysis()

