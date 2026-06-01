from typing import Any

from usos.auth.utils import get_authenticated_session
from usos.utils import _get_base_url, _get_with_retries

GRADE_FIELDS = (
    "value_symbol|passes|value_description|exam_id|exam_session_number|"
    "counts_into_average|grade_type_id|date_modified|date_acquisition|comment|"
    "course_edition[course_id|course_name]"
)


def fetch_grades_by_terms(term_ids: list[str]) -> dict[str, Any]:
    if not term_ids:
        return {}
    base_url = _get_base_url()
    session = get_authenticated_session()

    term_ids_param = "|".join(term_ids)
    response = _get_with_retries(
        session.get,
        f"{base_url}/services/grades/terms2",
        params={
            "term_ids": term_ids_param,
            "fields": GRADE_FIELDS,
            "format": "json",
        },
        timeout=20,
        attempts=4,
    )

    data = response.json()
    if isinstance(data, dict):
        return data
    return {}


def fetch_course_edition_grades(course_id: str, term_id: str) -> dict[str, Any]:
    if not course_id or not term_id:
        raise ValueError("Both course_id and term_id are required.")

    base_url = _get_base_url()
    session = get_authenticated_session()

    response = _get_with_retries(
        session.get,
        f"{base_url}/services/grades/course_edition2",
        params={
            "course_id": course_id,
            "term_id": term_id,
            "fields": GRADE_FIELDS,
            "format": "json",
        },
        timeout=20,
        attempts=4,
    )

    data = response.json()
    if isinstance(data, dict):
        return data
    return {}


def fetch_latest_grades(days: int = 7) -> list[dict[str, Any]]:
    base_url = _get_base_url()
    session = get_authenticated_session()

    response = _get_with_retries(
        session.get,
        f"{base_url}/services/grades/latest",
        params={
            "days": days,
            "fields": GRADE_FIELDS,
            "format": "json",
        },
        timeout=20,
        attempts=4,
    )

    data = response.json()
    if isinstance(data, list):
        return data
    return []


def fetch_user_ects_points() -> dict[str, Any]:
    base_url = _get_base_url()
    session = get_authenticated_session()

    response = _get_with_retries(
        session.get,
        f"{base_url}/services/courses/user_ects_points",
        params={"format": "json"},
        timeout=20,
        attempts=4,
    )

    data = response.json()
    if isinstance(data, dict):
        return data
    return {}


def compute_weighted_average(
    grades_data: dict[str, Any],
    ects_data: dict[str, Any],
) -> tuple[float | None, float, int, int]:
    total_grade_points = 0.0
    total_ects = 0.0
    grades_counted = 0
    grades_skipped = 0

    for term_id, courses in grades_data.items():
        if not isinstance(courses, dict):
            continue
        term_ects = ects_data.get(term_id) or {}
        for course_id, course_edition in courses.items():
            if not isinstance(course_edition, dict):
                continue

            course_grades = course_edition.get("course_grades")
            if not isinstance(course_grades, dict) or not course_grades:
                continue

            candidate_grades = []
            for session_key, grade_entry in course_grades.items():
                if not isinstance(grade_entry, dict):
                    continue
                if not grade_entry.get("counts_into_average"):
                    continue

                val_sym = grade_entry.get("value_symbol")
                if not val_sym:
                    continue
                try:
                    grade_val = float(val_sym)
                except ValueError:
                    continue

                session_num = 1
                try:
                    session_num = int(session_key)
                except ValueError:
                    session_num = grade_entry.get("exam_session_number") or 1

                candidate_grades.append((session_num, grade_val))

            if not candidate_grades:
                grades_skipped += len(course_grades)
                continue

            candidate_grades.sort(key=lambda x: x[0])
            _, grade_val = candidate_grades[-1]

            ects_str = term_ects.get(course_id)
            if ects_str is None:
                grades_skipped += len(course_grades)
                continue

            try:
                ects_val = float(ects_str)
            except ValueError:
                grades_skipped += len(course_grades)
                continue

            total_grade_points += grade_val * ects_val
            total_ects += ects_val
            grades_counted += 1
            grades_skipped += len(course_grades) - 1

    average = None
    if total_ects > 0:
        average = total_grade_points / total_ects

    return average, total_ects, grades_counted, grades_skipped
