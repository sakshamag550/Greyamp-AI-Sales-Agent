import os
import json
import requests
from dotenv import load_dotenv

# --- 1. Setup ---
# Load environment variables from .env file
load_dotenv()
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

if not GNEWS_API_KEY:
    print("Error: GNEWS_API_KEY not found. Please add it to your .env file.")
    exit()

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

# --- 3. Function to search for news articles ---
def search_for_signals(icp):
    print(f"\n🔎 Searching for signals for ICP: {icp.get('icp_name', 'Unnamed ICP')}...")

    # We'll combine industry and buying signals for a more targeted search
    industry = " OR ".join([f'"{i}"' for i in icp.get("industry_vertical", [])])
    signals = " OR ".join([f'"{s}"' for s in icp.get("buying_signals", [])])

    # Construct a powerful search query. GNews supports boolean operators.
    query = f"({industry}) AND ({signals})"

    print(f"   Constructed Query: {query}")

    # Define the API endpoint and parameters
    url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max=5&token={GNEWS_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
        articles = response.json().get("articles", [])
        print(f"   ✅ Found {len(articles)} potential articles.")
        return articles
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error fetching news: {e}")
        return []

# --- 4. Main execution block ---
if __name__ == "__main__":
    print("Starting Phase 3: The Scout Agent is hunting for leads...")

    icp_data = load_icps()

    if icp_data and "ideal_customer_profiles" in icp_data:
        all_raw_leads = []
        # Loop through each ICP defined in our JSON file
        for icp_profile in icp_data["ideal_customer_profiles"]:
            found_articles = search_for_signals(icp_profile)
            if found_articles:
                # Add the ICP name to each article for context in the next phase
                for article in found_articles:
                    article['matched_icp'] = icp_profile.get('icp_name')
                all_raw_leads.extend(found_articles)

        # Save the raw leads to a file for Phase 4
        with open("raw_leads.json", "w") as f:
            json.dump(all_raw_leads, f, indent=2)

        print("\n-------------------------------------------------")
        print("Phase 3 successfully completed!")
        print(f"Found a total of {len(all_raw_leads)} raw leads.")
        print("Results are saved in 'raw_leads.json'. This file is the input for the 'Analyst' Agent in Phase 4.")
        print("-------------------------------------------------")
    else:
        print("Could not find valid ICP data to process.")