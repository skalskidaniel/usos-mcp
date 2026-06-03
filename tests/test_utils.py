import unittest
from unittest.mock import patch, MagicMock
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


from usos.utils import (
    _parse_bool,
    resolve_faculty_id,
    fetch_user_faculties,
    fetch_classtypes_index,
    MultipleFacultiesError,
)

class TestRefactoredUtils(unittest.TestCase):
    def test_parse_bool(self):
        self.assertTrue(_parse_bool(True))
        self.assertTrue(_parse_bool("True"))
        self.assertTrue(_parse_bool("T"))
        self.assertTrue(_parse_bool("yes"))
        self.assertTrue(_parse_bool(1))
        self.assertFalse(_parse_bool(False))
        self.assertFalse(_parse_bool("False"))
        self.assertFalse(_parse_bool("N"))
        self.assertFalse(_parse_bool(0))
        self.assertFalse(_parse_bool(None))

    @patch("usos.utils.fetch_user_faculties")
    def test_resolve_faculty_id_success(self, mock_fetch):
        # 1. Explicit faculty_id passed
        self.assertEqual(resolve_faculty_id("03000000"), "03000000")

        # 2. Auto-resolve single faculty
        mock_fetch.return_value = [{"id": "04000000", "name": "Faculty of CS"}]
        self.assertEqual(resolve_faculty_id(None), "04000000")

    @patch("usos.utils.fetch_user_faculties")
    def test_resolve_faculty_id_multiple(self, mock_fetch):
        mock_fetch.return_value = [
            {"id": "03000000", "name": "Faculty A"},
            {"id": "04000000", "name": "Faculty B"},
        ]
        with self.assertRaises(MultipleFacultiesError) as ctx:
            resolve_faculty_id(None)
        self.assertEqual(len(ctx.exception.faculties), 2)

    @patch("usos.utils.fetch_user_faculties")
    def test_resolve_faculty_id_empty(self, mock_fetch):
        mock_fetch.return_value = []
        with self.assertRaises(ValueError):
            resolve_faculty_id(None)

    @patch("usos.utils.get_authenticated_session")
    @patch("usos.utils._get_base_url")
    def test_fetch_user_faculties_success(self, mock_get_base_url, mock_get_session):
        mock_get_base_url.return_value = "https://usos.example.com"
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock response for /services/users/user
        mock_res_user = MagicMock()
        mock_res_user.json.return_value = {
            "student_programmes": [
                {"programme": {"id": "PROG-CS"}}
            ]
        }
        # Mock response for /services/progs/programme
        mock_res_prog = MagicMock()
        mock_res_prog.json.return_value = {
            "faculty": {"id": "FAC-CS", "name": {"en": "Computer Science"}}
        }

        mock_session.get.side_effect = [mock_res_user, mock_res_prog]

        facs = fetch_user_faculties()
        self.assertEqual(len(facs), 1)
        self.assertEqual(facs[0]["id"], "FAC-CS")

    @patch("usos.utils._get_with_retries")
    @patch("usos.utils._get_base_url")
    def test_fetch_classtypes_index_success(self, mock_get_base_url, mock_get_with_retries):
        mock_get_base_url.return_value = "https://usos.example.com"
        mock_res = MagicMock()
        mock_res.json.return_value = {
            "w": {"name": {"en": "Lecture"}},
        }
        mock_get_with_retries.return_value = mock_res

        types = fetch_classtypes_index()
        self.assertEqual(types["w"]["name"]["en"], "Lecture")


if __name__ == "__main__":
    unittest.main()
