#!/usr/bin/env python
# coding: utf-8

# # Getting Familiar with Llama Stack Basics
# 
# In this section of the lab, we will review some basic capabilities of llamastack, by the end of this section, you will be able to: 
# - Initialize the *client* to use the LlamaStack server we created in previous sections
# - Create a simple *chat completion* request from the llm and recieve a response
# - Use structured data methods to extact just the information you need from the LLM response
# 
# 

# ### Installing llamatack libraries
# 
# Let's start by installing the Python Libraries we neeed: (click on the code cell and press Shift + Enter keys

# In[ ]:


get_ipython().system('pip install -U llama-stack-client==0.2.5 dotenv')


# ### Define the LLamastack server and Model
# 
# Let's point our variables to our Llamastack server and chose our desired model: 

# In[ ]:


# Load environment variables from .env file
import os
from dotenv import load_dotenv
load_dotenv()

os.environ['LLAMA_STACK_SERVER'] = 'http://localhost:8321'
os.environ['LLAMA_STACK_MODEL'] = 'meta-llama/Llama-3.2-3B-Instruct'


# > **Note:**
# >When running this code in a regular Python application, we would usually like to read environment variables from an `.env` file, for our needs in this lab, we will hard code these in this cell, to make things more clear
# >

# ### Initialize the *Client* 
# As a first step, let's define our client, provide it our Llama-Stack Server location and select the model we would like to work with, later, we will see that pointing this to a different location (Llama-Stack Serve) is all we would need to do to move to a production environment.

# In[ ]:


from llama_stack_client import LlamaStackClient

LLAMA_STACK_SERVER=os.getenv("LLAMA_STACK_SERVER")
LLAMA_STACK_MODEL=os.getenv("LLAMA_STACK_MODEL")

client = LlamaStackClient(base_url=LLAMA_STACK_SERVER)

# List available models
models = client.models.list()

# Print table header
print("--- Available models: ---")

print("Model Identifier                         Provider ID     Provider Resource ID")

for m in models:
    print(f"{m.identifier:40} {m.provider_id:15} {m.provider_resource_id}")


# ### Simple LLM *chat completion* and response
# Now that our client is set up, let's go through some very simple code snippets, to get you familiar with the syntex. If you used other AI Frameworks, this will soon feel very familiar, as Llamastack follows similar principals and terminology, while allowing a standard to help you quickly shift different components in and out 

# In[ ]:


response = client.inference.chat_completion(
    model_id=LLAMA_STACK_MODEL,
    messages=[
        {"role": "system", "content": "You're a helpful assistant."},
        {
            "role": "user",
            "content": "What is the top speed of a leopard?",
        },
    ],
    # temperature=0.0, 
)
print(response.completion_message.content)


# ### Extracting structued data from response
# Often, we want the LLM to provide us a specific answer, not in a conversational manner, using structured data can be helpful, later in the lab, you will see how we want certain agents to give us specific facts and not a short story about the facts.
# 
# Try different animals, to see how the structured data can be helpful for us:

# In[ ]:


from pydantic import BaseModel
import json

class AnimalSpeed(BaseModel):
    speed: int
    animal: str
    metric_type: str

response = client.inference.chat_completion(
    model_id=LLAMA_STACK_MODEL,
    messages=[
        {"role": "system", "content": "You're a helpful assistant."},
        {
            "role": "user",
            "content": "What is the top speed of a leopard?",            
        },
    ],
    stream=False,    
    response_format={
            "type": "json_schema",
            "json_schema": AnimalSpeed.model_json_schema(),
        }
)


try:
    response_data = json.loads(response.completion_message.content)
    animal = AnimalSpeed(**response_data)    
    print("-------")
    print("Speed: ", animal.speed)
    print("Animal: ", animal.animal)
    print("metric_type: ", animal.metric_type)
    print("-------")
except (json.JSONDecodeError, ValueError) as e:
    print(f"Invalid format: {e}")


# ### Summary 
# Ok, so now we know that using llamastack and python is easy and approachable, let's get into some more exciting things!
