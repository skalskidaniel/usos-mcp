import unittest
from unittest.mock import patch, MagicMock
from datetime import date
from usos.utils import (
    resolve_term_id,
    resolve_faculty_id,
    fetch_user_faculties,
    MultipleFacultiesError,
    _parse_bool,
)

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


class TestFacultyResolution(unittest.TestCase):
    @patch("usos.utils.fetch_user_faculties")
    def test_resolve_faculty_id_explicit(self, mock_fetch):
        # If faculty_id is passed, it should be returned stripped
        self.assertEqual(resolve_faculty_id("  03000000  "), "03000000")
        mock_fetch.assert_not_called()

    @patch("usos.utils.fetch_user_faculties")
    def test_resolve_faculty_id_single(self, mock_fetch):
        # If faculty_id is None and exactly one faculty is returned, resolve to it
        mock_fetch.return_value = [{"id": "03000000", "name": "Faculty of Math"}]
        self.assertEqual(resolve_faculty_id(None), "03000000")

    @patch("usos.utils.fetch_user_faculties")
    def test_resolve_faculty_id_multiple(self, mock_fetch):
        # If multiple faculties are found, raise MultipleFacultiesError
        facs = [
            {"id": "03000000", "name": "Faculty of Math"},
            {"id": "04000000", "name": "Faculty of Physics"},
        ]
        mock_fetch.return_value = facs
        with self.assertRaises(MultipleFacultiesError) as ctx:
            resolve_faculty_id(None)
        self.assertEqual(ctx.exception.faculties, facs)

    @patch("usos.utils.fetch_user_faculties")
    def test_resolve_faculty_id_none(self, mock_fetch):
        # If no faculties are found, raise ValueError
        mock_fetch.return_value = []
        with self.assertRaises(ValueError):
            resolve_faculty_id(None)

    @patch("usos.utils.get_authenticated_session")
    @patch("usos.utils._get_base_url")
    def test_fetch_user_faculties_success(self, mock_base_url, mock_get_session):
        mock_base_url.return_value = "http://test"
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock the profile response containing student_programmes
        mock_profile_resp = MagicMock()
        mock_profile_resp.json.return_value = {
            "student_programmes": [
                {
                    "programme": {
                        "id": "PROG-1"
                    }
                }
            ]
        }
        
        # Mock the programme response containing faculty info
        mock_prog_resp = MagicMock()
        mock_prog_resp.json.return_value = {
            "id": "PROG-1",
            "faculty": {
                "id": "FAC-1",
                "name": {"en": "Faculty of Computer Science"}
            }
        }

        mock_session.get.side_effect = [mock_profile_resp, mock_prog_resp]

        faculties = fetch_user_faculties()
        self.assertEqual(len(faculties), 1)
        self.assertEqual(faculties[0]["id"], "FAC-1")
        self.assertEqual(faculties[0]["name"]["en"], "Faculty of Computer Science")


class TestParseBool(unittest.TestCase):
    def test_parse_bool(self):
        self.assertTrue(_parse_bool(True))
        self.assertFalse(_parse_bool(False))
        self.assertTrue(_parse_bool("T"))
        self.assertTrue(_parse_bool("true"))
        self.assertTrue(_parse_bool("TRUE"))
        self.assertTrue(_parse_bool("y"))
        self.assertTrue(_parse_bool("yes"))
        self.assertTrue(_parse_bool("1"))
        self.assertFalse(_parse_bool("F"))
        self.assertFalse(_parse_bool("false"))
        self.assertFalse(_parse_bool("0"))
        self.assertTrue(_parse_bool(1))
        self.assertTrue(_parse_bool(1.5))
        self.assertFalse(_parse_bool(0))
        self.assertFalse(_parse_bool(None))
        self.assertFalse(_parse_bool([]))


if __name__ == "__main__":
    unittest.main()

