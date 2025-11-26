
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/List_of_countries_by_intentional_homicide_rate"

print("Scraping homicide rate data from Wikipedia...")
df_homicide = None

# Set headers to avoid 403 Forbidden error
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    # Method 1: First fetch HTML with requests, then parse with pandas
    print("Fetching HTML content...")
    resp = requests.get(WIKIPEDIA_URL, timeout=30, headers=headers)
    resp.raise_for_status()
    print(f"✓ HTML fetched successfully ({len(resp.text)} characters)")
    
    # Parse all tables from the HTML
    print("Parsing tables from HTML...")
    tables = pd.read_html(resp.text)
    print(f"✓ Found {len(tables)} tables")
    
    # Find the table with homicide rate data (should have many rows and contain country/rate columns)
    for idx, table in enumerate(tables):
        cols_str = str(table.columns).lower()
        # Look for tables with country and rate columns, and should have many rows
        if len(table) > 50 and ('country' in cols_str or 'territory' in cols_str) and ('rate' in cols_str or 'homicide' in cols_str):
            df_homicide = table
            print(f"✓ Found homicide rate table (table #{idx+1}) with {len(df_homicide)} rows")
            break
    
    # If not found by criteria, try the largest table
    if df_homicide is None and len(tables) > 0:
        largest_table = max(tables, key=len)
        if len(largest_table) > 50:  # Should have many countries
            df_homicide = largest_table
            print(f"Using largest table as fallback (table with {len(df_homicide)} rows)")
    
    if df_homicide is not None and len(df_homicide) > 0:
        print(f"\n✓ Successfully loaded {len(df_homicide)} rows")
        print(f"\nColumns: {list(df_homicide.columns)}")
        print(f"\nFirst few rows:")
        display(df_homicide.head(10))
    else:
        raise ValueError("No valid tables found")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nTrying alternative method with BeautifulSoup...")
    
    try:
        resp = requests.get(WIKIPEDIA_URL, timeout=30, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find all wikitable elements
        tables_html = soup.find_all('table', class_='wikitable')
        print(f"Found {len(tables_html)} wikitable elements")
        
        # Try each table
        for idx, table_html in enumerate(tables_html):
            try:
                temp_df = pd.read_html(str(table_html))[0]
                cols_str = str(temp_df.columns).lower()
                if len(temp_df) > 50 and ('country' in cols_str or 'territory' in cols_str):
                    df_homicide = temp_df
                    print(f"✓ Found homicide rate table (wikitable #{idx+1}) with {len(df_homicide)} rows")
                    break
            except:
                continue
        
        if df_homicide is not None and len(df_homicide) > 0:
            print(f"\nColumns: {list(df_homicide.columns)}")
            display(df_homicide.head(10))
        else:
            raise ValueError("No suitable wikitable found")
            
    except Exception as e2:
        print(f"Error with BeautifulSoup method: {e2}")
        import traceback
        traceback.print_exc()
        print("Creating empty DataFrame as fallback...")
        df_homicide = pd.DataFrame()

# Ensure df_homicide is always defined
if df_homicide is None or (isinstance(df_homicide, pd.DataFrame) and len(df_homicide) == 0):
    df_homicide = pd.DataFrame()
    print("\n⚠️ Warning: Could not scrape homicide rate data. Using empty DataFrame.")
    print("The analysis will continue but without homicide rate data.")
else:
    print(f"\n✅ Successfully loaded homicide rate data for {len(df_homicide)} countries/territories")
