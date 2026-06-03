import unittest
from unittest.mock import patch, MagicMock
import asyncio
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

from usos.courses.models import CourseBasicInfo, CourseSyllabus, StudentExam, CourseUnitInfo, ExamGroupDetails
from usos.courses.tools import get_course, get_syllabus, get_exams, resolve_classtypes
from usos.courses.utils import fetch_course_basic_info, fetch_syllabus_details, fetch_student_exams


class TestCoursesModels(unittest.TestCase):
    def test_course_basic_info_validation(self):
        # Valid model
        info = CourseBasicInfo(
            course_id="CS101",
            name="Intro to CS",
            ects_credits=5.0,
            assessment_criteria="Exam",
            passing_status="passed",
        )
        self.assertEqual(info.course_id, "CS101")
        self.assertEqual(info.passing_status, "passed")

        # Invalid passing status
        with self.assertRaises(ValidationError):
            CourseBasicInfo(
                course_id="CS101",
                name="Intro to CS",
                passing_status="unknown_status",
            )

        # Invalid ECTS credits (too high)
        with self.assertRaises(ValidationError):
            CourseBasicInfo(
                course_id="CS101",
                name="Intro to CS",
                ects_credits=100.0,
            )

    def test_course_syllabus_and_unit_info(self):
        unit = CourseUnitInfo(
            unit_id=123,
            classtype_id="w",
            class_type_name="Lecture",
            topics="Functions, Loops",
            learning_outcomes="Understand basics",
            assessment_criteria="Quiz",
        )
        syllabus = CourseSyllabus(
            course_id="CS101",
            name="Intro to CS",
            term_id="2025Z",
            description="Learn to code",
            prerequisites="None",
            bibliography="Book A",
            course_units=[unit],
        )
        self.assertEqual(syllabus.term_id, "2025Z")
        self.assertEqual(len(syllabus.course_units), 1)
        self.assertEqual(syllabus.course_units[0].unit_id, 123)

        # Invalid term_id format
        with self.assertRaises(ValidationError):
            CourseSyllabus(
                course_id="CS101",
                name="Intro to CS",
                term_id="invalid_term",
            )

    def test_exam_group_details_dates_validation(self):
        # Valid dates
        details = ExamGroupDetails(
            group_number=1,
            exam_start="2026-06-15T09:00:00",
            exam_end="2026-06-15T12:00:00",
            capacity=30,
        )
        self.assertEqual(details.group_number, 1)

        # Invalid dates (start after end)
        with self.assertRaises(ValidationError) as ctx:
            ExamGroupDetails(
                group_number=1,
                exam_start="2026-06-15T15:00:00",
                exam_end="2026-06-15T12:00:00",
            )
        self.assertIn("exam_start must be before exam_end", str(ctx.exception))


class TestCoursesUtils(unittest.TestCase):
    @patch("usos.courses.utils.get_authenticated_session")
    @patch("usos.courses.utils._get_base_url")
    def test_fetch_course_basic_info_with_term_success(self, mock_get_base_url, mock_get_session):
        mock_get_base_url.return_value = "https://usos.example.com"
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock the edition response
        mock_response_ed = MagicMock()
        mock_response_ed.json.return_value = {
            "passing_status": "passed",
            "course": {
                "id": "CS101",
                "name": {"en": "Intro to CS"},
                "ects_credits_simplified": 6.0,
                "assessment_criteria": {"en": "Written exam"},
            }
        }
        mock_session.get.return_value = mock_response_ed

        res = fetch_course_basic_info("CS101", "2025Z")
        self.assertEqual(res["course_id"], "CS101")
        self.assertEqual(res["name"], "Intro to CS")
        self.assertEqual(res["ects_credits"], 6.0)
        self.assertEqual(res["passing_status"], "passed")

    @patch("usos.courses.utils.get_authenticated_session")
    @patch("usos.courses.utils._get_base_url")
    def test_fetch_course_basic_info_fallback_to_course2(self, mock_get_base_url, mock_get_session):
        mock_get_base_url.return_value = "https://usos.example.com"
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock course_edition2 to fail, and course2 to succeed
        mock_response_ed = MagicMock()
        mock_response_ed.json.side_effect = Exception("Not found")
        
        mock_response_c2 = MagicMock()
        mock_response_c2.json.return_value = {
            "CS101": {
                "id": "CS101",
                "name": {"en": "Intro to CS"},
                "ects_credits_simplified": 5.0,
                "assessment_criteria": {"en": "Project"},
            }
        }

        mock_session.get.side_effect = [mock_response_ed, mock_response_c2]

        res = fetch_course_basic_info("CS101", "2025Z")
        self.assertEqual(res["course_id"], "CS101")
        self.assertEqual(res["ects_credits"], 5.0)
        self.assertIsNone(res["passing_status"])

    @patch("usos.courses.utils.get_authenticated_session")
    @patch("usos.courses.utils._get_base_url")
    def test_fetch_course_basic_info_not_found(self, mock_get_base_url, mock_get_session):
        mock_get_base_url.return_value = "https://usos.example.com"
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock course2 returning empty dict
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_session.get.return_value = mock_response

        with self.assertRaises(ValueError):
            fetch_course_basic_info("CS101", None)

    @patch("usos.courses.utils.get_authenticated_session")
    @patch("usos.courses.utils._get_base_url")
    def test_fetch_syllabus_details_success(self, mock_get_base_url, mock_get_session):
        mock_get_base_url.return_value = "https://usos.example.com"
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "course_id": "CS101",
            "course_name": {"en": "Intro to CS"},
            "term_id": "2025Z",
            "description": {"en": "Learn to code"},
            "bibliography": {"en": "Some book"},
            "course_units": [
                {
                    "id": 444,
                    "classtype_id": "w",
                    "topics": {"en": "Loops"},
                    "learning_outcomes": {"en": "Learn loops"},
                    "assessment_criteria": {"en": "Quiz"},
                }
            ]
        }
        mock_session.get.return_value = mock_response

        res = fetch_syllabus_details("CS101", "2025Z")
        self.assertEqual(res["course_id"], "CS101")
        self.assertEqual(res["name"], "Intro to CS")
        self.assertEqual(len(res["course_units"]), 1)
        self.assertEqual(res["course_units"][0]["id"], 444)

    @patch("usos.courses.utils.get_authenticated_session")
    @patch("usos.courses.utils._get_base_url")
    def test_fetch_syllabus_details_not_found(self, mock_get_base_url, mock_get_session):
        mock_get_base_url.return_value = "https://usos.example.com"
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_session.get.return_value = mock_response

        with self.assertRaises(ValueError):
            fetch_syllabus_details("CS101", "2025Z")


class TestCoursesTools(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_ctx = MagicMock()
        self.mock_ctx.info = unittest.mock.AsyncMock()
        self.mock_ctx.error = unittest.mock.AsyncMock()

    @patch("usos.courses.tools.resolve_term_id")
    @patch("usos.courses.tools.fetch_course_basic_info")
    async def test_get_course_tool_success(self, mock_fetch_info, mock_resolve_term):
        mock_resolve_term.return_value = "2025Z"
        mock_fetch_info.return_value = {
            "course_id": "CS101",
            "name": "Intro to CS",
            "ects_credits": 5.0,
            "assessment_criteria": "Exam",
            "passing_status": "passed",
        }

        res = await get_course("CS101", "2025Z", ctx=self.mock_ctx)
        self.assertEqual(res["course_id"], "CS101")
        self.assertEqual(res["passing_status"], "passed")
        mock_resolve_term.assert_called_once_with("2025Z")

    @patch("usos.courses.tools.resolve_term_id")
    @patch("usos.courses.tools.fetch_course_basic_info")
    async def test_get_course_tool_error(self, mock_fetch_info, mock_resolve_term):
        mock_resolve_term.side_effect = Exception("API error")

        with self.assertRaises(ToolError):
            await get_course("CS101", "2025Z", ctx=self.mock_ctx)

    @patch("usos.courses.tools.resolve_term_id")
    @patch("usos.courses.tools.fetch_syllabus_details")
    @patch("usos.courses.tools.fetch_classtypes_index")
    async def test_get_syllabus_tool_success(self, mock_fetch_classtypes, mock_fetch_syllabus, mock_resolve_term):
        mock_resolve_term.return_value = "2025Z"
        mock_fetch_syllabus.return_value = {
            "course_id": "CS101",
            "name": "Intro to CS",
            "term_id": "2025Z",
            "description": "Learn to code",
            "bibliography": "Some book",
            "prerequisites": None,
            "course_units": [
                {
                    "id": 444,
                    "classtype_id": "w",
                    "topics": "Loops",
                    "learning_outcomes": "Learn loops",
                    "assessment_criteria": "Quiz",
                }
            ]
        }
        mock_fetch_classtypes.return_value = {
            "w": {"name": {"en": "Lecture", "pl": "Wykład"}}
        }

        res = await get_syllabus("CS101", "2025Z", ctx=self.mock_ctx)
        self.assertEqual(res["course_id"], "CS101")
        self.assertEqual(res["term_id"], "2025Z")
        self.assertEqual(len(res["course_units"]), 1)
        unit = res["course_units"][0]
        self.assertEqual(unit["unit_id"], 444)
        self.assertEqual(unit["class_type_name"], "Lecture")

    @patch("usos.courses.tools.fetch_student_exams")
    async def test_get_exams_tool_success(self, mock_fetch_exams):
        mock_fetch_exams.return_value = [
            {
                "id": "exam_99",
                "course": {"id": "CS101", "name": {"en": "Intro to CS"}},
                "term": {"id": "2025Z"},
                "examination_session_id": "session_1",
                "groups": [
                    {
                        "number": 2,
                        "exam_start": "2026-06-15 09:00:00",
                        "exam_end": "2026-06-15 12:00:00",
                        "capacity": 50,
                    }
                ]
            }
        ]

        res = await get_exams(ctx=self.mock_ctx)
        self.assertEqual(len(res), 1)
        exam = res[0]
        self.assertEqual(exam["exam_id"], "exam_99")
        self.assertEqual(exam["course_id"], "CS101")
        self.assertEqual(exam["course_name"], "Intro to CS")
        self.assertEqual(exam["term_id"], "2025Z")
        self.assertEqual(len(exam["groups"]), 1)
        grp = exam["groups"][0]
        self.assertEqual(grp["group_number"], 2)
        self.assertEqual(grp["exam_start"], "2026-06-15 09:00:00")
        self.assertEqual(grp["exam_end"], "2026-06-15 12:00:00")
        self.assertEqual(grp["capacity"], 50)

    @patch("usos.courses.tools.fetch_classtypes_index")
    async def test_resolve_classtypes_tool_success(self, mock_fetch_classtypes):
        mock_fetch_classtypes.return_value = {
            "w": {"name": {"en": "Lecture", "pl": "Wykład"}},
            "c": {"name": {"en": "Exercises", "pl": "Ćwiczenia"}}
        }

        res = await resolve_classtypes(ctx=self.mock_ctx)
        self.assertEqual(res["w"], "Lecture")
        self.assertEqual(res["c"], "Exercises")


if __name__ == "__main__":
    unittest.main()
