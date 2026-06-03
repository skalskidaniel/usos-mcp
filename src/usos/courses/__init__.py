"""Courses package for retrieving general course details, syllabus details, and scheduled student exams.

This package provides MCP capabilities for:
- Fetching course details and syllabus information (ECTS points, method of passing, assessment criteria, description, bibliography, and course units with class types).
- Checking scheduled exam dates and groups for the authenticated student.

USOS API modules used:
- services/courses (course, course_edition, class_types)
- services/exams (student_exams)

Registered tools:
- get_course_info: Fetch comprehensive details about a course edition.
- get_exams: Check scheduled exam dates and groups for the authenticated student.
"""
