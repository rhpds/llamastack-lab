from llama_stack_client.lib.agents.client_tool import client_tool
import geocoder

@client_tool
def get_location(query: str = "location"):
    """
    Provides the user's location upon request.

    This function uses the geocoder library to determine the user's location
    based on their IP address.  It returns the city, state, and country.

    :param query:  The query from the user.  Defaults to "location".
    :type query: str
    :return:  Information about the user's current location.
    :rtype: str

    Example:
        >>> get_location("where am i")
        "Your current location is: Some City, Some State, Some Country"
    """
    import geocoder
    try:
        g = geocoder.ip('me')
        if g.ok:
            return f"Your current location is: {g.city}, {g.state}, {g.country}" # can be modified to return latitude and longitude if needed
        else:
            return "Unable to determine your location"
    except Exception as e:
        return f"Error getting location: {str(e)}"


@client_tool
def get_location_dummy(query: str = "location"):
    """
    Provides the user's location upon request.

    This function is just a placeholder, but is good for testing

    :param query:  The query from the user.  Defaults to "location".
    :type query: str
    :return:  Information about the user's current location.
    :rtype: str

    Example:
        >>> get_location("where am i")
        "Your current location is: Some City, Some State, Some Country"
    """

    return f"Raleigh, North Carolina, USA"
