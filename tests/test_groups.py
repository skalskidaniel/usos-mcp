import unittest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from fastmcp.exceptions import ToolError
from usos.groups.models import StudentGroup, GroupParticipant
from usos.groups.tools import get_student_groups, get_group_participants


class TestGroupsModels(unittest.TestCase):
    def test_student_group_validation(self):
        # Valid data
        group = StudentGroup(
            course_unit_id=12345,
            group_number=1,
            class_type="Lecture",
            class_type_id="WYK",
            course_id="INFO-1-1",
            course_name="Introduction to CS",
            term_id="2025Z",
        )
        self.assertEqual(group.course_unit_id, 12345)
        self.assertEqual(group.group_number, 1)
        self.assertEqual(group.term_id, "2025Z")

        # Invalid course_unit_id (<= 0)
        with self.assertRaises(ValidationError):
            StudentGroup(
                course_unit_id=0,
                group_number=1,
                term_id="2025Z",
            )

        # Invalid group_number (<= 0)
        with self.assertRaises(ValidationError):
            StudentGroup(
                course_unit_id=12345,
                group_number=0,
                term_id="2025Z",
            )

        # Invalid term_id pattern
        with self.assertRaises(ValidationError):
            StudentGroup(
                course_unit_id=12345,
                group_number=1,
                term_id="2025X",
            )

    def test_group_participant_validation(self):
        # Valid data
        participant = GroupParticipant(
            id="1234",
            first_name="John",
            last_name="Doe",
        )
        self.assertEqual(participant.id, "1234")
        self.assertEqual(participant.first_name, "John")
        self.assertEqual(participant.last_name, "Doe")

        # Invalid empty id
        with self.assertRaises(ValidationError):
            GroupParticipant(
                id="",
                first_name="John",
                last_name="Doe",
            )


class TestGroupsTools(unittest.IsolatedAsyncioTestCase):
    @patch("usos.groups.tools.fetch_user_groups")
    async def test_get_student_groups_success(self, mock_fetch):
        # Mock payload from services/groups/user
        mock_fetch.return_value = {
            "groups": {
                "2025Z": [
                    {
                        "course_unit_id": 101,
                        "group_number": 2,
                        "class_type": {"en": "Laboratory", "pl": "Laboratorium"},
                        "class_type_id": "LAB",
                        "course_id": "CS-101",
                        "course_name": {"en": "Computer Science I"},
                    }
                ]
            }
        }

        mock_ctx = MagicMock()
        mock_ctx.info = unittest.mock.AsyncMock()
        mock_ctx.error = unittest.mock.AsyncMock()

        result = await get_student_groups(active_only=True, ctx=mock_ctx)

        self.assertTrue(result["active_only"])
        self.assertEqual(len(result["groups"]), 1)
        group = result["groups"][0]
        self.assertEqual(group["course_unit_id"], 101)
        self.assertEqual(group["group_number"], 2)
        self.assertEqual(group["class_type"], "Laboratory")
        self.assertEqual(group["class_type_id"], "LAB")
        self.assertEqual(group["course_id"], "CS-101")
        self.assertEqual(group["course_name"], "Computer Science I")
        self.assertEqual(group["term_id"], "2025Z")

        mock_ctx.info.assert_called_once()

    @patch("usos.groups.tools.fetch_user_groups")
    async def test_get_student_groups_error(self, mock_fetch):
        mock_fetch.side_effect = Exception("API connection timed out")

        mock_ctx = MagicMock()
        mock_ctx.info = unittest.mock.AsyncMock()
        mock_ctx.error = unittest.mock.AsyncMock()

        with self.assertRaises(ToolError) as ctx:
            await get_student_groups(active_only=False, ctx=mock_ctx)

        self.assertIn("Failed to fetch student groups", str(ctx.exception))
        mock_ctx.error.assert_called_once()

    @patch("usos.groups.tools.fetch_user_profile")
    @patch("usos.groups.tools.fetch_group_participants")
    async def test_get_group_participants_success(self, mock_fetch_participants, mock_fetch_profile):
        # Mock currently authenticated user's ID
        mock_fetch_profile.return_value = {"id": "999"}

        # Mock participant list (one of them is the current user 999)
        mock_fetch_participants.return_value = [
            {"id": "111", "first_name": "Alice", "last_name": "Smith"},
            {"id": "999", "first_name": "Me", "last_name": "Myself"},
            {"id": "222", "first_name": "Bob", "last_name": "Jones"},
        ]

        mock_ctx = MagicMock()
        mock_ctx.info = unittest.mock.AsyncMock()
        mock_ctx.error = unittest.mock.AsyncMock()

        result = await get_group_participants(
            course_unit_id=12345,
            group_number=1,
            ctx=mock_ctx,
        )

        self.assertEqual(result["course_unit_id"], 12345)
        self.assertEqual(result["group_number"], 1)
        self.assertEqual(len(result["participants"]), 2)

        p1 = result["participants"][0]
        self.assertEqual(p1["id"], "111")
        self.assertEqual(p1["first_name"], "Alice")
        self.assertEqual(p1["last_name"], "Smith")

        p2 = result["participants"][1]
        self.assertEqual(p2["id"], "222")
        self.assertEqual(p2["first_name"], "Bob")
        self.assertEqual(p2["last_name"], "Jones")

        mock_ctx.info.assert_called_once()

    @patch("usos.groups.tools.fetch_group_participants")
    async def test_get_group_participants_error(self, mock_fetch_participants):
        mock_fetch_participants.side_effect = Exception("HTTP 403 Forbidden")

        mock_ctx = MagicMock()
        mock_ctx.info = unittest.mock.AsyncMock()
        mock_ctx.error = unittest.mock.AsyncMock()

        with self.assertRaises(ToolError) as ctx:
            await get_group_participants(
                course_unit_id=12345,
                group_number=1,
                ctx=mock_ctx,
            )

        self.assertIn("Failed to fetch group participants", str(ctx.exception))
        mock_ctx.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
