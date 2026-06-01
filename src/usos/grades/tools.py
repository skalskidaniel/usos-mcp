from usos.registry import registry
from usos.utils import _error_payload, resolve_term_id, fetch_active_terms
from .utils import (
    fetch_grades_by_terms,
    fetch_course_edition_grades,
    fetch_latest_grades,
    fetch_user_ects_points,
    compute_weighted_average,
)
from .models import GradeAverage


@registry.tool(
    name="get_my_grades",
    description=(
        "Fetch the authenticated student's grades. "
        "Supports three modes: "
        "'term' (default) — grades for a given academic term; "
        "'course' — grades for a specific course edition (requires course_id); "
        "'latest' — recently modified grades (last N days)."
    ),
)
def get_my_grades(
    mode: str = "term",
    term_id: str | None = None,
    course_id: str | None = None,
    days: int = 7,
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
            if days < 1:
                raise ValueError("days must be a positive integer.")
            grades = fetch_latest_grades(days)
            return {
                "mode": mode,
                "days": days,
                "grades": grades,
            }
        else:
            raise ValueError(
                f"Unsupported mode: '{mode}'. Supported modes are: 'term', 'course', 'latest'."
            )
    except Exception as exc:
        return _error_payload(exc)


@registry.tool(
    name="calculate_grade_average",
    description=(
        "Calculate the authenticated student's ECTS-weighted grade point average. "
        "By default uses all active terms. Pass term_ids to filter by specific terms."
    ),
)
def calculate_grade_average(term_ids: list[str] | None = None) -> dict:
    try:
        resolved_terms = term_ids
        if not resolved_terms:
            active_terms = fetch_active_terms()
            resolved_terms = [t["id"] for t in active_terms if "id" in t]
            if not resolved_terms:
                raise ValueError(
                    "No active terms found to calculate average. Pass term_ids explicitly."
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
