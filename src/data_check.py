# Analyze the scraped homicide rate data
print("=" * 60)
print("HOMICIDE RATE DATA ANALYSIS")
print("=" * 60)

if 'df_homicide' in globals() and df_homicide is not None and len(df_homicide) > 0:
    print(f"\n📊 Dataset Overview:")
    print(f"   Total records: {len(df_homicide)}")
    print(f"   Columns: {list(df_homicide.columns)}")
    
    # Check data types
    print(f"\n📋 Data Types:")
    print(df_homicide.dtypes)
    
    # Check for missing values
    print(f"\n🔍 Missing Values:")
    missing = df_homicide.isnull().sum()
    print(missing[missing > 0])
    
    # Basic statistics for Rate column
    if 'Rate' in df_homicide.columns:
        print(f"\n📈 Homicide Rate Statistics (per 100,000):")
        print(df_homicide['Rate'].describe())
        
        # Check year distribution
        if 'Year' in df_homicide.columns:
            print(f"\n📅 Year Distribution:")
            print(df_homicide['Year'].value_counts().head(10))
        
        # Regional distribution
        if 'Region' in df_homicide.columns:
            print(f"\n🌍 Regional Distribution:")
            region_counts = df_homicide['Region'].value_counts()
            print(region_counts)
            
            print(f"\n📊 Average Homicide Rate by Region:")
            region_avg = df_homicide.groupby('Region')['Rate'].agg(['mean', 'median', 'count']).round(2)
            region_avg.columns = ['Mean Rate', 'Median Rate', 'Count']
            print(region_avg.sort_values('Mean Rate', ascending=False))
    
    # Top and bottom countries
    if 'Rate' in df_homicide.columns and 'Location' in df_homicide.columns:
        print(f"\n🔝 Top 10 Countries by Homicide Rate:")
        top_10 = df_homicide.nlargest(10, 'Rate')[['Location', 'Rate', 'Region']]
        print(top_10.to_string(index=False))
        
        print(f"\n🔻 Bottom 10 Countries by Homicide Rate:")
        bottom_10 = df_homicide.nsmallest(10, 'Rate')[['Location', 'Rate', 'Region']]
        print(bottom_10.to_string(index=False))
    
    # Display sample data
    print(f"\n📋 Sample Data (First 5 rows):")
    display(df_homicide.head())
    
else:
    print("⚠️ No homicide rate data available for analysis.")
