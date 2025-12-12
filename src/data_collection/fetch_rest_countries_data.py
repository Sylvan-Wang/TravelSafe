REST_COUNTRIES_URL = (
    "https://restcountries.com/v3.1/all"
    "?fields=name,cca2,region,subregion,population,capital,languages,currencies"
)

print("Fetching REST Countries data...")
resp = requests.get(REST_COUNTRIES_URL, timeout=20)
resp.raise_for_status()
countries_data = resp.json()

# Convert to DataFrame
countries_list = []
for item in countries_data:
    code = item.get("cca2")
    if not code:
        continue
    name = item.get("name", {}).get("common", "")
    countries_list.append({
        "code": code.upper(),
        "name": name,
        "region": item.get("region", ""),
        "subregion": item.get("subregion", ""),
        "population": item.get("population"),
        "capital": (item.get("capital") or ["N/A"])[0],
        "languages": ", ".join(list(item.get("languages", {}).values())[:3]) if item.get("languages") else "N/A",
        "currencies": ", ".join([c["name"] for c in list(item.get("currencies", {}).values())[:2]]) if item.get("currencies") else "N/A"
    })

df_countries = pd.DataFrame(countries_list)
print(f"✓ Loaded {len(df_countries)} countries from REST Countries API")
print(f"\nSample data:")
df_countries.head()
