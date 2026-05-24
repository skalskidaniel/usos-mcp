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
- get_oauth_request_token: Start OAuth 1.0a; return request token, secret, and authorize URL.
- get_oauth_access_token: Exchange request token and user PIN for persistent access credentials.
- check_authentication: Verify env credentials and probe the API with the current session.

Registered prompts:
- setup_usos_authentication: Step-by-step guide for first-time OAuth setup in the MCP client.

Registered resources:
- usos://universities/supported: List of USOS installations with `base_url` for university lookup.

OAuth endpoints are university-specific; token and authorize URLs are derived from `base_url`.
Consumer credentials can be passed to setup tools explicitly or loaded from the environment.
"""
