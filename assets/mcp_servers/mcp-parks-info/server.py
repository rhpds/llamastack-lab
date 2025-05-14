# server.py
# main ASGI application for the MCP Parks Info server

from starlette.applications import Starlette
from starlette.routing import Mount, Host
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("mcp-parks-info")

@mcp.tool()
def greet(name: str) -> str:
    """Say hello to a person.
    
    Examples of user prompts:
    - "greet John"
    - "say hello to Alice"
    """
    return f"Hello, {name}!"

@mcp.resource("status://health")
def get_health() -> str:
    """Get the server health status of the MCP Parks Info Server.
    
    Examples of user prompts:
    - "health check"
    - "is the server healthy?"
    """
    return "Status: Healthy"

# Default parameters for RAG tools
DEFAULT_SERVER_URL = "http://localhost:8321"
DEFAULT_SELECTED_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
DEFAULT_VECTOR_DB_ID = "Our_Parks_DB"

def _execute_park_rag(park_name: str, agent_prompt: str, input_query: str) -> dict:
    """
    Internal helper to execute a RAG call for a park tool.
    """
    try:
        from llama_stack_client import LlamaStackClient, Agent
    except ImportError:
        return "Error: The 'llama_stack_client' library is not installed. Please install it."

    client = LlamaStackClient(base_url=DEFAULT_SERVER_URL)
    query_config = {
        "query_generator_config": {"type": "default", "separator": " "},
        "max_tokens_in_context": 300,
        "max_chunks": 2
    }

    rag_agent = Agent(
        client,
        model=DEFAULT_SELECTED_MODEL,
        instructions=agent_prompt,
        tools=[{"name": "builtin::rag", "args": {"vector_db_ids": [DEFAULT_VECTOR_DB_ID], "query_config": query_config}}]
    )

    import hashlib, json as _json
    session_id = rag_agent.create_session(hashlib.md5(input_query.encode()).hexdigest())
    response = rag_agent.create_turn(
        messages=[{"role": "user", "content": input_query}],
        session_id=session_id,
        stream=False
    )
    # Serialize to JSON-serializable primitives
    json_str = response.model_dump_json()
    return _json.loads(json_str)

@mcp.tool()
def get_park_location(park_name: str) -> dict:
    """Get the location of a specified park using retrieval-augmented generation (RAG).
    
    Examples of user prompts:
    - "where is Granite Spire?"
    - "where is Yellowstone National Park?"
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer the question about the park's location.",
        input_query=f"What is the location of {park_name}?"
    )

@mcp.tool()
def get_park_cost(park_name: str) -> dict:
    """Get the cost to enter a specified park using retrieval-augmented generation (RAG).
    
    Examples of user prompts:
    - "what is the cost of entry to Azure Mangrove Wilderness Park?"
    - "how much does it cost to visit Yosemite National Park?"
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer the question about the park's cost.",
        input_query=f"What is the cost of entering {park_name}?"
    )

@mcp.tool()
def get_park_description(park_name: str) -> dict:
    """Get a description of a specified park using retrieval-augmented generation (RAG).
    
    Examples of user prompts:
    - "Give me some details about Prismatic Painted Prairie"
    - "provide a description of Crimson Basin"
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer the question about the park's description.",
        input_query=f"Provide a description of {park_name}."
    )

@mcp.tool()
def get_park_camping_sites(park_name: str) -> dict:
    """Get the camping sites available at a specified park using retrieval-augmented generation (RAG).
    
    Examples of user prompts:
    - "what camping sites are available in Yosemite National Park?"
    - "list the camping sites at Grand Canyon National Park"
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer the question about the park's camping sites.",
        input_query=f"What are the camping sites available in {park_name}?"
    )

@mcp.tool()
def get_park_seasonal_operations(park_name: str) -> dict:
    """Get the seasonal operations of a specified park using retrieval-augmented generation (RAG).
    
    Examples of user prompts:
    - "what are the seasonal operations for Glacier National Park?"
    - "when is Acadia National Park open for winter activities?"
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer the question about the park's seasonal operations.",
        input_query=f"What are the seasonal operations for {park_name}?"
    )

@mcp.tool()
def get_park_seasonal_attractions(park_name: str) -> dict:
    """Get the seasonal attractions of a specified park using retrieval-augmented generation (RAG).
    
    Examples of user prompts:
    - "what seasonal attractions does Zion National Park offer?"
    - "what events occur during spring at Joshua Tree National Park?"
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer the question about the park's seasonal attractions.",
        input_query=f"What are the seasonal attractions for {park_name}?"
    )

@mcp.tool()
def get_park_other_information(park_name: str) -> dict:
    """Get additional information about a specified park using retrieval-augmented generation (RAG).
    
    Examples of user prompts:
    - "Provide other information for Redwood National Park"
    - "give me additional facts about Denali National Park"
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer additional questions about the park.",
        input_query=f"Provide other information for {park_name}."
    )

app = Starlette(
    routes=[
        # Mount the MCP server's SSE app at the /mcp path
        Mount('/', app=mcp.sse_app()),
    ]
)