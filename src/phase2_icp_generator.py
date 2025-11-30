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

# --- 2. Input from Phase 1 ---
# PASTE THE SUMMARY FROM YOUR PHASE 1 SCRIPT RUN HERE
phase1_summary = """
**1. What is Greyamp's core business and value proposition?**
Greyamp Consulting is a transformation and digital solutions firm specializing in AI-first products and agentic solutions aimed at enhancing sales, marketing, and client engagement. Their value proposition lies in applying cutting-edge technology to address real-world business challenges, particularly within B2B sales processes.

**2. Who are their typical customers (industries, company type)?**
Greyamp primarily serves leading enterprises across various industries, including:
   - Telecommunications (e.g., Axiata Digital)
   - Financial Services & Insurance (e.g., HDFC Life, CUNA Mutual)
   - Retail & E-commerce
   
**3. What specific business problems do they solve for these customers?**
Greyamp solves problems related to legacy system modernization, building new user-centric digital products, automating software delivery through DevOps, and leveraging data and AI to accelerate business processes like sales and marketing. Greyamp helps customers modernize outdated systems, develop new digital products for customer engagement, and leverage AI to enhance business processes. Their solutions focus on delivering incremental value through a collaborative co-creation model and a Lean-Agile methodology.
"""

# --- 3. The Master Prompt for Phase 2 ---
# This prompt instructs the LLM to act as a Chief Strategy Officer
def create_icp_prompt(summary):
    prompt = f"""
    You are a Chief Strategy Officer for a B2B digital transformation consultancy specializing in AI solutions. Your task is to define FIVE distinct and high-potential Ideal Customer Profiles (ICPs) based on the company summary provided below.

    **CRITICAL INSTRUCTIONS:**
    1.  All companies MUST be located in **India**.
    2.  All "buying_signals" MUST be specifically related to **Artificial Intelligence (AI)**.

    **Company Summary:**
    ---
    {summary}
    ---

    Your final output MUST be a single, valid JSON object. The top-level key must be "ideal_customer_profiles", which contains an array of the five ICPs.

    **JSON Schema for each ICP:**
    - `icp_name`: A descriptive name for this profile (e.g., "AI-Powered FinTech Innovator").
    - `industry_vertical`: The specific industry to target (e.g., ["Financial Services", "Insurance"]).
    - `location_cities`: A list of 2-3 key cities in India for this ICP (e.g., ["Bengaluru", "Mumbai", "Pune"]).
    - `key_challenges`: A list of 2-3 specific business or technology problems this company is likely facing related to AI adoption.
    - `buying_signals`: A list of 3-4 short, 2-4 word keywords that are publicly discoverable events or "signals" specifically related to AI (e.g., "launching a new AI product", "hiring AI engineers", "acquiring an AI startup").
    """
    return prompt

# --- 4. Main execution block ---
if __name__ == "__main__":
    print("Starting Phase 2: Generating ICP Hypothesis...")

    icp_generation_prompt = create_icp_prompt(phase1_summary)

    print("Sending request to the LLM to generate ICPs...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"}, # This forces the output to be valid JSON
            messages=[
                {"role": "system", "content": "You are a helpful business strategy assistant that outputs only valid JSON."},
                {"role": "user", "content": icp_generation_prompt}
            ]
        )

        # Extract the JSON string from the response
        json_response_str = response.choices[0].message.content

        # Convert the JSON string into a Python dictionary
        icp_data = json.loads(json_response_str)

        print("\n--- LLM Strategy Complete: ICPs Generated ---")

        # Pretty-print the JSON to make it readable
        print(json.dumps(icp_data, indent=2))

        # Save the ICPs to a file for the next phase
        with open("icp_profiles.json", "w") as f:
            json.dump(icp_data, f, indent=2)

        print("\nPhase 2 successfully completed. ICPs saved to 'icp_profiles.json'.")
        print("This file will be the input for our 'Scout' Agent in Phase 3.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")