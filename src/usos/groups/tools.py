import asyncio

from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.tools import tool
from fastmcp.exceptions import ToolError

from usos.utils import extract_localized_str, fetch_user_profile
from .models import StudentGroup, GroupParticipant
from .utils import fetch_user_groups, fetch_group_participants


@tool(
    name="get_student_groups",
    description=(
        "Retrieve the list of class groups the authenticated student belongs to. "
        "Filter results to active academic terms only using active_only=True."
    ),
    tags={"groups"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    timeout=30,
)
async def get_student_groups(
    active_only: bool = False,
    ctx: Context = CurrentContext(),
) -> dict:
    """
    Args:
        active_only: If True, filters the returned groups to only those in the currently active academic terms.
    """
    try:
        await ctx.info("Retrieving student class groups from USOS API.")
        payload = await asyncio.to_thread(fetch_user_groups, active_only)

        raw_groups_by_term = payload.get("groups") or {}

        student_groups = []
        for term_id, raw_groups in raw_groups_by_term.items():
            if not isinstance(raw_groups, list):
                continue
            for rg in raw_groups:
                student_groups.append(
                    StudentGroup(
                        course_unit_id=int(rg.get("course_unit_id")),
                        group_number=int(rg.get("group_number")),
                        class_type=extract_localized_str(rg.get("class_type")),
                        class_type_id=rg.get("class_type_id"),
                        course_id=rg.get("course_id"),
                        course_name=extract_localized_str(rg.get("course_name")),
                        term_id=term_id,
                    )
                )

        return {
            "active_only": active_only,
            "groups": [g.model_dump() for g in student_groups],
        }
    except Exception as exc:
        await ctx.error(f"Failed to fetch student groups: {exc}")
        raise ToolError(f"Failed to fetch student groups: {exc}") from exc


@tool(
    name="get_group_participants",
    description=(
        "List the first names and surnames of other students enrolled in a specific class group. "
        "Requires course_unit_id and group_number."
    ),
    tags={"groups"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    timeout=30,
)
async def get_group_participants(
    course_unit_id: int,
    group_number: int,
    ctx: Context = CurrentContext(),
) -> dict:
    """
    Args:
        course_unit_id: The ID of the course unit the group belongs to.
        group_number: The number of the specific class group.
    """
    try:
        await ctx.info(
            f"Retrieving participants for group {group_number} under course unit {course_unit_id}."
        )

        participants_task = asyncio.to_thread(fetch_group_participants, course_unit_id, group_number)
        current_user_task = asyncio.to_thread(fetch_user_profile, None, "id")

        raw_participants, current_user_data = await asyncio.gather(
            participants_task, current_user_task
        )
        current_user_id = current_user_data.get("id")

        other_students = []
        for rp in raw_participants:
            p_id = rp.get("id")
            if current_user_id and str(p_id) == str(current_user_id):
                continue

            other_students.append(
                GroupParticipant(
                    id=str(p_id) if p_id is not None else "",
                    first_name=rp.get("first_name") or "",
                    last_name=rp.get("last_name") or "",
                )
            )

        return {
            "course_unit_id": course_unit_id,
            "group_number": group_number,
            "participants": [p.model_dump() for p in other_students],
        }
    except Exception as exc:
        await ctx.error(f"Failed to fetch group participants: {exc}")
        raise ToolError(f"Failed to fetch group participants: {exc}") from exc
