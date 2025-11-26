# Analyze the merged dataset
print("=" * 60)
print("MERGED DATASET ANALYSIS")
print("=" * 60)

if 'df_final' in globals() and df_final is not None and len(df_final) > 0:
    print(f"\n📊 Dataset Overview:")
    print(f"   Total countries: {len(df_final)}")
    print(f"   Countries with homicide rate data: {df_final['homicide_rate'].notna().sum()}")
    print(f"   Countries with safety scores: {df_final['crime_score'].notna().sum()}")
    print(f"   Coverage: {df_final['homicide_rate'].notna().sum() / len(df_final) * 100:.1f}%")
    
    # Data completeness
    print(f"\n📋 Data Completeness:")
    completeness = {
        'Homicide Rate': df_final['homicide_rate'].notna().sum(),
        'Crime Score': df_final['crime_score'].notna().sum(),
        'Political Score': df_final['political_score'].notna().sum(),
        'Health Score': df_final['health_score'].notna().sum(),
        'Natural Disaster Score': df_final['natural_disaster_score'].notna().sum(),
        'Population': df_final['population'].notna().sum(),
        'Region': df_final['region'].notna().sum()
    }
    for key, value in completeness.items():
        pct = value / len(df_final) * 100
        print(f"   {key}: {value}/{len(df_final)} ({pct:.1f}%)")
    
    # Overall risk distribution
    print(f"\n⚠️ Overall Risk Distribution:")
    risk_dist = df_final['overall_risk'].value_counts()
    for risk, count in risk_dist.items():
        pct = count / len(df_final) * 100
        print(f"   {risk}: {count} countries ({pct:.1f}%)")
    
    # Regional coverage
    print(f"\n🌍 Regional Coverage:")
    regional_coverage = df_final.groupby('region').agg({
        'homicide_rate': lambda x: x.notna().sum(),
        'code': 'count'
    })
    regional_coverage.columns = ['With Homicide Data', 'Total Countries']
    regional_coverage['Coverage %'] = (regional_coverage['With Homicide Data'] / regional_coverage['Total Countries'] * 100).round(1)
    print(regional_coverage.sort_values('Coverage %', ascending=False))
    
    # Countries with both homicide and safety data
    df_with_both = df_final[(df_final['homicide_rate'].notna()) & (df_final['crime_score'].notna())]
    print(f"\n✅ Countries with Both Homicide Rate and Safety Scores: {len(df_with_both)}")
    
    if len(df_with_both) > 0:
        print(f"\n📈 Statistics for Countries with Complete Data:")
        print(f"   Average Homicide Rate: {df_with_both['homicide_rate'].mean():.2f} per 100,000")
        print(f"   Average Crime Score: {df_with_both['crime_score'].mean():.2f}")
        print(f"   Average Political Score: {df_with_both['political_score'].mean():.2f}")
        
        # Correlation preview
        if len(df_with_both) > 10:
            corr_homicide_crime = df_with_both['homicide_rate'].corr(df_with_both['crime_score'])
            print(f"\n🔗 Correlation (Homicide Rate vs Crime Score): {corr_homicide_crime:.3f}")
            if abs(corr_homicide_crime) > 0.5:
                print("   → Strong correlation")
            elif abs(corr_homicide_crime) > 0.3:
                print("   → Moderate correlation")
            else:
                print("   → Weak correlation")
    
    # Sample of merged data
    print(f"\n📋 Sample Merged Data (First 5 rows with homicide data):")
    sample = df_final[df_final['homicide_rate'].notna()].head()
    display(sample[['name', 'region', 'homicide_rate', 'crime_score', 'political_score', 'overall_risk']])
    
else:
    print("⚠️ Merged dataset not available. Please run the data integration cell first.")
