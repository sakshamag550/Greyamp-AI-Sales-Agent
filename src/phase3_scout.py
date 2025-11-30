import os
import json
import requests
from dotenv import load_dotenv

# --- 1. Setup ---
# Load environment variables from .env file
load_dotenv()
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY") # Load the NewsAPI key

# --- 2. Function to load ICPs from file ---
def load_icps(filepath="icp_profiles.json"):
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'.")
        return None

# --- 3. GNews Search Function ---
def search_gnews(icp):
    print(f"\n📰 Searching GNews for signals for ICP: {icp.get('icp_name', 'Unnamed ICP')}...")
    if not GNEWS_API_KEY:
        print("   ❌ GNews API Key not found. Skipping.")
        return []
        
    industry = " OR ".join([f'"{i}"' for i in icp.get("industry_vertical", [])])
    
    # Use the broad query to ensure we get results
    query = f'({industry}) AND "AI"'
    
    print(f"   Constructed Query: {query}")
    url = f"https://gnews.io/api/v4/search?q={query}&lang=en&country=in&max=10&token={GNEWS_API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        print(f"   ✅ Found {len(articles)} potential articles from GNews.")
        return articles
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error fetching from GNews: {e}")
        return []

# --- 4. NewsAPI.org Search Function ---
def search_newsapi(icp):
    print(f"\n📰 Searching NewsAPI.org for signals for ICP: {icp.get('icp_name', 'Unnamed ICP')}...")
    if not NEWSAPI_KEY:
        print("   ❌ NewsAPI Key not found. Skipping.")
        return []

    industry = " OR ".join([f'"{i}"' for i in icp.get("industry_vertical", [])])
    
    # Use the broad query
    query = f'({industry}) AND "AI"'
    
    print(f"   Constructed Query: {query}")
    url = "https://newsapi.org/v2/everything"
    
    # --- REMOVED 'country': 'in' ---
    params = {
        'q': query,
        'language': 'en',
        'pageSize': 10, 
        'apiKey': NEWSAPI_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        print(f"   ✅ Found {len(articles)} potential articles from NewsAPI.")
        
        # --- Data Standardization ---
        formatted_leads = []
        for article in articles:
            formatted_lead = {
                "title": article.get("title"),
                "description": article.get("description"),
                "content": article.get("content"),
                "url": article.get("url"),
                "image": article.get("urlToImage"),
                "publishedAt": article.get("publishedAt"),
                "source": {
                    "name": article.get("source", {}).get("name"),
                    "url": article.get("url") 
                }
            }
            formatted_leads.append(formatted_lead)
        return formatted_leads
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error fetching from NewsAPI: {e}")
        return []

# --- 5. Main execution block (UPDATED with de-duplication) ---
if __name__ == "__main__":
    print("Starting Phase 3: The Multi-Source Scout Agent is hunting for leads...")
    icp_data = load_icps()
    
    # --- NEW: Add a set to track processed URLs ---
    processed_urls = set()
    all_raw_leads = []

    if icp_data and "ideal_customer_profiles" in icp_data:
        # Correctly loop using the key from your JSON file
        for icp_profile in icp_data["ideal_customer_profiles"]:
            
            # Call both search functions
            gnews_leads = search_gnews(icp_profile)
            newsapi_leads = search_newsapi(icp_profile)
            
            # Combine all leads from all sources
            combined_leads = gnews_leads + newsapi_leads

            # --- NEW: Process and de-duplicate the combined list ---
            for lead in combined_leads:
                url = lead.get('url')
                
                # Only add the lead if we have a URL and we haven't seen it before
                if url and url not in processed_urls:
                    lead['matched_icp'] = icp_profile.get('icp_name')
                    all_raw_leads.append(lead)
                    processed_urls.add(url) # Add the URL to our "memory"

        # Save the de-duplicated leads to a file for Phase 4
        with open("raw_leads.json", "w") as f:
            json.dump(all_raw_leads, f, indent=2)

        print("\n-------------------------------------------------")
        print("Phase 3 successfully completed!")
        print(f"Found a total of {len(all_raw_leads)} unique raw leads from all sources.")
        print("Results are saved in 'raw_leads.json'.")
        print("-------------------------------------------------")
    else:
        print("Could not find valid ICP data to process.")

