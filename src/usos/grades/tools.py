import asyncio

from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.tools import tool
from fastmcp.exceptions import ToolError
from usos.utils import resolve_term_id, fetch_active_terms
from .utils import (
    fetch_grades_by_terms,
    fetch_course_edition_grades,
    fetch_latest_grades,
    fetch_user_ects_points,
    compute_weighted_average,
    flatten_term_grades,
    flatten_course_edition_grades,
    flatten_latest_grades,
)
from .models import GradeAverage, GradeEntry


@tool(
    name="get_grades",
    description=(
        "Fetch the authenticated student's grades. "
        "Supports four modes: "
        "'term' — grades for a given academic term; "
        "'course' — grades for a specific course edition (requires course_id); "
        "'latest' — recently modified grades (last N days); "
        "'all' (default) — grades from all academic terms overall."
    ),
    tags={"grades"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    timeout=30,
)
async def get_grades(
    mode: str = "all",
    term_id: str | None = None,
    course_id: str | None = None,
    days: int | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    try:
        mode = mode.lower().strip()
        if mode == "term":
            await ctx.info("Fetching grades for term.")
            resolved_term = await asyncio.to_thread(resolve_term_id, term_id)
            grades = await asyncio.to_thread(fetch_grades_by_terms, [resolved_term])
            flat_grades = flatten_term_grades(grades)
            return {
                "mode": mode,
                "term_id": resolved_term,
                "grades": [GradeEntry(**g) for g in flat_grades],
            }
        elif mode == "course":
            if not course_id:
                raise ValueError("course_id is required in 'course' mode.")
            await ctx.info("Fetching grades for course edition.")
            resolved_term = await asyncio.to_thread(resolve_term_id, term_id)
            grades = await asyncio.to_thread(
                fetch_course_edition_grades,
                course_id,
                resolved_term,
            )
            flat_grades = flatten_course_edition_grades(
                grades, course_id, resolved_term
            )
            return {
                "mode": mode,
                "course_id": course_id,
                "term_id": resolved_term,
                "grades": [GradeEntry(**g) for g in flat_grades],
            }
        elif mode == "latest":
            if days is None:
                days = 7
            if days < 1:
                raise ValueError("days must be a positive integer.")
            if days > 107:
                raise ValueError("days must be not greater than 107")
            await ctx.info("Fetching latest grades.")
            grades = await asyncio.to_thread(fetch_latest_grades, days)
            flat_grades = flatten_latest_grades(grades)
            return {
                "mode": mode,
                "days": days,
                "grades": [GradeEntry(**g) for g in flat_grades],
            }
        elif mode == "all":
            await ctx.info("Fetching grades for all terms.")
            ects_data = await asyncio.to_thread(fetch_user_ects_points)
            active_terms = await asyncio.to_thread(fetch_active_terms)
            active_ids = [t["id"] for t in active_terms if "id" in t]
            resolved_terms = list(set(active_ids + list(ects_data.keys())))
            resolved_terms.sort()

            grades = await asyncio.to_thread(fetch_grades_by_terms, resolved_terms)
            flat_grades = flatten_term_grades(grades)
            return {
                "mode": mode,
                "term_ids": resolved_terms,
                "grades": [GradeEntry(**g) for g in flat_grades],
            }
        else:
            raise ValueError(
                f"Unsupported mode: '{mode}'. Supported modes are: 'term', 'course', 'latest', 'all'."
            )
    except Exception as exc:
        await ctx.error(f"Failed to fetch grades: {exc}")
        raise ToolError(f"Failed to fetch grades: {exc}") from exc


@tool(
    name="get_gpa",
    description=(
        "Calculate the authenticated student's ECTS-weighted grade point average. "
        "By default uses all academic terms from the student's study history. "
        "Pass term_ids to filter by specific terms."
    ),
    tags={"grades"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    timeout=30,
)
async def get_gpa(
    term_ids: list[str] | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    try:
        resolved_terms = term_ids
        if not resolved_terms:
            await ctx.info("Resolving academic terms for grade average.")
            ects_data = await asyncio.to_thread(fetch_user_ects_points)
            active_terms = await asyncio.to_thread(fetch_active_terms)
            active_ids = [t["id"] for t in active_terms if "id" in t]
            resolved_terms = list(set(active_ids + list(ects_data.keys())))
            resolved_terms.sort()
            if not resolved_terms:
                raise ValueError(
                    "No academic terms found to calculate average. Pass term_ids explicitly."
                )

        await ctx.info("Fetching grades and ECTS data for average.")
        grades_data = await asyncio.to_thread(fetch_grades_by_terms, resolved_terms)
        ects_data = await asyncio.to_thread(fetch_user_ects_points)

        avg, total_ects, counted, skipped = await asyncio.to_thread(
            compute_weighted_average,
            grades_data,
            ects_data,
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
        await ctx.error(f"Failed to calculate grade average: {exc}")
        raise ToolError(f"Failed to calculate grade average: {exc}") from exc
