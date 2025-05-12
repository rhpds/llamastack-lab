#!/usr/bin/env python
# coding: utf-8

# # Exploring ReAct Agents and Tool Use
# 
# In this section, we will explore ReAct agents and how they can leverage multiple tools to perform tasks.
# 
# - Understand the ReAct framework and its components.
# - See how a ReAct agent combines reasoning and acting.
# - Utilize both built-in and custom tools with a ReAct agent.
# - Observe the steps a ReAct agent takes to solve a problem.
# 
# > **Note:**
# > This section builds upon the basic agent concepts introduced previously. Familiarity with terms like "Turns" and "Steps" will be helpful.
# >

# **Regular AI agents** often work by taking a prompt and generating a response directly, maybe using some internal knowledge or a single tool call. They are often more reactive and limited to predefined functions or knowledge.
# 
# A **ReAct agent** (short for **Reasoning and Acting**) is different because it doesn't just generate an immediate response. Instead, it uses a loop of:
# 
# 1.  **Reasoning (Thought):** It thinks step-by-step about the problem and what needs to be done.
# 2.  **Acting (Action):** Based on its thought, it decides to perform an action, often using external tools (like searching the web, running code, or interacting with an API).
# 3.  **Observing (Observation):** It then observes the result of that action.
# 
# This **Reason-Act-Observe loop** allows the ReAct agent to dynamically plan, gather information, and refine its approach based on what it learns from its actions, making it much more capable of handling complex tasks and interacting with dynamic environments than a regular agent.
# 
# Think of it this way:
# 
# * **Regular AI Agents:** Primarily take input and give output based on internal knowledge or a single action. They are often reactive.
# * **ReAct Agents:** Use a **Reason-Act-Observe loop**. They **think** about the problem, decide on an **action** (like using a tool), and then **observe** the result to inform their next thought and action. This makes them more dynamic and capable of complex, multi-step tasks.

# ## Adding a new Model to our exising Llama Stack Server
# 
# Before we dive into **ReAct Agents**, let's add another model to our server. It's crucial to understand that different models are specifically designed and excel at different tasks, often varying based on their size and training.
# 
# Recognizing this is important because:
# 
# * **Size vs. Capability & Cost:** Larger models (like 7B+ parameters) often handle complex instructions, nuanced language, and broader knowledge better, but require more computing resources and can be slower/more expensive. Smaller models (like 3B parameters) are faster, cheaper, and can run on less powerful hardware, often sufficient for simpler or more focused tasks.
# * **Task Specialization:** Some models are fine-tuned for specific "skills" like code generation, summarization, or following structured instructions (which is key for agents using tools). A model strong in one area might underperform in another compared to a specialist.
# * **Balancing Performance Needs:** For a given application, you might use a smaller, faster model for initial filtering or simple responses, and only route complex queries to a larger, more capable (and costly) model.
# 
# Understanding these trade-offs allows you to choose the best model for a given job. We're adding this specific model now because its capabilities align well with the agent tasks we'll be working with next.
# 
# For this section of the lab, we chose the `granite3.2:8b` model due to its excellent **tool calling capabilities**, manageable **size**, and strong **natural language interpretation**.

# ### Adding the model
# 
# First, let's get `ollama` to "run" or "load" the model: (This might take a moment if Ollama needs to pull the model for the first time)

# In[ ]:


get_ipython().system('ollama run granite3.2:8b "Just say hello" --keepalive 60m')


# Second, le'ts define our `client` normally, just like we did in the previous sections: 

# In[ ]:


from llama_stack_client import LlamaStackClient
LLAMA_STACK_SERVER='http://localhost:8321'
client = LlamaStackClient(
    base_url=LLAMA_STACK_SERVER,
)

models = client.models.list()
print("--- Available models: ---")
for m in models:
    print(f"{m.identifier} - {m.provider_id} - {m.provider_resource_id}")


# Third, Register the model using the `client.models.register` function, and print out the updated models list with `client.models.list` to verify success

# In[ ]:


# Register a model
model = client.models.register(
    model_id="granite3.2:8b",
    model_type="llm",
    provider_id="ollama",
    provider_model_id="granite3.2:8b",
    metadata={"description": "granite3.2:8b via ollama"}
)

models = client.models.list()
print("--- Available models: ---")
for m in models:
    print(f"{m.identifier} - {m.provider_id} - {m.provider_resource_id}")


# > **Note:**
# > Alternitivly, you could have also just run llama-stack-client commands instead of the python code: 
# > ```bash
# > # Register a Model
# > llama-stack-client models register --provider-id ollama --provider-model-id granite3.2:8b granite3.2:8b
# > # List available models
# > llama-stack-client models list
# > #To unregister, simply run: 
# > llama-stack-client models unregister granite3.2:8b
# ```

# ## Our First ReAct Agent
# ### Setting up steps
# In our first scenario, we will follow the same example from preivous sections just to see how the ReAct agent handles that kind of situation. 
# 
# We've combined these steps to make it easier and faster for you, in this step we will do the following:
# 
# * Installing the necessary Python libraries for this lab.
# * Import `get_location` function from a library instead of having it's code directly in the notebook `from src.client_tools import get_location`
# * Initialize the *Client* and select the desired model
# 

# In[ ]:


get_ipython().system('pip install -U llama-stack-client==0.2.5 dotenv > /dev/null 2>&1 && echo "pip Python Prerequisites installed succesfuly"')

import os
# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# for communication with Llama Stack
from llama_stack_client import LlamaStackClient

# These libraries are just here to print the results from the agent in a more human-readable way 
from src.utils import step_printer
from src.client_tools import get_location
from termcolor import cprint
import uuid
from llama_stack_client.lib.agents.event_logger import EventLogger
stream=False ## Defaulting to False, you can change this throughout the section to "True" if you wanted to see the output in another format (Using EventLogger)

# for our lab, we will just define our variables manualy here, in a regular application, this would be ready directly from the local .env file and we would comment these lines out
os.environ['LLAMA_STACK_SERVER'] = 'http://localhost:8321'

# We will be using the Tavily web search service (docs.tavily.com/)
tavily_search_api_key='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'
provider_data = {"tavily_search_api_key": tavily_search_api_key}

from llama_stack_client import LlamaStackClient
LLAMA_STACK_SERVER=os.getenv("LLAMA_STACK_SERVER")

client = LlamaStackClient(
    base_url=LLAMA_STACK_SERVER,
    provider_data=provider_data
)
# List available models and select from allowed models list
allowed_models_list=["granite3.2:8b"]
selected_model = None

models = client.models.list()

print("--- Available models: ---")
for m in models:
    print(f"{m.identifier} - {m.provider_id} - {m.provider_resource_id}")
    # Check if the model identifier contains any of the allowed substrings
    if any(substring in m.identifier for substring in allowed_models_list):
        # Only set selected_model if it hasn't been set yet
        if selected_model is None:
            selected_model = m.identifier

# If no allowed model was found, you might want to handle that case
if selected_model is None:
    print("No allowed model found in the list.")


print(f"Selected model (from allowed list): {selected_model}")
            # Removed the break here to show all available models, but the selection logic remains picking the first one


model = selected_model


# ### Review the ReAct Agent Chain of Thought
# 
# Now that our server is set up and we have a model capable of tool calling, let's see our **ReAct agent** in action. We will give it a specific, multi-step task:
# 
# "**search for any weather-related risks in my area that could disrupt network connectivity or system availability?**"
# 
# Watch the output closely. Unlike a simple model call, you will see the agent's "Chain of Thought" unfold. The agent will:
# 
# 1.  **Think** about the request and plan the next step.
# 2.  Decide on an **Action**, often involving using one of the available tools (like a search engine or a location service).
# 3.  Receive an **Observation** which is the result of the action.
# 4.  Repeat the **Think → Action → Observation** loop, building on the observations, until it formulates a final answer.

# In[ ]:


from llama_stack_client.lib.agents.react.agent import ReActAgent
from llama_stack_client.lib.agents.react.tool_parser import ReActOutput

stream=False
agent = ReActAgent(
            client=client,
            model=model,
            tools=[get_location, "builtin::websearch"],
            response_format={
                "type": "json_schema",
                "json_schema": ReActOutput.model_json_schema(),
            },
            #sampling_params=sampling_params,
        )
user_prompts = [
    "what are weather-related risks in my area that could disrupt network connectivity or system availability?"
]
session_id = agent.create_session("React_Session")
for prompt in user_prompts:
    print("\n"+"="*50)
    print(f"Processing user query: {prompt}", "blue")
    print("="*50)
    response = agent.create_turn(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        session_id=session_id,
        stream=stream
    )
    if stream:
        for log in EventLogger().log(response):
            log.print()
    else:
        step_printer(response.steps) # print the steps of an agent's response in a formatted way. 


# ### Analyzing the Agent's Execution
# 
# Let's break down the output we just saw to understand how the ReAct agent processed the query:
# 
# * **Step 1 (Inference):** The agent receives the query. Its initial **Thought** is that it needs the user's location before it can search for weather risks *in that area*. It decides its first **Action** should be to use the `get_location` tool.
# * **Step 2 (Tool Execution):** The `get_location` tool is executed. The **Observation** is the result returned by the tool, which is the user's location: "Columbus, Ohio, US". (At the time of running this, this is where the cloud instance was running)
# * **Step 3 (Inference):** With the location obtained, the agent has a new **Thought**: It now knows *where* to search. Its next **Action** is to use the `web_search` tool, formulating the search query "weather-related risks in Columbus, Ohio".
# * **Step 4 (Tool Execution):** The `web_search` tool is executed with the generated query. The **Observation** is the search results returned by the web search tool, containing snippets from various sources about climate risks, precipitation, heat, and severe weather outlooks in Columbus, Ohio.
# * **Step 5 (Inference):** The agent processes the search results (the Observation from Step 4). Its final **Thought** is that it has enough information. It then formulates and provides the final **Answer**, summarizing the key weather risks found (increased precipitation/flooding and heat) and noting their potential impact on network connectivity and system availability, directly addressing the user's original question.
# 
# This sequence clearly illustrates the **Reasoning (Thought), Action (Tool Use), and Observation (Tool Output)** loop that defines the ReAct agent's problem-solving process.

# ## Lab Summary: Exploring ReAct Agents and Tool Use
# 
# In this Lab, you delved into the world of **ReAct agents** within the Llama Stack framework, understanding how these agents go beyond simple input-output by combining reasoning and action. You learned how ReAct agents can effectively leverage multiple tools to accomplish complex, multi-step tasks.
# 
# You learned how to:
# 
# * **Understand the ReAct framework:** You explored the core concept of the **Reason-Act-Observe loop** that defines how ReAct agents operate, contrasting it with more traditional agents.
# * **Add and manage models:** You practiced adding a new model (`granite3.2:8b`) to your Llama Stack Server programmatically using the Python client and noted how the server makes models available via a unified API.
# * **Build and configure a ReAct agent:** You initialized a `ReActAgent` instance, providing it access to both built-in (`websearch`) and custom (`get_location`) tools.
# * **Observe the agent's Chain of Thought:** By examining the output steps, you saw the agent's internal reasoning process (Thought), its decisions to use tools (Action), and the results it received from those tools (Observation).
# * **Process complex queries:** You experienced how the agent uses the ReAct loop to break down a complex user query into smaller steps, gathering necessary information via tools before formulating a final answer.
# 
# Through these exercises, you gained practical experience with setting up and running ReAct agents, highlighting their power in dynamic problem-solving and appreciating how the Llama Stack framework facilitates the integration of models and tools necessary for agentic workflows.
