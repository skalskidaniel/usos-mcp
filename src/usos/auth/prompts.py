from fastmcp.prompts import prompt


@prompt(
    name="authenticate_me",
    description="Use this prompt if you are using the MCP for the first time or need to authenticate.",
)
def authenticate_me_prompt() -> str:
    return "\n".join(
        [
            "You are going to guide the user through the USOS authentication process using the `login` tool.",
            "Perform one step at a time and wait for the user's response before calling the tool again with new parameters.",
            "1. Start by calling the `login` tool with no arguments to initialize the session.",
            "2. Inspect the tool's returned `status` and follow these instructions:",
            "   - If status is `AWAITING_BASE_URL`: Ask the user for the name of their university. Once provided, read the `usos://universities/supported` resource to match their university to a `base_url`. If found, call `login(base_url=...)` with the matched URL. If their university is not supported, ask them for their custom USOS base URL directly and call `login(base_url=...)` with that.",
            "   - If status is `AWAITING_APP_REGISTRATION`: Instruct the user to visit `<base_url>/developers` (replacing `<base_url>` with the URL provided by the tool or matched in the previous step), log in, register a new application, and retrieve a `Consumer Key` and `Consumer Secret`. Ask the user to provide these credentials, then call `login(consumer_key=..., consumer_secret=...)`.",
            "   - If status is `AWAITING_PIN`: Show the provided `authorize_url` to the user and instruct them to click the link, authorize the app, and paste the PIN code back to you. Once they provide it, call `login(pin=...)`.",
            "   - If status is `SUCCESS`: Confirm to the user that authentication is complete and the server is fully ready. Mention that their credentials have been saved to the local configuration store, and that they can use the `logout` tool if they ever want to log out.",
        ]
    )
