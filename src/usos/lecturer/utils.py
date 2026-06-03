from typing import Any
from usos.auth.utils import get_authenticated_session
from usos.utils import _get_base_url, _get_with_retries

LECTURER_FIELDS = "id|first_name|last_name|titles|email"
TT_DEFAULT_FIELDS = (
    "type|start_time|end_time|name|url|course_id|course_name|classtype_name|"
    "building_name|room_number|room_id|lecturer_ids|group_number|frequency"
)

def fetch_course_lecturers(course_id: str, term_id: str) -> dict[str, Any]:
    """Fetch lecturers for a given course edition via services/courses/course_edition."""
    base_url = _get_base_url()
    session = get_authenticated_session()
    
    response = _get_with_retries(
        session.get,
        f"{base_url}/services/courses/course_edition",
        params={
            "course_id": course_id,
            "term_id": term_id,
            "fields": "course_name|lecturers",
            "format": "json",
        },
        timeout=20,
        attempts=4,
    )
    return response.json()

def search_users(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search for users using services/users/search2."""
    base_url = _get_base_url()
    session = get_authenticated_session()
    
    response = _get_with_retries(
        session.get,
        f"{base_url}/services/users/search2",
        params={
            "query": query,
            "lang": "pl",
            "num": min(limit, 20),
            "format": "json",
        },
        timeout=20,
        attempts=4,
    )
    data = response.json()
    return data.get("items", []) if isinstance(data, dict) else []

def fetch_lecturer_courses(lecturer_id: str | None) -> list[dict[str, Any]]:
    """Retrieve courses taught by a given lecturer via services/groups/lecturer."""
    base_url = _get_base_url()
    session = get_authenticated_session()
    
    params = {
        "fields": "course_id|course_name|term_id|group_number|class_type_id",
        "format": "json",
    }
    if lecturer_id:
        params["user_id"] = lecturer_id
        
    response = _get_with_retries(
        session.get,
        f"{base_url}/services/groups/lecturer",
        params=params,
        timeout=20,
        attempts=4,
    )
    
    data = response.json()
    if isinstance(data, dict) and "groups" in data:
        data = data["groups"]

    groups = []
    if isinstance(data, dict):
        for term_id, term_groups in data.items():
            if isinstance(term_groups, list):
                for tg in term_groups:
                    tg["term_id"] = tg.get("term_id") or term_id
                    groups.append(tg)
    elif isinstance(data, list):
        groups = data
    return groups

def fetch_lecturer_schedule(lecturer_id: str, start: str, days: int = 1) -> list[dict[str, Any]]:
    """Fetch timetable for a lecturer via services/tt/staff."""
    if days < 1 or days > 7:
        raise ValueError("days must be between 1 and 7 for services/tt/staff.")
        
    base_url = _get_base_url()
    session = get_authenticated_session()
    
    response = _get_with_retries(
        session.get,
        f"{base_url}/services/tt/staff",
        params={
            "user_id": lecturer_id,
            "start": start,
            "days": days,
            "fields": TT_DEFAULT_FIELDS,
            "format": "json",
        },
        timeout=20,
        attempts=4,
    )
    data = response.json()
    return data if isinstance(data, list) else []
