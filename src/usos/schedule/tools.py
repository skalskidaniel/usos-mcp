import asyncio

from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.tools import tool
from fastmcp.exceptions import ToolError
from usos.utils import (
    get_semester_date_range,
    resolve_term_id,
    today_str
)


from .models import CalendarEvent
from .utils import (
    fetch_calendar_events,
    fetch_user_faculties,
    fetch_student_schedule,
    resolve_faculty_id,
    flatten_calendar_event,
)


@tool(
    name="get_schedule",
    description="Fetch the authenticated student's timetable for a selected date window (1-7 days).",
    tags={"schedule"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "destructiveHint": False,
        "idempotentHint": False
    },
    timeout=30
)
async def get_schedule(
    start_date: str | None = None,
    days: int = 7,
    ctx: Context = CurrentContext(),
) -> dict:
    try:
        resolved_start = start_date or today_str()
        await ctx.info("Fetching student schedule.")
        activities = await asyncio.to_thread(
            fetch_student_schedule,
            start=resolved_start,
            days=days,
        )
        return {
            "start_date": resolved_start,
            "days": days,
            "count": len(activities),
            "activities": activities,
        }
    except Exception as exc:
        await ctx.error(f"Failed to fetch schedule: {exc}")
        raise ToolError(f"Failed to fetch schedule: {exc}") from exc


@tool(
    name="get_faculties",
    description=(
        "List faculties linked to the authenticated student's active programmes. "
        "Use ONLY when faculty_id is unknown and you want to use schedule tools."
    ),
    tags={"schedule"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    },
    timeout=15
)
async def get_faculties(ctx: Context = CurrentContext()) -> dict:
    try:
        await ctx.info("Fetching user faculties.")
        faculties = await asyncio.to_thread(fetch_user_faculties)
        return {"count": len(faculties), "faculties": faculties}
    except Exception as exc:
        await ctx.error(f"Failed to fetch faculties: {exc}")
        raise ToolError(f"Failed to fetch faculties: {exc}") from exc


@tool(
    name="get_days_off",
    description=(
        "Find day-off calendar events in a date range. faculty_id is optional and "
        "auto-resolved from the student's profile when omitted. "
        "Use get_my_faculties if resolution fails."
    ),
    tags={"schedule"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": False,
        "destructiveHint": False
    },
    timeout=30
)
async def get_days_off(
    start_date: str,
    end_date: str,
    faculty_id: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    try:
        await ctx.info("Resolving faculty and fetching day-off events.")
        resolved_faculty_id = await asyncio.to_thread(
            resolve_faculty_id,
            faculty_id,
        )
        events = await asyncio.to_thread(
            fetch_calendar_events,
            faculty_id=resolved_faculty_id,
            start_date=start_date,
            end_date=end_date,
        )
        days_off = [
            event for event in events if bool(event.get("is_day_off"))
        ]
        days_off.sort(key=lambda item: str(item.get("start_date", "")))
        
        flat_days_off = [flatten_calendar_event(e) for e in days_off]
        return {
            "faculty_id": resolved_faculty_id,
            "days_off": [CalendarEvent(**e) for e in flat_days_off],
        }
    except Exception as exc:
        await ctx.error(f"Failed to fetch day-off events: {exc}")
        raise ToolError(f"Failed to fetch day-off events: {exc}") from exc


@tool(
    name="get_exam_session_dates",
    description=(
        "Find exam session calendar events in a selected term. faculty_id is optional and "
        "auto-resolved from the student's profile when omitted. "
        "Use get_my_faculties if resolution fails."
    ),
    tags={"schedule"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "destructiveHint": False,
        "idempotentHint": False
    },
    timeout=30
)
async def get_exam_session_dates(
    term_id: str | None = None,
    faculty_id: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    try:
        await ctx.info("Resolving term and faculty for exam sessions.")
        resolved_faculty_id = await asyncio.to_thread(
            resolve_faculty_id,
            faculty_id,
        )
        resolved_term_id = await asyncio.to_thread(
            resolve_term_id,
            term_id,
        )
        start_date, end_date = await asyncio.to_thread(
            get_semester_date_range,
            resolved_term_id,
        )
        events = await asyncio.to_thread(
            fetch_calendar_events,
            faculty_id=resolved_faculty_id,
            start_date=start_date,
            end_date=end_date,
        )
        exam_sessions = [
            event for event in events if str(event.get("type", "")).lower() == "exam_session"
        ]
        exam_sessions = list({
            (event.get("id"), str(event.get("start_date", ""))): event
            for event in exam_sessions
        }.values())
        exam_sessions.sort(key=lambda item: str(item.get("start_date", "")))
        
        flat_exams = [flatten_calendar_event(e) for e in exam_sessions]
        return {
            "faculty_id": resolved_faculty_id,
            "term_id": resolved_term_id,
            "exam_sessions": [CalendarEvent(**e) for e in flat_exams],
        }
    except Exception as exc:
        await ctx.error(f"Failed to fetch exam session dates: {exc}")
        raise ToolError(f"Failed to fetch exam session dates: {exc}") from exc
