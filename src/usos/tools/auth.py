import webbrowser
import json
from pathlib import Path
from fastmcp import FastMCP
from usos.auth import get_authorization_url, verify_pin_and_save_token, get_authenticated_session, set_base_url


def register_auth_tools(mcp: FastMCP) -> None:
    UNIVERSITIES_FILE = Path(__file__).parents[1] / "auth" / "universities.json"
    UNIVERSITIES_KEYS = set()
    with open(UNIVERSITIES_FILE, "r", encoding="utf-8") as f:
        universities = json.load(f)
        for uni in universities.keys():
            UNIVERSITIES_KEYS.add(uni)

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

    @mcp.tool()
    def get_supported_universities() -> dict[str, dict[str, str]]:
        """
        Check which universities are supported
        :return: dict with Polish and English names of the supported universities
        """

        if not UNIVERSITIES_FILE.exists():
            return {}

        with open(UNIVERSITIES_FILE, "r", encoding="utf-8") as f:
            universities = json.load(f)
        return universities

    @mcp.tool()
    def set_university(university_id: str) -> str:
        """
        Set the api endpoints for the exact university.
        This tool must be called before starting the authentication process.

        :param university_id: University ID (must be in supported_universities keys)
        :return: confirmation message
        """
        if university_id not in UNIVERSITIES_KEYS:
            raise ValueError(f"The university key {university_id} not found in compatible universities.")
        
        with open(UNIVERSITIES_FILE, "r", encoding="utf-8") as f:
            universities = json.load(f)
            
        base_url = universities[university_id]["base_url"]
        set_base_url(base_url)
        
        return f"Successfully set university to {universities[university_id].get('name_en', university_id)} with base URL: {base_url}"