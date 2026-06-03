import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from usos.grades.tools import get_grades


class TestGradesTools(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_ctx = MagicMock()
        self.mock_ctx.info = AsyncMock()
        self.mock_ctx.warning = AsyncMock()
        self.mock_ctx.error = AsyncMock()

    @patch("usos.grades.tools.fetch_latest_grades")
    async def test_get_grades_latest_success(self, mock_latest):
        mock_latest.return_value = [
            {
                "value_symbol": "5.0",
                "passes": True,
                "value_description": {"en": "Very good"},
                "exam_session_number": 1,
                "counts_into_average": True,
                "grade_type_id": "STD",
                "date_modified": "2026-06-01 10:00:00",
                "course_edition": {
                    "course_id": "CS101",
                    "course_name": {"en": "Programming"},
                }
            }
        ]

        res = await get_grades(mode="latest", days=7, ctx=self.mock_ctx)
        self.assertEqual(res["mode"], "latest")
        self.assertEqual(len(res["grades"]), 1)
        self.assertEqual(res["grades"][0].course_id, "CS101")
        self.assertEqual(res["grades"][0].value_symbol, "5.0")

    @patch("usos.grades.tools.fetch_latest_grades")
    @patch("usos.grades.tools.fetch_user_ects_points")
    @patch("usos.grades.tools.fetch_active_terms")
    @patch("usos.grades.tools.fetch_grades_by_terms")
    async def test_get_grades_latest_fallback_success(
        self, mock_fetch_terms_grades, mock_active_terms, mock_ects, mock_latest
    ):
        mock_latest.side_effect = Exception("500 Server Error: Internal Server Error")

        mock_ects.return_value = {"2025Z": {"CS101": "5.0"}}
        mock_active_terms.return_value = [{"id": "2025Z"}]

        now = datetime.now()
        date_recent = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        date_old = (now - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")

        mock_fetch_terms_grades.return_value = {
            "2025Z": {
                "CS101": {
                    "course_grades": [
                        {
                            "value_symbol": "4.5",
                            "passes": True,
                            "value_description": {"en": "Good plus"},
                            "exam_session_number": 1,
                            "counts_into_average": True,
                            "date_modified": date_recent,
                        },
                        {
                            "value_symbol": "3.0",
                            "passes": True,
                            "value_description": {"en": "Satisfactory"},
                            "exam_session_number": 1,
                            "counts_into_average": True,
                            "date_modified": date_old,
                        }
                    ]
                }
            }
        }

        res = await get_grades(mode="latest", days=7, ctx=self.mock_ctx)
        
        self.assertEqual(res["mode"], "latest")
        self.assertEqual(len(res["grades"]), 1)
        self.assertEqual(res["grades"][0].course_id, "CS101")
        self.assertEqual(res["grades"][0].value_symbol, "4.5")
        
        self.mock_ctx.warning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
