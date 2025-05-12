#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# MCP Servers


# In[31]:


from src.utils import step_printer


# In[ ]:


Let's run our first MCP Server. The MCP-Weather container


# Run this in a terminal: 
# 
# ```bash
# CONTAINER_NAME=mcp-weather
# CONTAINER_IMAGE="mcp-weather"
# CONTAINER_TAG="0.1"
# REMOTE_REGISTRY="local-registry-quay-local-quay-registry.apps.ocpvdev01.dal13.infra.demo.redhat.com/rhdp/"
# 
# podman run -d \
# --name $CONTAINER_NAME \
# --network=host \
# ${REMOTE_REGISTRY}${CONTAINER_IMAGE}:latest \
# --port 8005  

# In[6]:


get_ipython().system('curl --max-time 1 http://localhost:8005/sse 2>/dev/null')


# In[39]:


import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# for communication with Llama Stack
from llama_stack_client import LlamaStackClient

# These libraries are just here to print the results from the agent in a more human-readable way 
from termcolor import cprint
import uuid
from llama_stack_client.lib.agents.event_logger import EventLogger
stream=False ## Defaulting to False, you can change this throughout the section to "True" if you wanted to see the output in another format (Using EventLogger)

# for our lab, we will just define our variables manualy here, in a regular application, this would be ready directly from the local .env file and we would comment these lines out
os.environ['LLAMA_STACK_SERVER'] = 'http://localhost:8321'

# We will be using the Tavily web search service (docs.tavily.com/)
tavily_search_api_key='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'
provider_data = {"tavily_search_api_key": tavily_search_api_key}

LLAMA_STACK_SERVER=os.getenv("LLAMA_STACK_SERVER")

client = LlamaStackClient(
    base_url=LLAMA_STACK_SERVER,
    provider_data=provider_data
)
# List available models
models = client.models.list()
print("--- Available models: ---")
for m in models:
    print(f"{m.identifier} - {m.provider_id} - {m.provider_resource_id}")

# For our development purposes, we might want to change different models and test with them, these lines select the first available model in the Llama Stack server. 
SELECTED_MODEL=models[0].identifier
print("--- Selected model: ---")
print(SELECTED_MODEL)


# In[40]:


registered_tools = client.tools.list()
registered_toolgroups = [t.toolgroup_id for t in registered_tools]

for tools in registered_tools:
    print(tools)


# In[41]:


client.toolgroups.register(
        toolgroup_id="mcp::mcp-weather",
        provider_id="model-context-protocol",
        mcp_endpoint={"uri":"http://localhost:8005/sse"},
    )


# In[42]:


registered_tools = client.tools.list()
registered_toolgroups = [t.toolgroup_id for t in registered_tools]

for tools in registered_tools:
    print("\n")
    print(tools)


# In[43]:


from llama_stack_client.lib.agents.agent import Agent

agent = Agent(
    client, 
    model=SELECTED_MODEL,
    instructions="""You are a helpful agent with access to tools, use the weather tool to answer questions
            """ ,
    tools=["mcp::mcp-weather"],
)


# In[44]:


stream=False
user_prompts = [
       "what is the weather in boulder colorado",
       "are there any weather alerts for Boston at the moment?",
]


for prompt in user_prompts:
    # Generate a new Unique Identifier for each session 
    new_uuid = uuid.uuid4()
    session_id = agent.create_session(f"web-session-{new_uuid}")

    cprint(f"\n{'='*100}\nProcessing user query: {prompt}\n{'='*100}", "blue")


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


# In[ ]:




