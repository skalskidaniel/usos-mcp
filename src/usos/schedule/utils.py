from __future__ import annotations

from typing import Any

import requests
from requests import HTTPError
from requests.exceptions import RequestException

from usos.auth.utils import get_authenticated_session
from usos.utils import (
    _get_base_url,
    _get_with_retries,
    date_range_to_windows,
    extract_localized_str,
    MultipleFacultiesError,
    fetch_user_faculties,
    resolve_faculty_id,
)


TT_DEFAULT_FIELDS = (
    "type|start_time|end_time|name|url|course_id|course_name|classtype_name|"
    "building_name|room_number|room_id|lecturer_ids|group_number|frequency"
)
CALENDAR_DEFAULT_FIELDS = "id|name|start_date|end_date|type|is_day_off"
FACULTY_DEFAULT_FIELDS = "id|name"


def fetch_student_schedule(start: str, days: int) -> list[dict[str, Any]]:
    if days < 1 or days > 7:
        raise ValueError("days must be between 1 and 7 for services/tt/student.")

    base_url = _get_base_url()
    session = get_authenticated_session()
    response = _get_with_retries(
        session.get,
        f"{base_url}/services/tt/student",
        params={
            "start": start,
            "days": days,
            "fields": TT_DEFAULT_FIELDS,
            "format": "json",
        },
        timeout=20,
        attempts=4,
    )
    data = response.json()
    if isinstance(data, list):
        return data
    return []


def fetch_faculty_search(
    query: str,
    lang: str = "pl",
    limit: int = 20,
) -> list[dict[str, Any]]:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query must not be empty.")

    safe_limit = max(1, min(limit, 20))
    base_url = _get_base_url()
    params = {
        "lang": lang,
        "query": normalized_query,
        "fields": FACULTY_DEFAULT_FIELDS,
        "num": safe_limit,
        "start": 0,
        "format": "json",
    }

    response = _get_with_retries(
        requests.get,
        f"{base_url}/services/fac/search",
        params=params,
        timeout=20,
        attempts=4,
    )
    payload = response.json()
    items = payload.get("items", []) if isinstance(payload, dict) else []
    if isinstance(items, list):
        return items
    return []



def fetch_calendar_events(
    faculty_id: str,
    start_date: str,
    end_date: str,
) -> list[dict[str, Any]]:
    if not faculty_id:
        raise ValueError("faculty_id is required.")

    base_url = _get_base_url()
    session = get_authenticated_session()

    events: list[dict[str, Any]] = []
    for window_start, window_end in date_range_to_windows(
        start_date=start_date,
        end_date=end_date,
        window_days=30,
    ):
        response = _get_with_retries(
            session.get,
            f"{base_url}/services/calendar/search",
            params={
                "faculty_id": faculty_id,
                "start_date": window_start,
                "end_date": window_end,
                "fields": CALENDAR_DEFAULT_FIELDS,
                "format": "json",
            },
            timeout=20,
            attempts=4,
        )
        payload = response.json()
        if isinstance(payload, list):
            events.extend(payload)

    return events


def flatten_calendar_event(event: dict[str, Any]) -> dict[str, Any]:
    name_str = extract_localized_str(event.get("name"))

    start_date = event.get("start_date")
    if isinstance(start_date, str) and " " in start_date:
        start_date = start_date.split(" ")[0]
    end_date = event.get("end_date")
    if isinstance(end_date, str) and " " in end_date:
        end_date = end_date.split(" ")[0]

    return {
        "id": event.get("id"),
        "name": name_str,
        "start_date": start_date,
        "end_date": end_date,
        "type": event.get("type"),
        "is_day_off": bool(event.get("is_day_off")),
    }
