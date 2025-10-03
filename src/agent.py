import os
from dotenv import load_dotenv
from typing import List, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

# --- 1. Load API Key ---
# Load environment variables from .env file
load_dotenv()

# We will use this to check if the API key is set
# If you don't have an API key, you can get one from https://platform.openai.com/api-keys
if os.getenv("OPENAI_API_KEY") is None:
    print("OPENAI_API_KEY is not set. Please set it in your .env file.")
    exit()

# --- 2. Define the Agent's State ---
# The state is the memory of our agent. It's what gets passed between steps.
# Here, it's a list of messages that make up the conversation.
class AgentState(TypedDict):
    messages: List[BaseMessage]

# --- 3. Define the Nodes (the "workers") ---
# Nodes are the functions that do the work. We'll have one main node
# that calls the LLM.

def call_model(state: AgentState):
    """This node calls the language model to get a response."""
    messages = state['messages']
    # Initialize our LLM. We'll use OpenAI's gpt-4o-mini for speed and cost.
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0) 
    
    # Get the response from the model
    response = model.invoke(messages)
    
    # We return a dictionary with the AIMessage response to update our state
    return {"messages": [response]}

# --- 4. Define the Graph (the "flowchart") ---
# LangGraph lets us define our agent's workflow as a graph.
# Nodes are the steps, and edges are the connections between them.

# Create a new state graph
workflow = StateGraph(AgentState)

# Add our node to the graph. We're naming it "agent"
workflow.add_node("agent", call_model)

# Set the entry point of the graph. The first node to be called is "agent".
workflow.set_entry_point("agent")

# Add a simple edge. After the "agent" node runs, the graph ends.
# In the future, we can add more complex logic here.
workflow.add_edge("agent", END)

# Compile the graph into a runnable app. This is our final agent.
app = workflow.compile()

# --- 5. Run the Agent ---
# Let's test it!

# Start with a human message
inputs = {"messages": [HumanMessage(content="Hi! I'm an intern starting a new project. Can you give me a word of encouragement?")]}

# The .stream() method lets us see the output as it's generated.
for output in app.stream(inputs):
    # The output is a dictionary, and we print the "agent" node's output
    for key, value in output.items():
        print(f"Output from node '{key}':")
        print("---")
        print(value)
    print("\n---\n")