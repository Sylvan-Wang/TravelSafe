#Descriptive Statistics
print("=== Descriptive Statistics ===")
print("\nHomicide Rate Statistics:")
print(df_final['homicide_rate'].describe())

print("\n\nSafety Score Statistics:")
safety_cols = ['crime_score', 'political_score', 'health_score', 'natural_disaster_score']
print(df_final[safety_cols].describe())

print("\n\nOverall Risk Distribution:")
print(df_final['overall_risk'].value_counts())

#Correlation Analysis
# Calculate correlations
numeric_cols = ['population', 'homicide_rate', 'crime_score', 'political_score', 
                'health_score', 'natural_disaster_score']
corr_data = df_final[numeric_cols].corr()

print("Correlation Matrix:")
print(corr_data.round(3))


#Regional Analysis
# Analyze by region
regional_stats = df_final.groupby('region').agg({
    'homicide_rate': ['mean', 'median', 'std'],
    'crime_score': 'mean',
    'political_score': 'mean',
    'population': 'sum'
}).round(2)

print("Regional Safety Statistics:")
print(regional_stats)
