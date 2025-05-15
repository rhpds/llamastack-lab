from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("mcp-parks-info")

@mcp.resource("status://health")
def get_health() -> str:
    """Get the server health status of the MCP Parks Info Server.

    Examples:
    - "health check"
    - "is the server healthy?"
    """
    return "Status: Healthy"

# Default parameters for RAG tools
DEFAULT_SERVER_URL = "http://localhost:8321"
DEFAULT_SELECTED_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
DEFAULT_VECTOR_DB_ID = "Our_Parks_DB"

def _execute_park_rag(park_name: str, agent_prompt: str, input_query: str) -> dict:
    """Internal helper to execute a RAG call for a park tool."""
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
    # json_str = response["output_message"]["content"].model_dump_json()
    # return _json.loads(json_str)
    return {"result": response.output_message.content}

@mcp.tool()
def get_park_location(park_name: str) -> dict:
    """Get the location of a specified park.

    :param park_name: The name of the park (e.g., "Crimson Basin").
    :type park_name: str
    :return: A dictionary with the park's location and coordinates
    :rtype: dict

    Example:
        >>> get_park_location("Crimson Basin")
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer the question about the park's location.",
        input_query=f"What is the location and coordinates of {park_name}?"
    )

@mcp.tool()
def get_park_cost(park_name: str) -> dict:
    """Get the cost to enter a specified park.

    :param park_name: The name of the park (e.g., "Azure Mangrove Wilderness Park").
    :type park_name: str
    :return: A dictionary with cost information.
    :rtype: dict

    Example:
        >>> get_park_cost("Azure Mangrove Wilderness Park")
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer the question about the park's cost.",
        input_query=f"What is the cost of entering {park_name}?"
    )

@mcp.tool()
def get_park_description(park_name: str) -> dict:
    """Get a description of a specified park.

    :param park_name: The name of the park (e.g., "Prismatic Painted Prairie").
    :type park_name: str
    :return: A dictionary with the park's description.
    :rtype: dict

    Example:
        >>> get_park_description("Prismatic Painted Prairie")
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer the question about the park's description.",
        input_query=f"Provide a description of {park_name}."
    )

@mcp.tool()
def get_park_camping_sites(park_name: str) -> dict:
    """Get the camping sites available at a specified park.

    :param park_name: The name of the park (e.g., "Grand Canyon National Park").
    :type park_name: str
    :return: A dictionary with camping site details.
    :rtype: dict

    Example:
        >>> get_park_camping_sites("Grand Canyon National Park")
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer the question about the park's camping sites.",
        input_query=f"What are the camping sites available in {park_name}?"
    )

@mcp.tool()
def get_park_seasonal_operations(park_name: str) -> dict:
    """Get the seasonal operations of a specified park.

    :param park_name: The name of the park (e.g., "Glacier National Park").
    :type park_name: str
    :return: A dictionary with seasonal operation info.
    :rtype: dict

    Example:
        >>> get_park_seasonal_operations("Glacier National Park")
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer the question about the park's seasonal operations.",
        input_query=f"What are the seasonal operations for {park_name}?"
    )

@mcp.tool()
def get_park_seasonal_attractions(park_name: str) -> dict:
    """Get the seasonal attractions of a specified park.

    :param park_name: The name of the park (e.g., "Zion National Park").
    :type park_name: str
    :return: A dictionary with seasonal attractions.
    :rtype: dict

    Example:
        >>> get_park_seasonal_attractions("Zion National Park")
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer the question about the park's seasonal attractions.",
        input_query=f"What are the seasonal attractions for {park_name}?"
    )

@mcp.tool()
def get_park_other_information(park_name: str) -> dict:
    """Get additional information about a specified park.

    :param park_name: The name of the park (e.g., "Denali National Park").
    :type park_name: str
    :return: A dictionary with additional park facts.
    :rtype: dict

    Example:
        >>> get_park_other_information("Denali National Park")
    """
    return _execute_park_rag(
        park_name,
        agent_prompt="Use the RAG tool (builtin::rag) to answer additional questions about the park.",
        input_query=f"Provide other information for {park_name}."
    )

app = Starlette(
    routes=[
        Mount('/', app=mcp.sse_app()),
    ]
)
