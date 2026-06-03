import unittest
from unittest.mock import patch, MagicMock
from usos.schedule.utils import flatten_calendar_event
from fastmcp.exceptions import ToolError
from usos.schedule.tools import get_days_off, get_exam_session_dates

class TestScheduleTools(unittest.IsolatedAsyncioTestCase):
    def test_flatten_calendar_event(self):
        raw_event = {
            "id": "405",
            "name": {
                "pl": "Przerwa świąteczna",
                "en": "Christmas break"
            },
            "start_date": "2025-12-24 00:00:00",
            "end_date": "2026-01-06 23:59:00",
            "type": "break",
            "is_day_off": True
        }
        
        flat = flatten_calendar_event(raw_event)
        self.assertEqual(flat["id"], "405")
        self.assertEqual(flat["name"], "Christmas break")
        self.assertEqual(flat["start_date"], "2025-12-24")
        self.assertEqual(flat["end_date"], "2026-01-06")
        self.assertEqual(flat["type"], "break")
        self.assertTrue(flat["is_day_off"])

    @patch("usos.schedule.tools.resolve_faculty_id")
    @patch("usos.schedule.tools.fetch_calendar_events")
    async def test_get_days_off_returns_flat_models(self, mock_fetch_events, mock_resolve_faculty):
        mock_resolve_faculty.return_value = "03000000"
        mock_fetch_events.return_value = [
            {
                "id": "405",
                "name": {"en": "Christmas break"},
                "start_date": "2025-12-24 00:00:00",
                "end_date": "2026-01-06 23:59:00",
                "type": "break",
                "is_day_off": True
            },
            {
                "id": "406",
                "name": {"en": "New Year"},
                "start_date": "2026-01-01 00:00:00",
                "end_date": "2026-01-01 23:59:00",
                "type": "holiday",
                "is_day_off": False # should be filtered out from days_off
            }
        ]
        
        # Create a mock context with async info and error methods
        mock_ctx = MagicMock()
        mock_ctx.info = unittest.mock.AsyncMock()
        mock_ctx.error = unittest.mock.AsyncMock()

        # Since get_days_off is an async function, we await it
        result = await get_days_off(
            start_date="2025-12-01",
            end_date="2026-01-15",
            faculty_id="03000000",
            ctx=mock_ctx
        )
        
        self.assertEqual(result["faculty_id"], "03000000")
        self.assertEqual(len(result["days_off"]), 1)
        event = result["days_off"][0]
        self.assertEqual(event.id, "405")
        self.assertEqual(event.name, "Christmas break")
        self.assertEqual(event.start_date, "2025-12-24")
        self.assertEqual(event.end_date, "2026-01-06")
        self.assertTrue(event.is_day_off)

    @patch("usos.schedule.tools.resolve_faculty_id")
    @patch("usos.schedule.tools.resolve_term_id")
    @patch("usos.schedule.tools.get_semester_date_range")
    @patch("usos.schedule.tools.fetch_calendar_events")
    async def test_get_exam_session_dates_returns_flat_models(
        self, mock_fetch_events, mock_date_range, mock_resolve_term, mock_resolve_faculty
    ):
        mock_resolve_faculty.return_value = "03000000"
        mock_resolve_term.return_value = "2025L"
        mock_date_range.return_value = ("2026-03-01", "2026-09-30")
        mock_fetch_events.return_value = [
            {
                "id": "exam_1",
                "name": {"en": "Exam Session 1"},
                "start_date": "2026-06-15 09:00:00",
                "end_date": "2026-06-25 18:00:00",
                "type": "exam_session",
                "is_day_off": False
            }
        ]
        
        mock_ctx = MagicMock()
        mock_ctx.info = unittest.mock.AsyncMock()
        mock_ctx.error = unittest.mock.AsyncMock()

        result = await get_exam_session_dates(
            term_id="2025L",
            faculty_id="03000000",
            ctx=mock_ctx
        )
        
        self.assertEqual(result["faculty_id"], "03000000")
        self.assertEqual(result["term_id"], "2025L")
        self.assertEqual(len(result["exam_sessions"]), 1)
        event = result["exam_sessions"][0]
        self.assertEqual(event.id, "exam_1")
        self.assertEqual(event.name, "Exam Session 1")
        self.assertEqual(event.start_date, "2026-06-15")
        self.assertEqual(event.end_date, "2026-06-25")

    @patch("usos.schedule.tools.resolve_faculty_id")
    async def test_get_days_off_raises_tool_error_on_exception(self, mock_resolve_faculty):
        mock_resolve_faculty.side_effect = Exception("API error")
        
        mock_ctx = MagicMock()
        mock_ctx.info = unittest.mock.AsyncMock()
        mock_ctx.error = unittest.mock.AsyncMock()

        with self.assertRaises(ToolError):
            await get_days_off(
                start_date="2025-12-01",
                end_date="2026-01-15",
                faculty_id="03000000",
                ctx=mock_ctx
            )

if __name__ == "__main__":
    unittest.main()
