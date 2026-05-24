from usos.registry import registry

@registry.prompt()
def authenticate_me() -> str:
    """Use this prompt if you are using the MCP for the first time"""
    #TODO enhance this prompt
    return "\n".join([
        "Tell me how can I authenticate myself to use this MCP.",
        "Specify how to update the env variables in my MCP host.",
        "You should ask first to which university do I attend."
        "Then, provide correct USOS_API_BASE_URL based on the universities resource.",
        "You should then use get_oauth_token tool to give me sign-in URL.",
        "I will then provide a PIN code for you.",
        "You should use this code for get_persistent_oauth_token tool.",
        "At the end you should give me a snippet with the configuration to paste in my MCP host configuration,"
        "or preferably do it by yourself"
    ])