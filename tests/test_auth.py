import unittest
import os
import json
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import model helpers
from usos.auth.models import USOSAuthSettings, get_storage_dir
from usos.auth.utils import save_auth_config
from usos.auth.tools import login, logout


class MockContext:
    def __init__(self):
        self.state = {}
        self.notifications = []

    async def get_state(self, key):
        return self.state.get(key)

    async def set_state(self, key, value):
        self.state[key] = value

    async def delete_state(self, key):
        self.state.pop(key, None)

    async def info(self, msg):
        pass

    async def error(self, msg):
        pass

    async def warning(self, msg):
        pass

    async def send_notification(self, notification):
        self.notifications.append(notification)


class TestAuthConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file_path = Path(self.temp_dir.name) / "auth" / "credentials.json"

        # Clear any existing USOS_API_* environment variables to isolate fallback logic
        self.original_env = {}
        for key in list(os.environ.keys()):
            if key.startswith("USOS_API_"):
                self.original_env[key] = os.environ[key]
                del os.environ[key]
        
        # Patch the configuration directory path AFTER deleting other USOS_API_* environment variables
        os.environ["USOS_API_STORAGE_DIR"] = self.temp_dir.name

        # Patch ENV_PATH in models.py to prevent loading real .env files during test
        self.path_patcher = patch("usos.auth.models.ENV_PATH", Path(self.temp_dir.name) / ".nonexistent_env")
        self.path_patcher.start()

    def tearDown(self):
        if "USOS_API_STORAGE_DIR" in os.environ:
            del os.environ["USOS_API_STORAGE_DIR"]
        self.path_patcher.stop()
        self.temp_dir.cleanup()
        
        # Restore original environment variables
        for key, val in self.original_env.items():
            os.environ[key] = val

    def test_get_storage_dir_respects_env_override(self):
        self.assertEqual(get_storage_dir(), Path(self.temp_dir.name))

    def test_settings_load_from_environment(self):
        os.environ["USOS_API_CONSUMER_KEY"] = "env_key"
        os.environ["USOS_API_CONSUMER_SECRET"] = "env_secret"
        os.environ["USOS_API_BASE_URL"] = "env_url"
        os.environ["USOS_API_OAUTH_TOKEN"] = "env_token"
        os.environ["USOS_API_OAUTH_TOKEN_SECRET"] = "env_token_secret"

        settings = USOSAuthSettings(_env_file=None)
        self.assertEqual(settings.consumer_key, "env_key")
        self.assertEqual(settings.consumer_secret, "env_secret")
        self.assertEqual(settings.base_url, "env_url")
        self.assertEqual(settings.oauth_token, "env_token")
        self.assertEqual(settings.oauth_token_secret, "env_token_secret")

    def test_settings_fallback_to_store_file(self):
        config_data = {
            "consumer_key": "file_key",
            "consumer_secret": "file_secret",
            "base_url": "file_url",
            "oauth_token": "file_token",
            "oauth_token_secret": "file_token_secret"
        }
        self.config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file_path, "w", encoding="utf-8") as f:
            json.dump({"value": config_data}, f)

        settings = USOSAuthSettings(_env_file=None)
        self.assertEqual(settings.consumer_key, "file_key")
        self.assertEqual(settings.consumer_secret, "file_secret")
        self.assertEqual(settings.base_url, "file_url")
        self.assertEqual(settings.oauth_token, "file_token")
        self.assertEqual(settings.oauth_token_secret, "file_token_secret")

    def test_save_auth_config_writes_correct_values(self):
        asyncio.run(save_auth_config(
            consumer_key="save_key",
            consumer_secret="save_secret",
            base_url="save_url",
            oauth_token="save_token",
            oauth_token_secret="save_token_secret"
        ))
        
        self.assertTrue(self.config_file_path.exists())
        with open(self.config_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        value = data["value"]
        self.assertEqual(value["consumer_key"], "save_key")
        self.assertEqual(value["consumer_secret"], "save_secret")
        self.assertEqual(value["base_url"], "save_url")
        self.assertEqual(value["oauth_token"], "save_token")
        self.assertEqual(value["oauth_token_secret"], "save_token_secret")

    def test_authenticate_state_machine_flow(self):
        ctx = MockContext()

        # Step 1: Initialize (no parameters)
        res = asyncio.run(login(ctx=ctx))
        self.assertEqual(res["status"], "AWAITING_BASE_URL")
        self.assertEqual(asyncio.run(ctx.get_state("auth_step")), "AWAITING_BASE_URL")

        # Step 2: Provide base_url
        res = asyncio.run(login(base_url="https://usos.uw.edu.pl", ctx=ctx))
        self.assertEqual(res["status"], "AWAITING_APP_REGISTRATION")
        self.assertEqual(asyncio.run(ctx.get_state("auth_base_url")), "https://usos.uw.edu.pl")
        self.assertEqual(asyncio.run(ctx.get_state("auth_step")), "AWAITING_APP_REGISTRATION")

        # Step 3: Provide consumer credentials
        with patch("usos.auth.tools.OAuth1Session") as mock_oauth_cls:
            mock_oauth = MagicMock()
            mock_oauth.fetch_request_token.return_value = {
                "oauth_token": "req_token",
                "oauth_token_secret": "req_secret"
            }
            mock_oauth.authorization_url.return_value = "https://usos.uw.edu.pl/authorize?oauth_token=req_token"
            mock_oauth_cls.return_value = mock_oauth

            res = asyncio.run(login(
                consumer_key="my_key",
                consumer_secret="my_secret",
                ctx=ctx
            ))

        self.assertEqual(res["status"], "AWAITING_PIN")
        self.assertEqual(res["authorize_url"], "https://usos.uw.edu.pl/authorize?oauth_token=req_token")
        self.assertEqual(asyncio.run(ctx.get_state("auth_step")), "AWAITING_PIN")
        self.assertEqual(asyncio.run(ctx.get_state("oauth_token")), "req_token")
        self.assertEqual(asyncio.run(ctx.get_state("oauth_token_secret")), "req_secret")
        self.assertEqual(asyncio.run(ctx.get_state("consumer_key")), "my_key")
        self.assertEqual(asyncio.run(ctx.get_state("consumer_secret")), "my_secret")

        # Step 4: Provide PIN
        with patch("usos.auth.tools.OAuth1Session") as mock_oauth_cls:
            mock_oauth = MagicMock()
            mock_oauth.fetch_access_token.return_value = {
                "oauth_token": "access_token",
                "oauth_token_secret": "access_secret"
            }
            mock_oauth_cls.return_value = mock_oauth

            res = asyncio.run(login(pin="123456", ctx=ctx))

        self.assertEqual(res["status"], "SUCCESS")

        # Session state should be cleaned up
        self.assertIsNone(asyncio.run(ctx.get_state("auth_step")))
        self.assertIsNone(asyncio.run(ctx.get_state("auth_base_url")))

        # Check credentials saved to FileTreeStore location
        self.assertTrue(self.config_file_path.exists())
        with open(self.config_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        value = data["value"]
        self.assertEqual(value["consumer_key"], "my_key")
        self.assertEqual(value["consumer_secret"], "my_secret")
        self.assertEqual(value["base_url"], "https://usos.uw.edu.pl")
        self.assertEqual(value["oauth_token"], "access_token")
        self.assertEqual(value["oauth_token_secret"], "access_secret")

    def test_clear_authentication_deletes_file(self):
        asyncio.run(save_auth_config(
            consumer_key="save_key",
            consumer_secret="save_secret",
            base_url="save_url",
            oauth_token="save_token",
            oauth_token_secret="save_token_secret"
        ))
        self.assertTrue(self.config_file_path.exists())

        ctx = MockContext()
        asyncio.run(ctx.set_state("auth_step", "AWAITING_PIN"))

        result = asyncio.run(logout(ctx=ctx))
        self.assertTrue(result["success"])
        self.assertFalse(self.config_file_path.exists())

        # Verify context state got cleared as well
        self.assertIsNone(asyncio.run(ctx.get_state("auth_step")))


if __name__ == "__main__":
    unittest.main()
