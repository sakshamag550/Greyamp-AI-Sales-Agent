import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# --- 1. Setup ---
# Load environment variables and initialize the OpenAI client
load_dotenv()
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    exit()

# --- 2. Function to load raw leads from file ---
def load_raw_leads(filepath="raw_leads.json"):
    try:
        with open(filepath, 'r') as file:
            # The user's uploaded file has one lead
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found. Please run phase3_scout.py first.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'. The file might be corrupted.")
        return []

# --- 3. The Master Prompt for the Analyst Agent ---
def create_analysis_prompt(article):
    # The article has a title, description, and content
    prompt = f"""
    You are an expert business analyst. Your task is to analyze the following news article and extract specific, structured information about the company mentioned.

    **Article Context:**
    - Matched ICP: "{article.get('matched_icp', 'N/A')}"
    - Title: "{article.get('title', 'N/A')}"
    - Description: "{article.get('description', 'N/A')}"
    - Content Snippet: "{article.get('content', 'N/A')}"

    **Your Instructions:**
    Based on the article context, extract the following information. Your final output MUST be a single, valid JSON object. If you cannot find a piece of information, use "N/A" for that field.

    **JSON Schema to follow:**
    - `company_name`: The name of the primary company discussed in the article.
    - `key_person_name`: The name of a key executive mentioned (e.g., CEO, CTO).
    - `key_person_role`: The job title of that key executive.
    - `qualifying_event_signal`: A concise, one-sentence summary of the event that makes this company a good lead (e.g., "Experienced a major network failure during an upgrade, highlighting a need for modernization.").
    - `summary`: A brief summary of the article's content.
    """
    return prompt

# --- 4. Main execution block ---
if __name__ == "__main__":
    print("Starting Phase 4: The Analyst Agent is qualifying leads...")

    raw_leads = load_raw_leads()
    qualified_leads = []

    if not raw_leads:
        print("No raw leads to process. Exiting.")
    else:
        print(f"Found {len(raw_leads)} raw lead(s) to analyze.")

        # Loop through each article and analyze it
        for article in raw_leads:
            print(f"  -> Analyzing article: \"{article.get('title', 'Untitled')}\"")
            analysis_prompt = create_analysis_prompt(article)

            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are a helpful business analysis assistant that outputs only valid JSON."},
                        {"role": "user", "content": analysis_prompt}
                    ]
                )

                # Extract the JSON string and convert it to a Python dictionary
                json_response_str = response.choices[0].message.content
                lead_data = json.loads(json_response_str)
                qualified_leads.append(lead_data)
                print("     ✅ Analysis complete. Lead qualified.")

            except Exception as e:
                print(f"     ❌ Error analyzing article: {e}")

        # Save the qualified leads to a final file
        with open("qualified_leads.json", "w") as f:
            json.dump(qualified_leads, f, indent=2)

        print("\n-------------------------------------------------")
        print("Phase 4 successfully completed!")
        print(f"Saved {len(qualified_leads)} qualified lead(s) to 'qualified_leads.json'.")
        print("This is the final output of the AI Sales Agent pipeline.")
        print("-------------------------------------------------")