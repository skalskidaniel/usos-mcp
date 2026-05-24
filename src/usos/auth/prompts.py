from usos.registry import registry

@registry.prompt(
    name="setup_usos_authentication",
    description="Step-by-step guide for setting up USOS API authentication."
)
def setup_usos_authentication() -> str:
    """Use this prompt if you are using the MCP for the first time or need to authenticate."""
    return "\n".join([
        "Follow these steps strictly to authenticate the user with the USOS API:",
        "1. Ask the user for the name of their university.",
        "2. Once provided, use the `supported-universities` resource to find their university and its `base_url`.",
        "3. Instruct the user to visit `<base_url>/developers` (replacing `<base_url>` with the URL from step 2). Explain they need to log in, register an application, and obtain a `Consumer Key` and `Consumer Secret`. Ask the user to provide these credentials back to you in the chat.",
        "4. Wait for the user to provide the consumer key and secret.",
        "5. Once provided, use the `get_oauth_request_token` tool with the found `base_url` and the user-provided `consumer_key` and `consumer_secret` to obtain an `oauth_token`, `oauth_token_secret`, and an `authorize_url`.",
        "6. Provide the `authorize_url` to the user and instruct them to click the link, authorize the app, and retrieve the PIN.",
        "7. Wait for the user to provide the PIN.",
        "8. Once the user provides the PIN, use the `get_oauth_access_token` tool with the `base_url`, `consumer_key`, `consumer_secret`, `oauth_token` (from step 5), `oauth_token_secret` (from step 5), and the provided `pin`.",
        "9. Present the user with a code snippet containing their final environment variables to add to their MCP client configuration (e.g. Claude Desktop config or .env):",
        "   USOS_API_CONSUMER_KEY=<their consumer key>",
        "   USOS_API_CONSUMER_SECRET=<their consumer secret>",
        "   USOS_API_BASE_URL=<base_url found in step 2>",
        "   USOS_API_OAUTH_TOKEN=<oauth_token from step 8>",
        "   USOS_API_OAUTH_TOKEN_SECRET=<oauth_token_secret from step 8>",
        "Explain that after adding these configuration values to their MCP client environment, they need to restart the client so that the server can authenticate automatically."
    ])
