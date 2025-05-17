import re

def insert_tools_to_prompt(my_instructions: str, allowed_tools_array: list) -> str:
    """
    Formats the source template string by inserting tool names and descriptions
    from a list of Tool objects.

    Args:
        my_instructions: A multi-string variable containing the source template.
                         Expected to have <<tool_names>> and <<tool_descriptions>> placeholders.
        allowed_tools_array: A list of Tool objects obtained from the client library.

    Returns:
        A multi-string variable with placeholders replaced by formatted tool information.
    """
    tool_names = []
    tool_descriptions = []

    for tool in allowed_tools_array:
        tool_names.append(tool.identifier)
        formatted_parameters = []
        for param in tool.parameters:
            # Escape single quotes in the parameter description for the string literal
            param_description_escaped = param.description.replace("'", "\\'")
            formatted_parameters.append(
                f"Parameter(description='{param_description_escaped}', name='{param.name}', parameter_type='{param.parameter_type}', required={param.required}, default={param.default})"
            )
        cleaned_description = tool.description.replace('\\n', '\n').replace("    ", "").replace("'", "\\'")

        tool_descriptions.append(
            f"- {tool.identifier}: {{'name': '{tool.identifier}', 'description': '{cleaned_description}', 'parameters': [{', '.join(formatted_parameters)}]}}"
        )

    tool_names_string = ", ".join(tool_names)

    tool_descriptions_string = "\n".join(tool_descriptions)

    output_template = my_instructions.replace("<<tool_names>>", tool_names_string).replace("<<tool_descriptions>>", tool_descriptions_string)

    return output_template



