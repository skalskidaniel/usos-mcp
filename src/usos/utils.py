from __future__ import annotations

from datetime import date, datetime, timedelta
import time
from typing import Any

import requests
<<<<<<< HEAD
from requests import HTTPError
from requests.exceptions import ChunkedEncodingError, RequestException
=======
from requests import HTTPError, RequestException
from requests.exceptions import ChunkedEncodingError
>>>>>>> feat/issue-5-groups
from requests.exceptions import ConnectTimeout
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import ReadTimeout
from requests.exceptions import Timeout
from requests.exceptions import RequestException

from usos.auth.models import USOSAuthSettings
from usos.auth.utils import get_authenticated_session

RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _get_base_url() -> str:
    settings = USOSAuthSettings()
    if not settings.base_url:
        raise ValueError("USOS_API_BASE_URL is not configured.")
    return settings.base_url.rstrip("/")


def _parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def today_str() -> str:
    return date.today().isoformat()


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


def _get_with_retries(
    requester,
    url: str,
    params: dict[str, Any],
    *,
    timeout: int = 20,
    attempts: int = 3,
    base_sleep_s: float = 0.4,
):
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = requester(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code not in RETRIABLE_STATUS_CODES:
                raise
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(base_sleep_s * attempt)
        except (
            RequestsConnectionError,
            ReadTimeout,
            ConnectTimeout,
            Timeout,
            ChunkedEncodingError,
        ) as exc:
            last_error = exc
            if attempt == attempts:
                break
            time.sleep(base_sleep_s * attempt)
    if last_error is not None:
        raise last_error
    raise RuntimeError("Request failed without a captured error.")


def fetch_active_terms() -> list[dict[str, Any]]:
    base_url = _get_base_url()
    response = _get_with_retries(
        requests.get,
        f"{base_url}/services/terms/terms_index",
        params={"active_only": "true", "format": "json"},
        timeout=20,
        attempts=4,
    )
    data = response.json()
    if isinstance(data, list):
        return data
    return []


def fetch_term(term_id: str) -> dict[str, Any]:
    if not term_id:
        raise ValueError("term_id is required.")
    base_url = _get_base_url()
    response = _get_with_retries(
        requests.get,
        f"{base_url}/services/terms/term",
        params={"term_id": term_id, "format": "json"},
        timeout=20,
        attempts=4,
    )
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

    today = date.today()
    matching_terms = []
    for term in active_terms:
        t_id = term.get("id")
        start_str = term.get("start_date")
        finish_str = term.get("finish_date") or term.get("end_date")
        if (
            isinstance(t_id, str)
            and t_id
            and isinstance(start_str, str)
            and isinstance(finish_str, str)
        ):
            try:
                start_d = _parse_date(start_str)
                finish_d = _parse_date(finish_str)
                if start_d <= today <= finish_d:
                    duration = (finish_d - start_d).days
                    matching_terms.append((duration, t_id))
            except ValueError:
                continue

    if matching_terms:
        matching_terms.sort()
        return matching_terms[0][1]

    for term in active_terms:
        resolved = term.get("id")
        if isinstance(resolved, str) and resolved:
            return resolved

    raise ValueError("Active term data does not include a valid term id.")


def extract_localized_str(
    value: str | dict | None,
    prefer: str = "en",
) -> str | None:
    """Extract a single string from a USOS localized field (str, dict, or None)."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get(prefer) or value.get("pl") or next(iter(value.values()), None)
    return None


<<<<<<< HEAD
def _parse_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().upper() in ("T", "TRUE", "Y", "YES", "1")
    if isinstance(val, (int, float)):
        return bool(val)
    return False


class MultipleFacultiesError(Exception):
    def __init__(self, faculties: list[dict[str, Any]]) -> None:
=======
class MultipleFacultiesError(Exception):
    def __init__(self, faculties: list[dict]) -> None:
>>>>>>> feat/issue-5-groups
        self.faculties = faculties
        super().__init__("Multiple faculties found. Pass faculty_id explicitly.")


def fetch_user_faculties() -> list[dict[str, Any]]:
    """Return faculties associated with the authenticated user.

    Resolution strategy:
    1. Student programmes (preferred for student users).
    2. Employment functions (fallback for staff users or limited scopes).
    """
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


<<<<<<< HEAD
def fetch_user_profile(user_id: str | None = None, fields: str = "id") -> dict[str, Any]:
    base_url = _get_base_url()
    session = get_authenticated_session()
    params = {"fields": fields, "format": "json"}
    if user_id:
        params["user_id"] = user_id
=======
def _parse_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().upper() in ("T", "TRUE", "Y", "YES", "1")
    if isinstance(val, (int, float)):
        return bool(val)
    return False


def fetch_user_profile(user_id: str | None = None, fields: str = "id") -> dict[str, Any]:
    """Fetch user profile information from USOS API.

    If user_id is None, fetches the profile of the currently authenticated user.
    """
    base_url = _get_base_url()
    session = get_authenticated_session()

    params = {"fields": fields, "format": "json"}
    if user_id:
        params["user_id"] = user_id

>>>>>>> feat/issue-5-groups
    response = _get_with_retries(
        session.get,
        f"{base_url}/services/users/user",
        params=params,
        timeout=20,
        attempts=4,
    )
    data = response.json()
    if isinstance(data, dict):
        return data
    return {}

<<<<<<< HEAD

def fetch_classtypes_index() -> dict[str, Any]:
    base_url = _get_base_url()
    response = _get_with_retries(
        requests.get,
        f"{base_url}/services/courses/classtypes_index",
        params={"format": "json"},
        timeout=20,
        attempts=4,
    )
    data = response.json()
    if isinstance(data, dict):
        return data
    return {}
=======
>>>>>>> feat/issue-5-groups
