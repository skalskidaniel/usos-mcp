import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pydantic import ValidationError

from fastmcp.exceptions import ToolError

from usos.lecturer.models import AcademicTitles, Lecturer, LecturerGroup
from usos.lecturer.tools import (
    get_course_lecturers,
    search_lecturer,
    get_lecturer_courses,
)


class TestLecturerModels(unittest.TestCase):
    def test_academic_titles_cleaning(self):
        titles = AcademicTitles(before="  dr hab.  ", after=" PhD ")
        self.assertEqual(titles.before, "dr hab.")
        self.assertEqual(titles.after, "PhD")

        titles_none = AcademicTitles(before=None, after="")
        self.assertIsNone(titles_none.before)
        self.assertIsNone(titles_none.after)

    def test_lecturer_validation(self):
        # Valid lecturer
        lecturer = Lecturer(
            id="123",
            first_name="John",
            last_name="Doe",
            titles={"before": "Dr"},
            email="john.doe@example.com",
        )
        self.assertEqual(lecturer.id, "123")
        self.assertEqual(lecturer.titles.before, "Dr")

        # Invalid emails
        with self.assertRaises(ValidationError):
            Lecturer(id="123", first_name="John", last_name="Doe", email="invalid-email")

        # Empty/missing required fields
        with self.assertRaises(ValidationError):
            Lecturer(id=" ", first_name="John", last_name="Doe")

    def test_lecturer_group_validation(self):
        # Valid group
        group = LecturerGroup(
            course_id="CS-101",
            course_name="Intro to CS",
            class_type_id="w",
        )
        self.assertEqual(group.course_id, "CS-101")
        self.assertEqual(group.course_name, "Intro to CS")
        self.assertEqual(group.class_type_id, "w")

        # Invalid course_id
        with self.assertRaises(ValidationError):
            LecturerGroup(course_id="", class_type_id="w")


class TestLecturerTools(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_ctx = MagicMock()
        self.mock_ctx.info = AsyncMock()
        self.mock_ctx.error = AsyncMock()

    @patch("usos.lecturer.tools.resolve_term_id")
    @patch("usos.lecturer.tools.fetch_course_lecturers")
    async def test_get_course_lecturers_success(self, mock_fetch, mock_resolve_term):
        mock_resolve_term.return_value = "2025Z"
        mock_fetch.return_value = {
            "course_name": {"en": "Software Engineering"},
            "lecturers": [
                {
                    "id": "1",
                    "first_name": "Alice",
                    "last_name": "Smith",
                    "titles": {"before": "Prof."},
                    "email": "alice@example.com",
                }
            ],
        }

        result = await get_course_lecturers(
            course_id="SE-01", term_id="2025Z", ctx=self.mock_ctx
        )
        self.assertEqual(result["course_id"], "SE-01")
        self.assertEqual(result["course_name"], "Software Engineering")
        self.assertEqual(result["term_id"], "2025Z")
        self.assertEqual(len(result["lecturers"]), 1)
        self.assertIsInstance(result["lecturers"][0], Lecturer)
        self.assertEqual(result["lecturers"][0].first_name, "Alice")

    @patch("usos.lecturer.tools.resolve_term_id")
    @patch("usos.lecturer.tools.fetch_course_lecturers")
    async def test_get_course_lecturers_error(self, mock_fetch, mock_resolve_term):
        mock_resolve_term.return_value = "2025Z"
        mock_fetch.side_effect = Exception("API connection error")

        with self.assertRaises(ToolError):
            await get_course_lecturers(course_id="SE-01", ctx=self.mock_ctx)

    @patch("usos.lecturer.tools.fetch_user_profile")
    @patch("usos.lecturer.tools.search_users")
    async def test_search_lecturer_success(self, mock_search, mock_profile):
        mock_search.return_value = [
            {"user_id": "10"},
            {"id": "20"},
        ]
        # Profile mock returns dictionary for first user, None/error for second
        mock_profile.side_effect = [
            {
                "id": "10",
                "first_name": "Bob",
                "last_name": "Jones",
                "email": "bob@example.com",
            },
            None,  # Should be skipped safely
        ]

        result = await search_lecturer(query="Bob", limit=5, ctx=self.mock_ctx)
        self.assertEqual(result["query"], "Bob")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0].first_name, "Bob")

    @patch("usos.lecturer.tools.search_users")
    async def test_search_lecturer_error(self, mock_search):
        mock_search.side_effect = Exception("Search timed out")

        with self.assertRaises(ToolError):
            await search_lecturer(query="Bob", ctx=self.mock_ctx)

    @patch("usos.lecturer.tools.fetch_lecturer_courses")
    async def test_get_lecturer_courses_success(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "course_id": "CS-101",
                "course_name": "Programming",
                "term_id": "2025Z",
                "number": 1,
                "class_type_id": "w",
            },
            {
                "course_id": "CS-101",
                "course_name": "Programming",
                "term_id": "2026Z",
                "number": 2,
                "class_type_id": "w",
            },
            {
                "course_id": "CS-102",
                "course_name": "Databases",
                "term_id": "2025L",
                "group_number": 2,
                "class_type_id": "c",
            },
        ]

        result = await get_lecturer_courses(lecturer_id="99", ctx=self.mock_ctx)
        self.assertEqual(result["lecturer_id"], "99")
        self.assertEqual(result["courses_count"], 2)
        self.assertEqual(len(result["courses"]), 2)
        self.assertIsInstance(result["courses"][0], LecturerGroup)
        self.assertEqual(result["courses"][0].course_id, "CS-101")
        self.assertEqual(result["courses"][0].course_name, "Programming")
        self.assertEqual(result["courses"][0].class_type_id, "w")
        self.assertEqual(result["courses"][1].course_id, "CS-102")

    @patch("usos.lecturer.tools.fetch_lecturer_courses")
    async def test_get_lecturer_courses_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("Lecturer not found")

        with self.assertRaises(ToolError):
            await get_lecturer_courses(lecturer_id="99", ctx=self.mock_ctx)

if __name__ == "__main__":
    unittest.main()
