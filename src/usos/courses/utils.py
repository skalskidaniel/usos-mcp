from typing import Any
from usos.auth.utils import get_authenticated_session
from usos.utils import (
    _get_base_url,
    _get_with_retries,
    extract_localized_str,
    fetch_classtypes_index,
)

COURSE_FIELDS = "id|name|ects_credits_simplified|assessment_criteria|description|bibliography"
EDITION_FIELDS = "course_id|course_name|term_id|description|bibliography|passing_status|course_units[id|classtype_id|topics|learning_outcomes|assessment_criteria|teaching_methods]"
EXAM_FIELDS = "id|examination_session_id|term[id]|course[id|name]|groups[exam_start|exam_end|capacity|number]"


def fetch_course_basic_info(course_id: str, term_id: str | None = None) -> dict[str, Any]:
    """Fetch ECTS, assessment criteria, and passing status of a course."""
    base_url = _get_base_url()
    session = get_authenticated_session()

    if term_id:
        try:
            response = _get_with_retries(
                session.get,
                f"{base_url}/services/courses/course_edition2",
                params={
                    "course_id": course_id,
                    "term_id": term_id,
                    "fields": f"passing_status|course[{COURSE_FIELDS}]",
                    "format": "json",
                },
                timeout=20,
                attempts=3,
            )
            data = response.json()
            if isinstance(data, dict) and data.get("course"):
                course_data = data.get("course") or {}
                return {
                    "course_id": course_id,
                    "name": extract_localized_str(course_data.get("name")),
                    "ects_credits": course_data.get("ects_credits_simplified"),
                    "assessment_criteria": extract_localized_str(course_data.get("assessment_criteria")),
                    "passing_status": data.get("passing_status"),
                }
        except Exception:
            pass

    response = _get_with_retries(
        session.get,
        f"{base_url}/services/courses/course2",
        params={
            "course_ids": course_id,
            "fields": COURSE_FIELDS,
            "format": "json",
        },
        timeout=20,
        attempts=3,
    )
    payload = response.json()
    course_data = payload.get(course_id) if isinstance(payload, dict) else {}
    if not course_data:
        raise ValueError(f"Course '{course_id}' not found.")

    return {
        "course_id": course_id,
        "name": extract_localized_str(course_data.get("name")),
        "ects_credits": course_data.get("ects_credits_simplified"),
        "assessment_criteria": extract_localized_str(course_data.get("assessment_criteria")),
        "passing_status": None,
    }


def fetch_syllabus_details(course_id: str, term_id: str) -> dict[str, Any]:
    """Fetch description, bibliography, prerequisites, and units."""
    base_url = _get_base_url()
    session = get_authenticated_session()

    response = _get_with_retries(
        session.get,
        f"{base_url}/services/courses/course_edition2",
        params={
            "course_id": course_id,
            "term_id": term_id,
            "fields": EDITION_FIELDS,
            "format": "json",
        },
        timeout=20,
        attempts=3,
    )
    data = response.json()
    if not data or not isinstance(data, dict) or "course_name" not in data:
        raise ValueError(f"Course edition '{course_id}' in term '{term_id}' not found.")

    course_units = data.get("course_units") or []
    return {
        "course_id": course_id,
        "name": extract_localized_str(data.get("course_name")),
        "term_id": term_id,
        "description": extract_localized_str(data.get("description")),
        "bibliography": extract_localized_str(data.get("bibliography")),
        "prerequisites": None,
        "course_units": course_units,
    }


def fetch_student_exams() -> list[dict[str, Any]]:
    """Retrieve exams for the authenticated student."""
    base_url = _get_base_url()
    session = get_authenticated_session()

    response = _get_with_retries(
        session.get,
        f"{base_url}/services/exams/student_exams",
        params={"fields": EXAM_FIELDS, "format": "json"},
        timeout=20,
        attempts=4,
    )
    data = response.json()
    if isinstance(data, list):
        return data
    return []


def resolve_classtypes() -> dict[str, str]:
    """Fetch the dictionary mapping course class type IDs to their localized names."""
    raw_types = fetch_classtypes_index()
    resolved = {}
    for ct_id, val in raw_types.items():
        resolved[ct_id] = extract_localized_str(val.get("name")) or ct_id
    return resolved
