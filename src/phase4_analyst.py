import os
import json
from openai import OpenAI
from tavily import TavilyClient # <-- NEW IMPORT
from dotenv import load_dotenv
import time

# --- 1. Setup ---
load_dotenv()
# Load Tavily API key
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    exit()

if not TAVILY_API_KEY:
    print("Error: TAVILY_API_KEY not found in .env file.")
    exit()

# Initialize the Tavily client
try:
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
except Exception as e:
    print(f"Error initializing Tavily client: {e}")
    exit()

# --- 2. Function to load raw leads (No change) ---
def load_raw_leads(filepath="raw_leads.json"):
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: '{filepath}' not found. Please run phase3_scout.py first.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'.")
        return []

# --- 3. UPDATED: Tool for the Agent to use - Tavily Search API ---
def search_tavily_for_details(query):
    print(f"   🔎 Using tool: Tavily Search for '{query}'")
    try:
        # Use Tavily's search method
        response = tavily.search(query=query, search_depth="basic", max_results=3)
        
        # Extract the content from the top 3 results
        snippets = [result.get('content', '') for result in response.get('results', [])]
        context = " ".join(snippets)
        return context
        
    except Exception as e:
        print(f"   -> Error during Tavily search: {e}")
        return ""

# --- 4. The Master Prompt (No change) ---
def create_analysis_prompt(article, enriched_context=""):
    prompt = f"""
    You are an expert business analyst for an Indian B2B consultancy. Your task is to analyze the provided information and extract structured data about a single, specific company that is a high-quality sales lead.

    **Primary Information (from news article):**
    ---
    - Title: "{article.get('title', 'N/A')}"
    - Description: "{article.get('description', 'N/A')}"
    - Content Snippet: "{article.get('content', 'N/A')}"
    ---

    **Secondary Information (from a targeted Tavily search, if available):**
    ---
    {enriched_context}
    ---

    **CRITICAL INSTRUCTIONS:**
    1.  **Location Filter:** The primary company MUST have a significant presence or be headquartered in **India**. If the company is clearly foreign with no direct Indian operations mentioned, return "N/A" for `company_name`.
    2.  **Signal Quality Filter:** The `qualifying_event_signal` MUST be a tangible business or technology event (e.g., new product launch, partnership, funding, hiring spree, major investment). It should NOT be a stock recommendation, a product release for a different industry (like a comic book), or a generic market trend. If no such event is mentioned, return "N/A" for `company_name`.
    3.  Your goal is to identify **one primary company**. Do NOT use generic terms.
    4.  Combine information from BOTH sources to fill out the JSON below. If information is not found, use "N/A".

    **JSON Schema to follow:**
    - `company_name`: The name of the primary company discussed.
    - `location_city`: The specific city in India where the company is headquartered or has a major office.
    - `key_person_name`: The name of a key executive (CEO, CTO, Founder, etc.).
    - `key_person_role`: The job title of that key executive.
    - `qualifying_event_signal`: A concise, one-sentence summary of the tangible AI-related business event.
    - `summary`: A brief summary of the original news article's content.
    """
    return prompt

# --- 5. Main execution block (UPDATED to call new function) ---
if __name__ == "__main__":
    print("Starting Phase 4: The Super-Analyst is qualifying and enriching leads (using Tavily API)...")
    raw_leads = load_raw_leads()
    all_processed_leads = [] # We'll store all results here first

    if not raw_leads:
        print("No raw leads to process. Exiting.")
    else:
        print(f"Found {len(raw_leads)} raw lead(s) to analyze.")

        for article in raw_leads:
            print(f"\nProcessing article: \"{article.get('title', 'Untitled')}\"")

            initial_prompt = create_analysis_prompt(article)
            try:
                initial_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[{"role": "user", "content": initial_prompt}]
                )
                lead_data = json.loads(initial_response.choices[0].message.content)
                company_name = lead_data.get("company_name", "N/A")

                if company_name != "N/A":
                    print(f"  -> Initial company identified: {company_name}")
                    full_enriched_context = ""
                    
                    # Call the new Tavily search function
                    location_context = search_tavily_for_details(f"{company_name} headquarters location India")
                    full_enriched_context += f"Location search results: {location_context}\\n"
                    time.sleep(1) # It's still good practice to add a small delay

                    # Call the new Tavily search function
                    people_context = search_tavily_for_details(f"{company_name} CEO CTO")
                    full_enriched_context += f"People search results: {people_context}\\n"
                    
                    print("  -> Performing final analysis with enriched data...")
                    final_prompt = create_analysis_prompt(article, full_enriched_context)
                    final_response = client.chat.completions.create(
                        model="gpt-4o",
                        response_format={"type": "json_object"},
                        messages=[{"role": "user", "content": final_prompt}]
                    )
                    final_lead_data = json.loads(final_response.choices[0].message.content)
                    all_processed_leads.append(final_lead_data)
                    print("     ✅ Lead qualified and enriched.")
                else:
                    print("  -> No specific company found. Skipping enrichment.")
                    all_processed_leads.append(lead_data)

            except Exception as e:
                print(f"     ❌ Error processing article: {e}")

        # --- NEW: Final Quality Filter ---
        final_qualified_leads = [
            lead for lead in all_processed_leads if lead.get("company_name") and lead.get("company_name") != "N/A"
        ]
        
        with open("qualified_leads.json", "w") as f:
            json.dump(final_qualified_leads, f, indent=2)

        print("\n=================================================")
        print("Phase 4 successfully completed!")
        print(f"Saved {len(final_qualified_leads)} high-quality, qualified leads to 'qualified_leads.json'.")
        print(f"(Filtered out {len(all_processed_leads) - len(final_qualified_leads)} invalid or low-quality leads)")
        print("=================================================")

