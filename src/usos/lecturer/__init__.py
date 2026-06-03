"""Lecturer package for querying teacher profiles, schedules, and courses.

This package provides MCP capabilities for:
- Finding which lecturers teach a given course.
- Searching for employees/lecturers by name.
- Retrieving courses taught by a lecturer.
- Fetching lecturer-specific timetables.

USOS API modules used:
- services/courses/course
- services/users/search2
- services/groups/lecturer
- services/tt/staff

Registered tools:
- get_course_lecturers: Check who teaches a given course.
- search_lecturer: Search for employees/lecturers.
- get_lecturer_courses: Find what courses a given employee teaches.
- get_lecturer_schedule: Fetch a specific lecturer's timetable.
"""
