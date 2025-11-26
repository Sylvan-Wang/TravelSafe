# Clean homicide rate data
# Check if df_homicide exists and is not empty
if 'df_homicide' not in globals() or df_homicide is None or len(df_homicide) == 0:
    print("Warning: df_homicide is empty or not defined. Creating empty DataFrame.")
    df_homicide_clean = pd.DataFrame(columns=['country_clean', 'homicide_rate'])
else:
    # The exact column names may vary, so we'll need to inspect and adjust
    print("Original columns:")
    print(df_homicide.columns.tolist())

    # Standardize column names (adjust based on actual Wikipedia table structure)
    # Common patterns: Country/Territory, Rate, Year, etc.
    if len(df_homicide.columns) > 0 and 'Country' in str(df_homicide.columns[0]):
        df_homicide = df_homicide.rename(columns={df_homicide.columns[0]: 'country'})

    # Find rate column (usually contains numbers and may have "Rate" or "per 100,000")
    rate_col = None
    for col in df_homicide.columns:
        if 'rate' in str(col).lower() or 'per 100' in str(col).lower() or df_homicide[col].dtype in [np.float64, np.int64]:
            if df_homicide[col].dtype in [np.float64, np.int64] or any(isinstance(x, (int, float)) for x in df_homicide[col].dropna().head(5) if pd.notna(x)):
                rate_col = col
                break

    if rate_col:
        df_homicide['homicide_rate'] = pd.to_numeric(df_homicide[rate_col], errors='coerce')
    else:
        # Fallback: use first numeric column
        numeric_cols = df_homicide.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            df_homicide['homicide_rate'] = df_homicide[numeric_cols[0]]
        else:
            df_homicide['homicide_rate'] = np.nan

    # Clean country names
    if len(df_homicide.columns) > 0:
        df_homicide['country_clean'] = df_homicide.iloc[:, 0].astype(str).str.strip()
    else:
        df_homicide['country_clean'] = ''

    # Remove rows with missing homicide rate
    df_homicide_clean = df_homicide[df_homicide['homicide_rate'].notna()].copy()

    print(f"\n✓ Cleaned data: {len(df_homicide_clean)} countries with valid homicide rates")
    if len(df_homicide_clean) > 0:
        print(f"\nSample cleaned data:")
        display(df_homicide_clean[['country_clean', 'homicide_rate']].head(10))
    else:
        print("No valid homicide rate data found.")
