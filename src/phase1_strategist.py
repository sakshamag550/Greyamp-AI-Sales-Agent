import os
from openai import OpenAI
from dotenv import load_dotenv

# --- 1. Load Environment Variables ---
# This line loads the OPENAI_API_KEY from your .env file
load_dotenv()

# --- 2. Initialize the OpenAI Client ---
# This sets up the connection to OpenAI using your API key
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Please make sure your OPENAI_API_KEY is set correctly in the .env file.")
    exit()

# --- 3. Read the Greyamp Context File ---
# This function reads the content of your greyamp_context.txt file
def read_context_file(filepath="greyamp_context.txt"):
    try:
        with open(filepath, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        print("Please make sure 'greyamp_context.txt' is in the same folder as this script.")
        return None

# --- 4. Define the Master Prompt for the LLM ---
# This is the specific instruction we give to the AI.
def create_prompt(context):
    prompt = f"""
    You are a world-class business strategist. Your task is to analyze the provided context document about a company called Greyamp Consulting.

    Read the following document carefully:
    ---
    {context}
    ---

    Based ONLY on the information in this document, provide a concise summary that answers these three questions:
    1. What is Greyamp's core business and value proposition?
    2. Who are their typical customers (industries, company type)?
    3. What specific business problems do they solve for these customers?

    Present the summary in a clear, easy-to-read format.
    """
    return prompt

# --- 5. Main execution block ---
if __name__ == "__main__":
    print("Starting Phase 1: Analyzing Greyamp's DNA...")

    # Read the context
    greyamp_context = read_context_file()

    if greyamp_context:
        # Create the prompt
        analysis_prompt = create_prompt(greyamp_context)

        print("Sending context to the LLM for analysis...")

        # Make the API call to the LLM
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Recommended gpt-4o. You can also use "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": "You are a helpful business analysis assistant."},
                    {"role": "user", "content": analysis_prompt}
                ]
            )

            # Extract and print the LLM's response
            summary = response.choices[0].message.content
            print("\n--- LLM Analysis Complete ---")
            print(summary)
            print("\nPhase 1 successfully completed. This summary is the foundation for Phase 2.")

        except Exception as e:
            print(f"\nAn error occurred during the API call: {e}")