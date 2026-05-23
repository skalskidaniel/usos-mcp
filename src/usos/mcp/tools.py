import webbrowser
from fastmcp import FastMCP
from usos.auth import get_authorization_url, verify_pin_and_save_token, get_authenticated_session

def register_auth_tools(mcp: FastMCP) -> None:

    @mcp.tool()
    def start_authentication() -> str:
        """
        Start the authentication process for the USOS API.
        This will return an authorization URL and attempt to open it in your default browser.
        The user must log in to USOS and copy the provided PIN.
        
        Returns:
            A string containing instructions and the authorization URL.
        """
        try:
            url = get_authorization_url()
            webbrowser.open(url)
            return (
                f"I've attempted to open the authorization page in your browser.\n"
                f"If it didn't open, please visit: {url}\n\n"
                f"After authorizing, USOS will display a PIN. Use the `submit_auth_pin` tool with that PIN."
            )
        except Exception as e:
            return f"Failed to start authentication: {str(e)}"

    @mcp.tool()
    def submit_auth_pin(pin: str) -> str:
        """
        Submit the authorization PIN obtained from the browser after logging in.
        This completes the authentication process.
        
        Args:
            pin: The numeric PIN provided by the USOS authentication page.
        """
        try:
            success = verify_pin_and_save_token(pin.strip())
            if success:
                return "Authentication successful!"
            return "Authentication failed for an unknown reason."
        except Exception as e:
            return f"Failed to verify PIN: {str(e)}"

    @mcp.tool()
    def check_auth_status() -> str:
        """
        Check if the MCP server is currently authenticated with the USOS API.
        """
        session = get_authenticated_session()
        if session is not None:
            return "Server is authenticated."
        else:
            return "Server is NOT authenticated. Please run `start_authentication`."
