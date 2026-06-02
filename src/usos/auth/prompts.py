from fastmcp.prompts import prompt

@prompt(
    name="setup_usos_authentication",
    description="Use this prompt if you are using the MCP for the first time or need to authenticate."
)
def setup_usos_authentication() -> str:
    return "\n".join([
        "Follow these steps strictly to authenticate the user with the USOS API. Perform one step at a time and wait for the user's response before proceeding.",
        "1. Ask the user for the name of their university.",
        "2. Once provided, use the `usos://universities/supported` resource to find their university and its `base_url`.",
        "3. Instruct the user to visit `<base_url>/developers` (replacing `<base_url>` with the URL from step 2). Explain they need to log in, register a new application (any name/description is fine for personal use), and obtain a `Consumer Key` and `Consumer Secret`. Ask the user to provide both of these credentials back to you in the chat.",
        "4. Wait for the user to provide the consumer key and secret.",
        "5. Once provided, use the `get_oauth_request_token` tool with the found `base_url`, the user-provided `consumer_key`, and the user-provided `consumer_secret` to obtain an `oauth_token`, `oauth_token_secret`, and an `authorize_url`. Keep the `oauth_token_secret` in your context, you will need it later.",
        "6. Provide the `authorize_url` to the user and instruct them to click the link, log in if prompted, authorize the app, and retrieve the PIN shown on the confirmation page.",
        "7. Wait for the user to provide the PIN.",
        "8. Once the user provides the PIN, use the `get_oauth_access_token` tool with only the provided `pin`. The `base_url`, `consumer_key`, and `consumer_secret` are retrieved automatically from the session context state set in step 5.",
        "9. Present the user with a JSON snippet containing their final environment variables to add to their MCP client configuration (e.g. `mcp.json` or Claude Desktop config):",
        '   "env": {',
        '     "USOS_API_CONSUMER_KEY": "<their consumer key>",',
        '     "USOS_API_CONSUMER_SECRET": "<their consumer secret>",',
        '     "USOS_API_BASE_URL": "<base_url found in step 2>",',
        '     "USOS_API_OAUTH_TOKEN": "<oauth_token from step 8>",',
        '     "USOS_API_OAUTH_TOKEN_SECRET": "<oauth_token_secret from step 8>"',
        '   }',
        "10. Remind the user that these values grant access to their USOS data and should be kept private. Explain that after saving these configuration values, they need to restart their MCP client (e.g. Cursor) so that the server can authenticate automatically."
    ])
