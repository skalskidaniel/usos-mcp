from typing import Any

from usos.auth.utils import get_authenticated_session
from usos.utils import _get_base_url, _get_with_retries

TERMS_GRADE_FIELDS = (
    "value_symbol|passes|value_description|exam_id|exam_session_number|"
    "counts_into_average|grade_type_id|date_modified|date_acquisition|comment"
)

LATEST_GRADE_FIELDS = (
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
            "fields": TERMS_GRADE_FIELDS,
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
            "fields": TERMS_GRADE_FIELDS,
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
            "fields": LATEST_GRADE_FIELDS,
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


def _parse_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().upper() in ("T", "TRUE", "Y", "YES", "1")
    if isinstance(val, (int, float)):
        return bool(val)
    return False


def _add_candidate(grouped: dict, key: str, g: dict):
    if not _parse_bool(g.get("counts_into_average")):
        return
    val_sym = g.get("value_symbol")
    if not val_sym:
        return
    try:
        grade_val = float(val_sym)
    except ValueError:
        return

    session_num = g.get("exam_session_number") or 1
    try:
        session_num = int(session_num)
    except ValueError:
        session_num = 1

    if key not in grouped:
        grouped[key] = []
    grouped[key].append((session_num, grade_val))


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

            grouped_candidates = {}

            course_grades = course_edition.get("course_grades")
            if course_grades:
                if isinstance(course_grades, list):
                    for g in course_grades:
                        if isinstance(g, dict):
                            _add_candidate(grouped_candidates, "course", g)
                elif isinstance(course_grades, dict):
                    for g in course_grades.values():
                        if isinstance(g, dict):
                            _add_candidate(grouped_candidates, "course", g)

            course_units_grades = course_edition.get("course_units_grades")
            if isinstance(course_units_grades, dict):
                for unit_id, unit_grades in course_units_grades.items():
                    if isinstance(unit_grades, list):
                        for sess_dict in unit_grades:
                            if isinstance(sess_dict, dict):
                                for g in sess_dict.values():
                                    if isinstance(g, dict):
                                        _add_candidate(grouped_candidates, unit_id, g)

            if not grouped_candidates:
                cg_len = len(course_grades) if isinstance(course_grades, (list, dict)) else 0
                cug_len = sum(len(x) for x in course_units_grades.values() if isinstance(x, list)) if isinstance(course_units_grades, dict) else 0
                grades_skipped += cg_len + cug_len
                continue

            resolved_grades = []
            for comp_key, candidates in grouped_candidates.items():
                if candidates:
                    candidates.sort(key=lambda x: x[0])
                    resolved_grades.append(candidates[-1][1])

            if not resolved_grades:
                continue

            if "course" in grouped_candidates and grouped_candidates["course"]:
                course_grade_value = grouped_candidates["course"][-1][1]
            else:
                course_grade_value = sum(resolved_grades) / len(resolved_grades)

            ects_str = term_ects.get(course_id)
            if ects_str is None:
                cg_len = len(course_grades) if isinstance(course_grades, (list, dict)) else 0
                cug_len = sum(len(x) for x in course_units_grades.values() if isinstance(x, list)) if isinstance(course_units_grades, dict) else 0
                grades_skipped += cg_len + cug_len
                continue

            try:
                ects_val = float(ects_str)
            except ValueError:
                cg_len = len(course_grades) if isinstance(course_grades, (list, dict)) else 0
                cug_len = sum(len(x) for x in course_units_grades.values() if isinstance(x, list)) if isinstance(course_units_grades, dict) else 0
                grades_skipped += cg_len + cug_len
                continue

            total_grade_points += course_grade_value * ects_val
            total_ects += ects_val
            grades_counted += len(resolved_grades)

            all_grades_count = 0
            if isinstance(course_grades, list):
                all_grades_count += len(course_grades)
            elif isinstance(course_grades, dict):
                all_grades_count += len(course_grades)
            if isinstance(course_units_grades, dict):
                for x in course_units_grades.values():
                    if isinstance(x, list):
                        for sd in x:
                            if isinstance(sd, dict):
                                all_grades_count += len([v for v in sd.values() if v is not None])

            grades_skipped += max(0, all_grades_count - len(resolved_grades))

    average = None
    if total_ects > 0:
        average = round(total_grade_points / total_ects, 2)

    return average, total_ects, grades_counted, grades_skipped
