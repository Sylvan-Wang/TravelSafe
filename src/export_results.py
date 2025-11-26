# Export final merged dataset
df_final.to_csv('travel_safety_analysis.csv', index=False)
print("✓ Exported merged dataset to 'travel_safety_analysis.csv'")

# Export summary statistics
summary_stats = {
    'total_countries': len(df_final),
    'countries_with_homicide_data': int(df_final['homicide_rate'].notna().sum()),
    'countries_with_safety_data': int(df_final['crime_score'].notna().sum()),
    'mean_homicide_rate': float(df_final['homicide_rate'].mean()) if df_final['homicide_rate'].notna().any() else None,
    'mean_crime_score': float(df_final['crime_score'].mean()) if df_final['crime_score'].notna().any() else None,
    'regions_covered': int(df_final['region'].nunique())
}

with open('analysis_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary_stats, f, indent=2, ensure_ascii=False)

print("✓ Exported summary statistics to 'analysis_summary.json'")
print("\nSummary:")
for key, value in summary_stats.items():
    print(f"  {key}: {value}")
