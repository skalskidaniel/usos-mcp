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
        "9. Inform the user that the authentication is complete and explain that their credentials have been saved automatically to the local config file (~/.config/usos-mcp/config.json). Describe that they can customize this location using the `USOS_API_CONFIG_PATH` environment variable if desired.",
        "10. Confirm that the server is now fully authenticated and that all other MCP tools are now active and ready for use. Mention that they do not need to restart their MCP client or do any manual configuration. Remind the user that if they ever want to sign out, they can use the `clear_authentication` tool."
    ])
