import asyncio
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.tools import tool
from fastmcp.exceptions import ToolError
from usos.utils import (
    fetch_user_profile,
    resolve_term_id,
    extract_localized_str,
)

from .models import Lecturer, LecturerGroup
from .utils import (
    fetch_course_lecturers,
    search_users,
    fetch_lecturer_courses,
    LECTURER_FIELDS,
)


@tool(
    name="get_course_lecturers",
    description="Check who teaches a given course in a specific term (list of lecturers).",
    tags={"lecturer"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    timeout=30,
)
async def get_course_lecturers(
    course_id: str,
    term_id: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """
    Args:
        course_id: The ID of the course.
        term_id: Optional ID of the academic term. Auto-resolved to current if omitted.
    """
    try:
        from usos.utils import resolve_course_and_term
        course_id, term_id = await asyncio.to_thread(resolve_course_and_term, course_id, term_id)
        await ctx.info(f"Fetching lecturers for course: {course_id}")
        resolved_term = await asyncio.to_thread(resolve_term_id, term_id)
        data = await asyncio.to_thread(fetch_course_lecturers, course_id, resolved_term)
        lecturers = [Lecturer(**lecturer) for lecturer in data.get("lecturers", [])]
        return {
            "course_id": course_id,
            "course_name": extract_localized_str(data.get("course_name")),
            "term_id": resolved_term,
            "lecturers": lecturers,
        }
    except Exception as exc:
        await ctx.error(f"Failed to fetch course lecturers: {exc}")
        raise ToolError(f"Failed to fetch course lecturers: {exc}") from exc


@tool(
    name="search_lecturer",
    description="Search for employees/lecturers and retrieve their academic titles and emails.",
    tags={"lecturer"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    timeout=30,
)
async def search_lecturer(
    query: str,
    limit: int = 10,
    ctx: Context = CurrentContext(),
) -> dict:
    """
    Args:
        query: The search string (e.g., part of a name or surname) to find employees/lecturers.
        limit: Maximum number of results to return (default is 10).
    """
    try:
        await ctx.info(f"Searching for users matching: {query}")
        items = await asyncio.to_thread(search_users, query, limit)
        user_ids = [
            item.get("user", {}).get("id") or item.get("user_id") or item.get("id")
            for item in items
            if (item.get("user", {}).get("id") or item.get("user_id") or item.get("id"))
        ]

        async def fetch_one(uid):
            return await asyncio.to_thread(fetch_user_profile, uid, LECTURER_FIELDS)

        details_list = await asyncio.gather(
            *(fetch_one(uid) for uid in user_ids), return_exceptions=True
        )

        lecturers = []
        for det in details_list:
            if (
                isinstance(det, Exception)
                or not det
                or not isinstance(det, dict)
                or "id" not in det
            ):
                continue
            lecturers.append(Lecturer(**det))

        return {
            "query": query,
            "results": lecturers,
        }
    except Exception as exc:
        await ctx.error(f"Failed to search for lecturers: {exc}")
        raise ToolError(f"Failed to search for lecturers: {exc}") from exc


@tool(
    name="get_lecturer_courses",
    description="Find what courses a given employee teaches.",
    tags={"lecturer"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    timeout=30,
)
async def get_lecturer_courses(
    lecturer_id: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """
    Args:
        lecturer_id: The ID of the lecturer. If omitted, uses the currently authenticated user's ID.
    """
    try:
        await ctx.info(f"Fetching courses for lecturer ID: {lecturer_id or 'self'}")
        raw_groups = await asyncio.to_thread(fetch_lecturer_courses, lecturer_id)

        seen = set()
        courses = []
        for g in raw_groups:
            course_id = g.get("course_id")
            class_type_id = g.get("class_type_id")
            key = (course_id, class_type_id)
            if key not in seen:
                seen.add(key)
                raw_name = g.get("course_name")
                course_name = extract_localized_str(raw_name) if isinstance(raw_name, dict) else raw_name

                course_unit_id = g.get("course_unit_id")
                try:
                    if course_unit_id is not None:
                        course_unit_id = int(course_unit_id)
                except (ValueError, TypeError):
                    course_unit_id = None

                mapped = LecturerGroup(
                    course_id=course_id,
                    course_unit_id=course_unit_id,
                    course_name=course_name,
                    class_type_id=class_type_id,
                )
                courses.append(mapped)

        return {
            "lecturer_id": lecturer_id or "self",
            "courses_count": len(courses),
            "courses": courses,
        }
    except Exception as exc:
        await ctx.error(f"Failed to fetch lecturer courses: {exc}")
        raise ToolError(f"Failed to fetch lecturer courses: {exc}") from exc



