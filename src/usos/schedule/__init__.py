"""
Schedule package for timetable and academic calendar features.

This package provides MCP capabilities for:
- Personal timetable retrieval for short ranges (today, tomorrow, week).
- Semester-wide timetable retrieval by batching 7-day timetable windows.
- Academic calendar checks for days off and exam session periods.

USOS API modules used:
- services/tt
- services/calendar
- services/terms

Registered tools:
- get_my_schedule: Fetch student timetable in a selected date window.
- get_my_faculties: List faculties linked to the authenticated student's programmes.
- get_days_off: List day-off calendar events in a date range.
- get_exam_session_dates: List exam-session calendar events in a term.

Registered resources:
- usos://schedule/api-info: Summary of schedule package capabilities and limits.

Important constraints:
- services/tt/student allows a maximum of 7 days per request.
- services/calendar/search allows a maximum date range of one month per request.
- services/calendar is marked as BETA in USOS API documentation.
- Calendar tools can auto-resolve faculty_id from the authenticated user's profile
  only when exactly one active faculty is found.
"""
