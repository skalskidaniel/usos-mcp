"""USOS MCP Courses Package.

Exposes MCP tools for retrieving general course information, syllabus details,
and student exam schedules from the USOS API.
"""

from .tools import get_course, get_syllabus, get_exams, resolve_classtypes

__all__ = [
    "get_course",
    "get_syllabus",
    "get_exams",
    "resolve_classtypes",
]
