import asyncio
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.tools import tool
from fastmcp.exceptions import ToolError
from usos.utils import today_str, fetch_user_profile

from .models import Lecturer, LecturerGroup
from .utils import (
    fetch_course_lecturers,
    search_users,
    fetch_lecturer_courses,
    fetch_lecturer_schedule,
    LECTURER_FIELDS,
)

@tool(
    name="get_course_lecturers",
    description="Check who teaches a given course (list of lecturers).",
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
    ctx: Context = CurrentContext(),
) -> dict:
    try:
        await ctx.info(f"Fetching lecturers for course: {course_id}")
        data = await asyncio.to_thread(fetch_course_lecturers, course_id)
        lecturers = [Lecturer(**l) for l in data.get("lecturers", [])]
        return {
            "course_id": course_id,
            "course_name": data.get("name"),
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
    try:
        await ctx.info(f"Searching for users matching: {query}")
        items = await asyncio.to_thread(search_users, query, limit)
        user_ids = [item.get("user_id") or item.get("id") for item in items if (item.get("user_id") or item.get("id"))]
        
        # Parallel fetch of user details to optimize execution
        async def fetch_one(uid):
            return await asyncio.to_thread(fetch_user_profile, uid, LECTURER_FIELDS)
            
        details_list = await asyncio.gather(*(fetch_one(uid) for uid in user_ids), return_exceptions=True)
        
        lecturers = []
        for det in details_list:
            if isinstance(det, Exception) or not det or not isinstance(det, dict) or "id" not in det:
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
    try:
        await ctx.info(f"Fetching courses for lecturer ID: {lecturer_id or 'self'}")
        raw_groups = await asyncio.to_thread(fetch_lecturer_courses, lecturer_id)
        
        groups = []
        for g in raw_groups:
            group_num = g.get("number") or g.get("group_number")
            try:
                if group_num is not None:
                    group_num = int(group_num)
                    if group_num <= 0:
                        group_num = None
            except (ValueError, TypeError):
                group_num = None

            mapped = LecturerGroup(
                course_id=g.get("course_id"),
                course_name=g.get("course_name"),
                term_id=g.get("term_id"),
                group_number=group_num,
                class_type_id=g.get("class_type_id"),
            )
            groups.append(mapped)
            
        return {
            "lecturer_id": lecturer_id or "self",
            "courses_count": len(groups),
            "courses": groups,
        }
    except Exception as exc:
        await ctx.error(f"Failed to fetch lecturer courses: {exc}")
        raise ToolError(f"Failed to fetch lecturer courses: {exc}") from exc


@tool(
    name="get_lecturer_schedule",
    description="Fetch a specific lecturer's timetable for a given day (max 7 days).",
    tags={"lecturer"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    timeout=30,
)
async def get_lecturer_schedule(
    lecturer_id: str,
    start_date: str | None = None,
    days: int = 1,
    ctx: Context = CurrentContext(),
) -> dict:
    try:
        resolved_start = start_date or today_str()
        await ctx.info(f"Fetching timetable for lecturer {lecturer_id} starting from {resolved_start}")
        activities = await asyncio.to_thread(
            fetch_lecturer_schedule,
            lecturer_id=lecturer_id,
            start=resolved_start,
            days=days,
        )
        return {
            "lecturer_id": lecturer_id,
            "start_date": resolved_start,
            "days": days,
            "count": len(activities),
            "activities": activities,
        }
    except Exception as exc:
        await ctx.error(f"Failed to fetch lecturer schedule: {exc}")
        raise ToolError(f"Failed to fetch lecturer schedule: {exc}") from exc
