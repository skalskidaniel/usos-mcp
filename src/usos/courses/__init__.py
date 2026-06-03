"""Courses package for retrieving general course details, syllabus details, and scheduled student exams.

This package provides MCP capabilities for:
- Fetching general course details (ECTS points, method of passing, assessment criteria).
- Fetching syllabus details for course editions (description, bibliography, and course units with class types).
- Checking scheduled exam dates and groups for the authenticated student.

USOS API modules used:
- services/courses (course, course_edition, course_edition2, class_types)
- services/exams (student_exams)

Registered tools:
- get_course: Fetch general details about a course.
- get_syllabus: Fetch full syllabus details of a course edition.
- get_exams: Check scheduled exam dates and groups for the authenticated student.
"""
