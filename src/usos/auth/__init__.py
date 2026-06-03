"""
Authentication package for USOS API access via OAuth 1.0a.

This package provides MCP capabilities for onboarding users and verifying
that the server can call USOS on their behalf. Other domain packages (e.g.
`usos.schedule`) reuse `get_authenticated_session()` from `usos.auth.utils`
once credentials are configured.

USOS API modules used:
- services/oauth (request_token, authorize, access_token)
- services/users/user (authentication health check)

Registered tools:
- login: Interactive step-by-step authentication tool.
- check_login: Verify local credentials and probe the API with the current session.
- logout: Clear stored credentials from the local configuration store.

Registered prompts:
- authenticate_me: Interactive step-by-step guide for first-time OAuth setup in the MCP client.

Registered resources:
- usos://universities/supported: List of USOS installations with `base_url` for university lookup.

OAuth endpoints are university-specific; token and authorization URLs are derived from `base_url`.
Credentials can be passed to set up tools explicitly or loaded from the environment/local config storage.
"""
