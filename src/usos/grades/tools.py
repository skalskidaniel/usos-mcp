from fastmcp.tools import tool
from usos.utils import _error_payload, resolve_term_id, fetch_active_terms
from .utils import (
    fetch_grades_by_terms,
    fetch_course_edition_grades,
    fetch_latest_grades,
    fetch_user_ects_points,
    compute_weighted_average,
)
from .models import GradeAverage


@tool(
    name="get_my_grades",
    description=(
        "Fetch the authenticated student's grades. "
        "Supports four modes: "
        "'term' — grades for a given academic term; "
        "'course' — grades for a specific course edition (requires course_id); "
        "'latest' — recently modified grades (last N days); "
        "'all' (default) — grades from all academic terms overall."
    ),
)
def get_my_grades(
    mode: str = "all",
    term_id: str | None = None,
    course_id: str | None = None,
    days: int | None = None,
) -> dict:
    try:
        mode = mode.lower().strip()
        if mode == "term":
            resolved_term = resolve_term_id(term_id)
            grades = fetch_grades_by_terms([resolved_term])
            return {
                "mode": mode,
                "term_id": resolved_term,
                "grades": grades,
            }
        elif mode == "course":
            if not course_id:
                raise ValueError("course_id is required in 'course' mode.")
            resolved_term = resolve_term_id(term_id)
            grades = fetch_course_edition_grades(course_id, resolved_term)
            return {
                "mode": mode,
                "course_id": course_id,
                "term_id": resolved_term,
                "grades": grades,
            }
        elif mode == "latest":
            if days is None:
                days = 7
            if days < 1:
                raise ValueError("days must be a positive integer.")
            if days > 107:
                raise ValueError("days must be not greater than 107")
            grades = fetch_latest_grades(days)
            return {
                "mode": mode,
                "days": days,
                "grades": grades,
            }
        elif mode == "all":
            ects_data = fetch_user_ects_points()
            active_terms = fetch_active_terms()
            active_ids = [t["id"] for t in active_terms if "id" in t]
            resolved_terms = list(set(active_ids + list(ects_data.keys())))
            resolved_terms.sort()
            
            grades = fetch_grades_by_terms(resolved_terms)
            return {
                "mode": mode,
                "term_ids": resolved_terms,
                "grades": grades,
            }
        else:
            raise ValueError(
                f"Unsupported mode: '{mode}'. Supported modes are: 'term', 'course', 'latest', 'all'."
            )
    except Exception as exc:
        return _error_payload(exc)


@tool(
    name="calculate_grade_average",
    description=(
        "Calculate the authenticated student's ECTS-weighted grade point average. "
        "By default uses all academic terms from the student's study history. "
        "Pass term_ids to filter by specific terms."
    ),
)
def calculate_grade_average(term_ids: list[str] | None = None) -> dict:
    try:
        resolved_terms = term_ids
        if not resolved_terms:
            ects_data = fetch_user_ects_points()
            active_terms = fetch_active_terms()
            active_ids = [t["id"] for t in active_terms if "id" in t]
            resolved_terms = list(set(active_ids + list(ects_data.keys())))
            resolved_terms.sort()
            if not resolved_terms:
                raise ValueError(
                    "No academic terms found to calculate average. Pass term_ids explicitly."
                )

        grades_data = fetch_grades_by_terms(resolved_terms)
        ects_data = fetch_user_ects_points()

        avg, total_ects, counted, skipped = compute_weighted_average(
            grades_data, ects_data
        )

        result = GradeAverage(
            average=avg,
            total_ects=total_ects,
            grades_counted=counted,
            grades_skipped=skipped,
            term_ids=resolved_terms,
        )
        return result.model_dump()
    except Exception as exc:
        return _error_payload(exc)
