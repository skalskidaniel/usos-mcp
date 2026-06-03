from typing import Any
from usos.auth.utils import get_authenticated_session
from usos.utils import _get_base_url, _get_with_retries

GROUP_FIELDS = "course_unit_id|group_number|class_type|class_type_id|course_id|course_name"


def fetch_user_groups(active_terms_only: bool = False) -> dict[str, Any]:
    """Fetch class groups for the authenticated user grouped by academic term."""
    base_url = _get_base_url()
    session = get_authenticated_session()

    response = _get_with_retries(
        session.get,
        f"{base_url}/services/groups/user",
        params={
            "fields": GROUP_FIELDS,
            "active_terms": "true" if active_terms_only else "false",
            "format": "json",
        },
        timeout=20,
        attempts=4,
    )
    data = response.json()
    return data if isinstance(data, dict) else {}


def fetch_group_participants(course_unit_id: int, group_number: int) -> list[dict[str, Any]]:
    """Fetch participant data for a specific group."""
    base_url = _get_base_url()
    session = get_authenticated_session()

    response = _get_with_retries(
        session.get,
        f"{base_url}/services/groups/group",
        params={
            "course_unit_id": str(course_unit_id),
            "group_number": str(group_number),
            "fields": "participants",
            "format": "json",
        },
        timeout=20,
        attempts=4,
    )
    data = response.json()
    if isinstance(data, dict):
        return data.get("participants") or []
    return []
