from typing import Any
from usos.auth.utils import get_authenticated_session
from usos.utils import (
    _get_base_url,
    _get_with_retries,
    extract_localized_str,
    fetch_classtypes_index,
)

from concurrent.futures import ThreadPoolExecutor

COURSE_FIELDS = "id|name|ects_credits_simplified|assessment_criteria|description|bibliography"
EXAM_FIELDS = "id|examination_session_id|term|course[id|name]|groups[exam_start|exam_end|capacity|number]"


def fetch_course_basic_info(course_id: str, term_id: str | None = None) -> dict[str, Any]:
    """Fetch ECTS, assessment criteria, and passing status of a course."""
    base_url = _get_base_url()
    session = get_authenticated_session()

    passing_status = None
    if term_id:
        try:
            response = _get_with_retries(
                session.get,
                f"{base_url}/services/courses/course_edition",
                params={
                    "course_id": course_id,
                    "term_id": term_id,
                    "fields": "passing_status",
                    "format": "json",
                },
                timeout=20,
                attempts=3,
            )
            data = response.json()
            if isinstance(data, dict):
                passing_status = data.get("passing_status")
        except Exception:
            pass

    response = _get_with_retries(
        session.get,
        f"{base_url}/services/courses/course",
        params={
            "course_id": course_id,
            "fields": "id|name|ects_credits_simplified|assessment_criteria",
            "format": "json",
        },
        timeout=20,
        attempts=3,
    )
    course_data = response.json()
    if not course_data:
        raise ValueError(f"Course '{course_id}' not found.")

    ects_credits = course_data.get("ects_credits_simplified")
    if ects_credits is None:
        try:
            from usos.grades.utils import fetch_user_ects_points
            ects_points = fetch_user_ects_points()
            if course_id in ects_points:
                ects_credits = float(ects_points[course_id])
        except Exception:
            pass

    return {
        "course_id": course_id,
        "name": extract_localized_str(course_data.get("name")),
        "ects_credits": ects_credits,
        "assessment_criteria": extract_localized_str(course_data.get("assessment_criteria")),
        "passing_status": passing_status,
    }


def fetch_syllabus_details(course_id: str, term_id: str) -> dict[str, Any]:
    """Fetch description, bibliography, prerequisites, and units."""
    base_url = _get_base_url()
    session = get_authenticated_session()

    response = _get_with_retries(
        session.get,
        f"{base_url}/services/courses/course_edition",
        params={
            "course_id": course_id,
            "term_id": term_id,
            "fields": "course_name|description|bibliography|course_units_ids",
            "format": "json",
        },
        timeout=20,
        attempts=3,
    )
    data = response.json()
    if not data or not isinstance(data, dict) or "course_name" not in data:
        raise ValueError(f"Course edition '{course_id}' in term '{term_id}' not found.")

    unit_ids = data.get("course_units_ids") or []
    course_units = []

    if unit_ids:
        def fetch_unit(unit_id):
            resp = _get_with_retries(
                session.get,
                f"{base_url}/services/courses/unit",
                params={
                    "unit_id": unit_id,
                    "fields": "id|classtype_id|topics|learning_outcomes|assessment_criteria",
                    "format": "json",
                },
                timeout=20,
                attempts=3,
            )
            return resp.json()

        with ThreadPoolExecutor(max_workers=len(unit_ids)) as executor:
            course_units = list(executor.map(fetch_unit, unit_ids))

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
