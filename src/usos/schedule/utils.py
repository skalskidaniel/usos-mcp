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
)
from .models import MultipleFacultiesError


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



def fetch_user_faculties() -> list[dict[str, Any]]:
    """Return faculties associated with the authenticated user.

    Resolution strategy:
    1. Student programmes (preferred for student users).
    2. Employment functions (fallback for staff users or limited scopes).
    """
    # TODO test this function
    base_url = _get_base_url()
    session = get_authenticated_session()
    faculties_by_id: dict[str, dict[str, Any]] = {}

    def _collect_programme_ids(programmes: Any) -> set[str]:
        programme_ids: set[str] = set()
        if not isinstance(programmes, list):
            return programme_ids
        for programme_entry in programmes:
            if not isinstance(programme_entry, dict):
                continue
            programme = programme_entry.get("programme")
            if not isinstance(programme, dict):
                continue
            programme_id = programme.get("id")
            if isinstance(programme_id, str) and programme_id:
                programme_ids.add(programme_id)
        return programme_ids

    def _resolve_programme_faculty(programme_id: str) -> None:
        try:
            response = _get_with_retries(
                session.get,
                f"{base_url}/services/progs/programme",
                params={
                    "programme_id": programme_id,
                    "fields": "id|description|faculty[id|name]",
                    "format": "json",
                },
                timeout=20,
                attempts=4,
            )
        except (HTTPError, RequestException):
            return

        payload = response.json()
        if not isinstance(payload, dict):
            return

        faculty = payload.get("faculty")
        if not isinstance(faculty, dict):
            return
        faculty_id = faculty.get("id")
        if not isinstance(faculty_id, str) or not faculty_id:
            return
        if faculty_id in faculties_by_id:
            return

        faculties_by_id[faculty_id] = {
            "id": faculty_id,
            "name": faculty.get("name"),
        }

    try:
        response = _get_with_retries(
            session.get,
            f"{base_url}/services/users/user",
            params={"fields": "student_programmes", "format": "json"},
            timeout=20,
            attempts=4,
        )
        payload = response.json()
        if isinstance(payload, dict):
            for programme_id in sorted(
                _collect_programme_ids(payload.get("student_programmes", []))
            ):
                _resolve_programme_faculty(programme_id)
    except (HTTPError, RequestException):
        pass

    return list(faculties_by_id.values())


def resolve_faculty_id(faculty_id: str | None) -> str:
    if faculty_id and faculty_id.strip():
        return faculty_id.strip()

    faculties = fetch_user_faculties()
    if len(faculties) == 1:
        resolved = faculties[0].get("id")
        if isinstance(resolved, str) and resolved:
            return resolved

    if len(faculties) > 1:
        raise MultipleFacultiesError(faculties)

    raise ValueError(
        "Could not auto-resolve faculty_id from student programmes or employment functions. "
        "Use get_faculties and pass faculty_id explicitly."
    )


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
    name = event.get("name")
    name_str = None
    if name:
        if isinstance(name, str):
            name_str = name
        elif isinstance(name, dict):
            name_str = (
                name.get("en")
                or name.get("pl")
                or next(iter(name.values()), None)
            )

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





