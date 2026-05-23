import json
from pathlib import Path

CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"

def save_credentials(token: str, token_secret: str) -> None:
    data = {"oauth_token": token, "oauth_token_secret": token_secret}
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f)

def load_credentials() -> tuple[str | None, str | None]:
    if not CREDENTIALS_FILE.exists():
        return None, None
    try:
        with open(CREDENTIALS_FILE, "r") as f:
            data = json.load(f)
            return data.get("oauth_token"), data.get("oauth_token_secret")
    except Exception:
        return None, None
