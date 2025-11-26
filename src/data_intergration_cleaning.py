# Merge datasets
# First, merge countries with safety data (by code)
df_merged = df_countries.merge(df_safety, on='code', how='left', suffixes=('', '_safety'))

# Then merge with homicide rate data (by country name)
# Need to handle name mismatches
def normalize_country_name(name):
    """Normalize country names for matching"""
    if pd.isna(name):
        return ""
    name = str(name).strip().lower()
    # Remove common suffixes
    name = re.sub(r'\s*\(.*?\)', '', name)  # Remove parentheses
    name = re.sub(r'^the\s+', '', name)  # Remove "the"
    return name

df_merged['name_normalized'] = df_merged['name'].apply(normalize_country_name)
df_homicide_clean['country_normalized'] = df_homicide_clean['country_clean'].apply(normalize_country_name)

# Merge on normalized names
df_final = df_merged.merge(
    df_homicide_clean[['country_normalized', 'homicide_rate']],
    left_on='name_normalized',
    right_on='country_normalized',
    how='left'
)

print(f"✓ Merged dataset: {len(df_final)} countries")
print(f"  - Countries with homicide rate: {df_final['homicide_rate'].notna().sum()}")
print(f"  - Countries with safety scores: {df_final['crime_score'].notna().sum()}")

# Display summary statistics
print("\nDataset summary:")
df_final.info()
