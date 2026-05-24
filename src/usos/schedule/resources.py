from usos.registry import registry


@registry.resource(
    uri="usos://schedule/api-info",
    name="schedule-api-info",
    description="Schedule API capabilities and faculty_id discovery guidance.",
)
def schedule_api_info() -> str:
    return "\n".join(
        [
            "Schedule package API info",
            "",
            "Capabilities:",
            "- Student timetable for short windows and full semesters.",
            "- Academic calendar day-off and exam-session lookup.",
            "- Faculty discovery for calendar tools.",
            "",
            "Faculty ID guidance:",
            "- Use `get_my_faculties` to list faculties from the authenticated student's programmes.",
            "- Use `search_faculties` when you only know part of a faculty name/code.",
            "- Use `get_faculty` to validate one chosen faculty_id.",
            "",
            "Calendar auto-resolution:",
            "- `get_days_off`, `get_semester_days_off`, and `get_exam_session_dates`",
            "  accept optional `faculty_id`.",
            "- If omitted, tools try to auto-resolve from active student programmes.",
            "- If multiple faculties are found, pass `faculty_id` explicitly.",
            "",
            "API constraints:",
            "- services/tt/student: max 7 days per request.",
            "- services/calendar/search: max 1 month per request.",
            "- services/calendar module is BETA in USOS API docs.",
        ]
    )
