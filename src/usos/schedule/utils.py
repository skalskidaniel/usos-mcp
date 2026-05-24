from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import requests

from usos.auth.models import USOSAuthSettings
from usos.auth.utils import get_authenticated_session


TT_DEFAULT_FIELDS = (
    "type|start_time|end_time|name|url|course_id|course_name|classtype_name|"
    "building_name|room_number|room_id|lecturer_ids|group_number|frequency"
)
CALENDAR_DEFAULT_FIELDS = "id|name|start_date|end_date|type|is_day_off"


def _get_base_url() -> str:
    settings = USOSAuthSettings()
    if not settings.base_url:
        raise ValueError("USOS_API_BASE_URL is not configured.")
    return settings.base_url.rstrip("/")


def _parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def today_str() -> str:
    return date.today().isoformat()


def week_start_str() -> str:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return monday.isoformat()


def date_range_to_windows(
    start_date: str,
    end_date: str,
    window_days: int,
) -> list[tuple[str, str]]:
    if window_days <= 0:
        raise ValueError("window_days must be a positive integer.")

    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start > end:
        raise ValueError("start_date must not be after end_date.")

    windows: list[tuple[str, str]] = []
    current = start
    while current <= end:
        current_end = min(current + timedelta(days=window_days - 1), end)
        windows.append((current.isoformat(), current_end.isoformat()))
        current = current_end + timedelta(days=1)
    return windows


def _days_inclusive(start_date: str, end_date: str) -> int:
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    return (end - start).days + 1


def fetch_student_schedule(start: str, days: int) -> list[dict[str, Any]]:
    if days < 1 or days > 7:
        raise ValueError("days must be between 1 and 7 for services/tt/student.")

    base_url = _get_base_url()
    session = get_authenticated_session()
    response = session.get(
        f"{base_url}/services/tt/student",
        params={
            "start": start,
            "days": days,
            "fields": TT_DEFAULT_FIELDS,
            "format": "json",
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if isinstance(data, list):
        return data
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
        response = session.get(
            f"{base_url}/services/calendar/search",
            params={
                "faculty_id": faculty_id,
                "start_date": window_start,
                "end_date": window_end,
                "fields": CALENDAR_DEFAULT_FIELDS,
                "format": "json",
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            events.extend(payload)

    return events


def fetch_active_terms() -> list[dict[str, Any]]:
    base_url = _get_base_url()
    response = requests.get(
        f"{base_url}/services/terms/terms_index",
        params={"active_only": "true", "format": "json"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if isinstance(data, list):
        return data
    return []


def fetch_term(term_id: str) -> dict[str, Any]:
    if not term_id:
        raise ValueError("term_id is required.")
    base_url = _get_base_url()
    response = requests.get(
        f"{base_url}/services/terms/term",
        params={"term_id": term_id, "format": "json"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict):
        return data
    raise ValueError("Unexpected terms/term response format.")


def get_semester_date_range(term_id: str) -> tuple[str, str]:
    term = fetch_term(term_id)
    start_date = term.get("start_date")
    finish_date = term.get("finish_date")
    if not isinstance(start_date, str) or not isinstance(finish_date, str):
        raise ValueError("Term data does not contain valid start_date and finish_date.")
    return start_date, finish_date


def resolve_term_id(term_id: str | None) -> str:
    if term_id:
        return term_id
    active_terms = fetch_active_terms()
    if not active_terms:
        raise ValueError("No active terms found in this USOS installation.")
    first = active_terms[0]
    resolved = first.get("id")
    if not isinstance(resolved, str) or not resolved:
        raise ValueError("Active term data does not include a valid term id.")
    return resolved


def fetch_semester_schedule(term_id: str) -> list[dict[str, Any]]:
    start_date, end_date = get_semester_date_range(term_id)
    activities: list[dict[str, Any]] = []
    for window_start, window_end in date_range_to_windows(
        start_date=start_date,
        end_date=end_date,
        window_days=7,
    ):
        days = _days_inclusive(window_start, window_end)
        activities.extend(fetch_student_schedule(start=window_start, days=days))
    return activities


def sort_and_deduplicate_activities(
    activities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[tuple[Any, Any, Any, Any]] = set()
    unique: list[dict[str, Any]] = []

    for activity in sorted(
        activities,
        key=lambda item: (
            str(item.get("start_time", "")),
            str(item.get("end_time", "")),
            str(item.get("type", "")),
        ),
    ):
        key = (
            activity.get("type"),
            activity.get("start_time"),
            activity.get("end_time"),
            str(activity.get("name")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(activity)
    return unique
