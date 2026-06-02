import unittest
from unittest.mock import patch
from datetime import date
from usos.utils import resolve_term_id

class TestResolveTermId(unittest.TestCase):
    def test_returns_explicit_term_id(self):
        self.assertEqual(resolve_term_id("2024Z"), "2024Z")

    @patch("usos.utils.fetch_active_terms")
    def test_falls_back_to_first_active_term_if_no_match(self, mock_fetch):
        # Setup: terms that don't contain today's date (assuming today is NOT 2020)
        mock_fetch.return_value = [
            {
                "id": "2020Z",
                "start_date": "2020-10-01",
                "finish_date": "2021-02-28",
            },
            {
                "id": "2020",
                "start_date": "2020-10-01",
                "finish_date": "2021-09-30",
            }
        ]
        # Since today is not in 2020/2021, none of the terms will match today's date.
        # It should fall back to returning the first term's ID ("2020Z").
        self.assertEqual(resolve_term_id(None), "2020Z")

    @patch("usos.utils.fetch_active_terms")
    @patch("usos.utils.date")
    def test_selects_shortest_duration_matching_term(self, mock_date, mock_fetch):
        # Mock today as 2026-06-02
        mock_date.today.return_value = date(2026, 6, 2)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw) # keep constructor working
        
        mock_fetch.return_value = [
            {
                "id": "2025",
                "start_date": "2025-10-01",
                "finish_date": "2026-09-30",
            },
            {
                "id": "2025Z",
                "start_date": "2025-10-01",
                "finish_date": "2026-02-28",
            },
            {
                "id": "2025L",
                "start_date": "2026-03-01",
                "finish_date": "2026-09-30",
            }
        ]
        
        self.assertEqual(resolve_term_id(None), "2025L")

    @patch("usos.utils.fetch_active_terms")
    def test_raises_error_if_no_active_terms(self, mock_fetch):
        mock_fetch.return_value = []
        with self.assertRaises(ValueError):
            resolve_term_id(None)

if __name__ == "__main__":
    unittest.main()
