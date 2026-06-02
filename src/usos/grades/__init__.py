"""
Grades package for checking grades and calculating GPA.

This package provides MCP capabilities for:
- Fetching student grades for specific academic terms or course editions.
- Checking recently modified/acquired grades.
- Calculating ECTS-weighted GPA across specific or all active semesters.

USOS API modules used:
- services/grades
- services/courses

Registered tools:
- get_grades: Unified grade retrieval (term, course, latest, or all modes).
- get_gpa: ECTS-weighted GPA calculator.

Important constraints:
- Requires OAuth authorization with 'grades' scope.
- Weighted average calculations exclude non-numeric grade symbols (e.g., ZAL, NZAL, NK).
"""
