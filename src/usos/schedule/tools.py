from typing import Any
from usos.registry import registry
from usos.utils import _error_payload


from .utils import (
    fetch_calendar_events,
    fetch_faculty_search,
    fetch_user_faculties,
    fetch_student_schedule,
    get_semester_date_range,
    resolve_faculty_id,
    resolve_term_id,
    today_str,
)


@registry.tool(
    name="get_my_schedule",
    description="Fetch the authenticated student's timetable for a selected date window (1-7 days).",
)
def get_my_schedule(start_date: str | None = None, days: int = 7) -> dict:
    try:
        resolved_start = start_date or today_str()
        activities = fetch_student_schedule(start=resolved_start, days=days)
        return {
            "start_date": resolved_start,
            "days": days,
            "count": len(activities),
            "activities": activities,
        }
    except Exception as exc:
        return _error_payload(exc)


@registry.tool(
    name="get_my_faculties",
    description=(
        "List faculties linked to the authenticated student's active programmes. "
        "Use ONLY when faculty_id is unknown and you want to use schedule tools."
    ),
)
def get_my_faculties() -> dict:
    try:
        faculties = fetch_user_faculties()
        return {"count": len(faculties), "faculties": faculties}
    except Exception as exc:
        return _error_payload(exc)


@registry.tool(
    name="get_days_off",
    description=(
        "Find day-off calendar events in a date range. faculty_id is optional and "
        "auto-resolved from the student's profile when omitted. "
        "Use get_my_faculties if resolution fails."
    ),
)
def get_days_off(
    start_date: str,
    end_date: str,
    faculty_id: str | None = None,
) -> dict:
    try:
        resolved_faculty_id = resolve_faculty_id(faculty_id)
        events = fetch_calendar_events(
            faculty_id=resolved_faculty_id,
            start_date=start_date,
            end_date=end_date,
        )
        days_off = [
            event for event in events if bool(event.get("is_day_off"))
        ]
        days_off.sort(key=lambda item: str(item.get("start_date", "")))
        return {
            "faculty_id": resolved_faculty_id,
            "resolved_faculty_id": resolved_faculty_id,
            "start_date": start_date,
            "end_date": end_date,
            "count": len(days_off),
            "events": days_off,
        }
    except Exception as exc:
        return _error_payload(exc)


@registry.tool(
    name="get_exam_session_dates",
    description=(
        "Find exam session calendar events in a selected term. faculty_id is optional and "
        "auto-resolved from the student's profile when omitted. "
        "Use get_my_faculties if resolution fails."
    ),
)
def get_exam_session_dates(
    term_id: str | None = None,
    faculty_id: str | None = None,
) -> dict:
    try:
        resolved_faculty_id = resolve_faculty_id(faculty_id)
        resolved_term_id = resolve_term_id(term_id)
        start_date, end_date = get_semester_date_range(resolved_term_id)
        events = fetch_calendar_events(
            faculty_id=resolved_faculty_id,
            start_date=start_date,
            end_date=end_date
            )
        exam_sessions = [
            event for event in events if str(event.get("type", "")).lower() == "exam_session"
        ]
        exam_sessions = list({
            (event.get("id"), str(event.get("start_date", ""))): event
            for event in exam_sessions
        }.values())
        exam_sessions.sort(key=lambda item: str(item.get("start_date", "")))
        return {
            "faculty_id": resolved_faculty_id,
            "resolved_faculty_id": resolved_faculty_id,
            "term_id": resolved_term_id,
            "start_date": start_date,
            "end_date": end_date,
            "count": len(exam_sessions),
            "events": exam_sessions,
        }
    except Exception as exc:
        return _error_payload(exc)