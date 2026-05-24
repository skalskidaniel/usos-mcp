import ast

from usos.registry import registry

from .utils import (
    fetch_active_terms,
    fetch_calendar_events,
    fetch_faculty,
    fetch_faculty_search,
    fetch_user_faculties,
    fetch_semester_schedule,
    fetch_student_schedule,
    get_semester_date_range,
    resolve_faculty_id,
    resolve_term_id,
    sort_and_deduplicate_activities,
    today_str,
)


def _error_payload(exc: Exception) -> dict:
    message = str(exc)
    payload: dict = {"error": message}
    marker = "Available faculties: "
    if marker in message:
        raw = message.split(marker, 1)[1].strip()
        try:
            payload["faculties"] = ast.literal_eval(raw)
        except Exception:
            pass
    return payload


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
    name="get_my_semester_schedule",
    description="Fetch the authenticated student's full semester timetable by batching 7-day requests.",
)
def get_my_semester_schedule(term_id: str | None = None) -> dict:
    try:
        resolved_term_id = resolve_term_id(term_id)
        start_date, end_date = get_semester_date_range(resolved_term_id)
        raw_activities = fetch_semester_schedule(resolved_term_id)
        activities = sort_and_deduplicate_activities(raw_activities)
        return {
            "term_id": resolved_term_id,
            "start_date": start_date,
            "end_date": end_date,
            "count": len(activities),
            "activities": activities,
        }
    except Exception as exc:
        return _error_payload(exc)


@registry.tool(
    name="search_faculties",
    description=(
        "Search faculties by name/code and return candidate faculty IDs. "
        "Use this before calendar tools when faculty_id is unknown."
    ),
)
def search_faculties(query: str, lang: str = "pl", limit: int = 20) -> dict:
    try:
        faculties = fetch_faculty_search(query=query, lang=lang, limit=limit)
        return {
            "query": query,
            "lang": lang,
            "count": len(faculties),
            "faculties": faculties,
        }
    except Exception as exc:
        return _error_payload(exc)


@registry.tool(
    name="get_faculty",
    description="Get details for a single faculty by faculty_id.",
)
def get_faculty(faculty_id: str) -> dict:
    try:
        faculty = fetch_faculty(faculty_id)
        return {"faculty": faculty}
    except Exception as exc:
        return _error_payload(exc)


@registry.tool(
    name="get_my_faculties",
    description=(
        "List faculties linked to the authenticated student's active programmes. "
        "Use this to pick faculty_id for calendar tools."
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
        "Use search_faculties or get_my_faculties if resolution fails."
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
    name="get_semester_days_off",
    description=(
        "Find day-off calendar events for a full semester. faculty_id is optional and "
        "auto-resolved from the student's profile when omitted. "
        "Use search_faculties or get_my_faculties if resolution fails."
    ),
)
def get_semester_days_off(
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
            end_date=end_date,
        )
        days_off = [
            event for event in events if bool(event.get("is_day_off"))
        ]
        days_off.sort(key=lambda item: str(item.get("start_date", "")))
        return {
            "faculty_id": resolved_faculty_id,
            "resolved_faculty_id": resolved_faculty_id,
            "term_id": resolved_term_id,
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
        "Use search_faculties or get_my_faculties if resolution fails."
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
            end_date=end_date,
        )
        exam_sessions = [
            event for event in events if str(event.get("type", "")).lower() == "exam_session"
        ]
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


@registry.tool(
    name="get_active_terms",
    description="List active academic terms available in the current USOS installation.",
)
def get_active_terms() -> dict:
    try:
        terms = fetch_active_terms()
        return {"count": len(terms), "terms": terms}
    except Exception as exc:
        return _error_payload(exc)
