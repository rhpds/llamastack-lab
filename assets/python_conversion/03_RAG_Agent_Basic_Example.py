#!/usr/bin/env python
# coding: utf-8

# # Getting Familiar with RAG Basics
# 
# In this section of the lab, we will review some basic capabilities of RAG, by the end of this section, you will be able to: 
# - Initialize the RAG *agent* to use the LlamaStack server we created in previous sections
# - Create a simple VectorDB to contain our documents 
# - Embed (insert) our documents into the VectorDB
# - Retrieve answers based on our documents using the RAG agent and LLM
# 
# 
# RAG stands for Retrieval-Augmented Generation (RAG). It's a novel approach that combines information retrieval and natural language generation techniques to improve the efficiency of knowledge graph-based systems, such as question-answering models and text summarization. The core idea is to leverage pre-trained language models to retrieve relevant information from a knowledge base or database, and then use this retrieved information to generate high-quality responses. 
# 
# In simple terms, RAG allows us to take documents (PDF, Markdown, Websites or other) that are not availble within our model and allow our agent to provide answers based on the content of those documents. Here are a few examples of what enterprise companies might use RAG: 
# 
# **1. Customer Service Chatbots with RAG**
# 
# A large retail company could use RAG to power their customer service chatbots. When a customer asks a question about a product, the chatbot uses RAG to retrieve relevant information from its knowledge base and generate a response that is both accurate and helpful. For example, if a customer asks "What are the features of the new Somephone 13", the chatbot can use RAG to retrieve information from its database and respond with a detailed list of features, including specifications, pricing, and availability.
# 
# **2. Personalized Product Recommendations**
# 
# An e-commerce company like could use RAG to generate personalized product recommendations for customers based on their browsing history and purchase behavior. When a customer visits the website, RAG is used to retrieve information about products that are similar to what they've previously purchased or browsed. The system then generates a list of recommended products, along with detailed descriptions and prices, to help the customer make an informed purchasing decision.
# 
# **3. Automated Content Generation for Marketing Campaigns**
# 
# A marketing agency could use RAG to generate high-quality content for their clients' marketing campaigns. For example, if a client wants to create a blog post about the benefits of using artificial intelligence in marketing, RAG can be used to retrieve relevant information from its database and generate a draft of the article. The system can then refine the content based on the client's brand voice and style, ensuring that the final product meets their expectations.
# 
# **4. Technical Writing Assistance**
# 
# A software development company could use RAG to assist with technical writing tasks such as generating user manuals, API documentation, and technical guides. When a developer needs to write code comments or documentation for a new feature, RAG can be used to retrieve relevant information from its database and generate high-quality text that is both accurate and concise.

# ### Install Python Prerequisist
# 
# As always, let's start by installing the Python Libraries we neeed

# In[ ]:


get_ipython().system('pip install -U llama-stack-client==0.2.5 dotenv')


# ### Define the LLamastack server and Model
# 
# Let's point our variables to our Llamastack server and chose our desired model: 

# In[ ]:


import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# for our lab, we will just define our variables manualy here:
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
print("--- Available models: ---")
for m in models:
    print(f"{m.identifier} - {m.provider_id} - {m.provider_resource_id}")


# Now that our client is set up, let's go through some very simple code snippets, to get you familiar with the syntex. If you used other AI Frameworks, this will soon feel very familiar, as Llamastack follows similar principals and terminology, while allowing a standard to help you quickly shift different components in and out 

# ### List available vectorDB providers
# Let's see what vectorDBs our server support out of the box, and select the first available. 
# 
# In Production, we would probably want to select a specific provider, but at this point of our development cycle, we are probably still interested in trying out different VectorDB options, notice that with LlamaStack these are interchangeable and absracted from the code, allowing us to switch them our at will.  
# 

# In[ ]:


# Get provider list and print it out 

print("List of providers available in our LlamaStack Server:")
providers = client.providers.list()
for provider in providers:
    print(provider)


vector_providers = []
for provider in client.providers.list():
    if provider.api == "vector_io":
        print(f"Found VectorDB provider: {provider.provider_id}\n")  # Simple print
        vector_providers.append(provider)

# In this example, we only have one provider, but on other server we might have many. here, we simply select the first one.
selected_vector_provider = vector_providers[0]




# ### Register and Initialize a new VectorDB on our LlamaStack Server
# 
# In this step, you will register a new vector database with the client. This process involves creating a unique identifier for the database and associating it with an embedding model.
# We will use the built-in "all-MiniLM-L6-v2" LLM to embed documetns into our VLLM.

# In[ ]:


import uuid

vector_db_id = f"test_vector_db_{uuid.uuid4()}"
client.vector_dbs.register(
    vector_db_id=vector_db_id,
    embedding_model="all-MiniLM-L6-v2",
    embedding_dimension=384,
    provider_id=selected_vector_provider.provider_id,
)


# ### Process documents 
# 
# In this step, we will process the documents and embed (insert) them into the vectorDB so we can retrieve them later.
# Note that we are reading them directly from the web, but we could of course also read them from a local folder. 
# 
# When inserting documents into a VectorDB, documents are split into "Chunks". Choices made at this stage can affect results by impacting model accuracy, processing speed, and memory usage. 
# The chunk size can be set by `chunk_size_in_tokens`, which refers to the number of tokens (small units of text) in each processed chunk. 
# 
# In this lab, we will not get into this topic and will just use a simple value.

# In[ ]:


from llama_stack_client.types import Document
urls = [
    "Azure_Mongrove_Wilderness.md",
    "Crimson_Basin.md",
    "Granite_Spire.md",
    "Obsidian_Rainforest.md",
    "Prismatic_Painted_Prairie.md",
]

# Read documents into the "documents" array
document_dirctory="assets/Parks"
# Read documents into the "documents" array
documents = [
    Document(
        document_id=f"num-{i}",
        content=f"https://raw.githubusercontent.com/rhpds/llamastack-lab/refs/heads/main/{document_dirctory}/{url}",
        mime_type="text/plain",
        metadata={},
    )
    for i, url in enumerate(urls)
]

# Insert the documents into the vectorDB
client.tool_runtime.rag_tool.insert(
    documents=documents,
    vector_db_id=vector_db_id,
    chunk_size_in_tokens=300,
)


# ### Define and initialize the Agent
# 
# In this section, we are creating the *Agent*, defining its *model*, *instructions* (or Prompt), and its *tools*, specifically, the built-in *RAG* tool.
# 
# Notice that we are passing our vectorDB to the agent using `vector_db_ids` and setting some query configuration options with `query_config`
# 
# 

# In[ ]:


from llama_stack_client import Agent

query_config = {
    "query_generator_config": {
        "type": "default",
        "separator": " "
    },
    "max_tokens_in_context": 300,
    "max_chunks": 2
}

rag_agent = Agent(
    client,
    model=os.environ['LLAMA_STACK_MODEL'],
    instructions="You should always use the RAG tool to answer questions, only answer what you are asked, don't add more information than requested",
    tools=[{
        "name": "builtin::rag",
        "args": {"vector_db_ids": [vector_db_id],"query_config": query_config  },
    }],
)



# ### Create a list of questions to test our retrieval agent
# 
# We will create an array of questions so we can test our retrieval agent.
# 
# You will notice, that for each example we also provided the expected answer. In a real-world scenario, we would use the answers to score and evaluate the responses. 
# This is a crucial part of development if this kind of function, Llamastack offers build-in to manage exactly this type of process, allowing you to test many models, methods, VectorDBs and having the metrics to see which one works the best and to allow you to see if your implementation drifted over time. 
# 
# Similar to regresssion testing in traditional code scenarios, consider a company that wants to evaluate a different model and needs a way to measure the improvement/degradation in quality. 

# In[ ]:


examples = [
    {
        "input_query": "What is the vehicle entry fee for Prismatic Painted Prairie?",
        "expected_answer": "$20"
    },
    {
        "input_query": "What kind of camping is available at Azure Mangrove Wilderness that requires tide-dependent access?",
        "expected_answer": "Chickee Platforms"
    },
    {
        "input_query": "When was Obsidian Rainforest Reserve established?",
        "expected_answer": "1976"
    },
    {
        "input_query": "What is a unique feature of Crimson Basin Desert Preserve?",
        "expected_answer": "Rare 'singing dunes' phenomenon during high winds"
    },
    {
        "input_query": "Are pets allowed at Granite Spire Alpine Sanctuary?",
        "expected_answer": "Prohibited"
    },
    {
        "input_query": "What is the size of Azure Mangrove Wilderness?",
        "expected_answer": "142,500 acres"
    },


]


# ### Run Retrieval agent
# 
# This step will get 4 separate responses from our agent, allowing us to manually evaluate its capabilities. 
# > **Note:**
# > You might have a quick laugh as the initial results will be hit and miss. This is an initial implementation and tuning, scoring, and tuning will be the next steps in a real-world scenario.
# >

# In[ ]:


from rich.pretty import pprint
import rich

rag_agent.sessions=[]
for example in examples:
    rag_session_id = rag_agent.create_session(session_name=f"rag_session_{uuid.uuid4()}")
    response = rag_agent.create_turn(
        messages=[
            {
                "role": "user",
                "content": example["input_query"]
            }
        ],
        session_id=rag_session_id,
        stream=False
    )
    rich.print(f"[bold cyan]Question:[/bold cyan] {example['input_query']}")
    rich.print(f"[bold yellow]Agent Answer:[/bold yellow] {response.output_message.content}")


# ### Inspecting the Agent's process
# 
# If you are interested, you can review the steps the agent has taken and see which documents were retrieved. 
# This is a crucial debugging tool when trying to understand what is causing your retrieval to succeed or fail. 

# In[ ]:


print("Session ID\t\t Question")
i=0
for session in rag_agent.sessions:
    session_response = client.agents.session.retrieve(agent_id=rag_agent.agent_id, session_id=rag_agent.sessions[i])
    print(i,"\t\t\t",session_response.turns[0].input_messages[0])
    i=i+1    

## Set this to whichever session you want to review:
session_to_debug=0

session_response = client.agents.session.retrieve(agent_id=rag_agent.agent_id, session_id=rag_agent.sessions[session_to_debug])
pprint(session_response.turns)


# ### Optional - Erasing existing VectorDBs
# 

# ### Erase existing VectorDBs
# 
# If you want to play with some chunk options and see if you can improve the results, you might want to delete your VectorDBs
# 

# In[ ]:


# Unregister all vector databases (THIS IS FOR DEBUG NOT FOR LAB)
for vector_db_id in client.vector_dbs.list():
    print(f"Unregistering vector database: {vector_db_id.identifier}")
    client.vector_dbs.unregister(vector_db_id=vector_db_id.identifier)


# ## Lab Summary: Getting Familiar with RAG Basics
# 
# In this lab, you were introduced to the fundamental concepts and basic capabilities of Retrieval-Augmented Generation (RAG) using the Llama Stack framework. You learned how RAG combines information retrieval and natural language generation to enhance knowledge graph-based systems. This allows an agent to provide answers based on documents not originally available to the model.
# 
# Through the exercises, you learned to:
# 
# * **Initialize a RAG agent:** You set up the RAG agent to work with the LlamaStack server.
# * **Create and manage a VectorDB:** You created a simple VectorDB to store documents and learned how to embed (insert) documents into it.
# * **Process and embed documents:** You saw how documents are processed and chunked before being embedded into the VectorDB.
# * **Retrieve answers using the RAG agent:** You practiced retrieving answers to questions based on the content of the documents stored in the VectorDB, utilizing the RAG agent and an LLM.
# * **Inspect the agent's process:** You explored how to review the steps the agent takes during retrieval, which is helpful for debugging and understanding the retrieved documents.
# 
# By completing this lab, you gained a foundational understanding of the RAG process, including setting up the necessary components, preparing data, and using a RAG agent to query custom documents. This experience highlights how Llama Stack provides a structured way to implement RAG and manage the lifecycle of vector databases.
