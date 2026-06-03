import asyncio
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.tools import tool
from fastmcp.exceptions import ToolError

from usos.utils import resolve_term_id, extract_localized_str, fetch_classtypes_index
from .models import CourseBasicInfo, CourseSyllabus, StudentExam, CourseUnitInfo, ExamGroupDetails
from .utils import (
    fetch_course_basic_info,
    fetch_syllabus_details,
    fetch_student_exams,
)


@tool(
    name="get_course",
    description="Fetch general details about a course (ECTS points, method of passing, assessment criteria).",
    tags={"courses"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
    timeout=30,
)
async def get_course(
    course_id: str,
    term_id: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    try:
        await ctx.info(f"Fetching course information for: {course_id}")
        resolved_term = await asyncio.to_thread(resolve_term_id, term_id)
        raw_info = await asyncio.to_thread(fetch_course_basic_info, course_id, resolved_term)
        return CourseBasicInfo(**raw_info).model_dump()
    except Exception as exc:
        await ctx.error(f"Failed to fetch course: {exc}")
        raise ToolError(f"Failed to fetch course: {exc}") from exc


@tool(
    name="get_syllabus",
    description="Fetch full syllabus details of a course edition: description, bibliography, and course units with class types.",
    tags={"courses"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
    timeout=30,
)
async def get_syllabus(
    course_id: str,
    term_id: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    try:
        resolved_term = await asyncio.to_thread(resolve_term_id, term_id)
        await ctx.info(f"Fetching syllabus for {course_id} in {resolved_term}")

        raw_syllabus, classtypes = await asyncio.gather(
            asyncio.to_thread(fetch_syllabus_details, course_id, resolved_term),
            asyncio.to_thread(fetch_classtypes_index),
        )

        resolved_units = []
        for unit in raw_syllabus.get("course_units", []):
            classtype_id = unit.get("classtype_id")
            resolved_class_name = None
            if classtype_id and classtype_id in classtypes:
                resolved_class_name = extract_localized_str(classtypes[classtype_id].get("name"))

            unit_id_raw = unit.get("id")
            unit_id = int(unit_id_raw) if unit_id_raw is not None else 1

            resolved_units.append(
                CourseUnitInfo(
                    unit_id=unit_id,
                    classtype_id=classtype_id or "unknown",
                    class_type_name=resolved_class_name,
                    topics=extract_localized_str(unit.get("topics")),
                    learning_outcomes=extract_localized_str(unit.get("learning_outcomes")),
                    assessment_criteria=extract_localized_str(unit.get("assessment_criteria")),
                )
            )

        syllabus = CourseSyllabus(
            course_id=raw_syllabus.get("course_id") or course_id,
            name=raw_syllabus.get("name") or "unknown",
            term_id=resolved_term,
            description=raw_syllabus.get("description"),
            prerequisites=raw_syllabus.get("prerequisites"),
            bibliography=raw_syllabus.get("bibliography"),
            course_units=resolved_units,
        )
        return syllabus.model_dump()
    except Exception as exc:
        await ctx.error(f"Failed to fetch syllabus: {exc}")
        raise ToolError(f"Failed to fetch syllabus: {exc}") from exc


@tool(
    name="get_exams",
    description="Check scheduled exam dates and groups for the authenticated student.",
    tags={"courses"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
    timeout=30,
)
async def get_exams(ctx: Context = CurrentContext()) -> list[dict]:
    try:
        await ctx.info("Fetching student exam calendar.")
        raw_exams = await asyncio.to_thread(fetch_student_exams)

        exams = []
        for exam in raw_exams:
            course = exam.get("course") or {}
            term = exam.get("term") or {}

            groups_details = []
            for grp in exam.get("groups", []):
                if "exam_start" in grp and "exam_end" in grp:
                    groups_details.append(
                        ExamGroupDetails(
                            group_number=grp.get("number") or 1,
                            exam_start=grp["exam_start"],
                            exam_end=grp["exam_end"],
                            capacity=grp.get("capacity"),
                        )
                    )

            term_id = term.get("id") or "0000Z"

            exams.append(
                StudentExam(
                    exam_id=exam.get("id") or "unknown",
                    course_id=course.get("id") or "unknown",
                    course_name=extract_localized_str(course.get("name")) or "unknown",
                    term_id=term_id,
                    examination_session_id=exam.get("examination_session_id"),
                    groups=groups_details,
                ).model_dump()
            )
        return exams
    except Exception as exc:
        await ctx.error(f"Failed to fetch exams: {exc}")
        raise ToolError(f"Failed to fetch exams: {exc}") from exc


@tool(
    name="resolve_classtypes",
    description="Fetch the dictionary mapping course class type IDs to their localized names.",
    tags={"courses"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
    timeout=15,
)
async def resolve_classtypes(ctx: Context = CurrentContext()) -> dict:
    try:
        await ctx.info("Fetching class types index.")
        raw_types = await asyncio.to_thread(fetch_classtypes_index)
        resolved = {}
        for ct_id, val in raw_types.items():
            resolved[ct_id] = extract_localized_str(val.get("name")) or ct_id
        return resolved
    except Exception as exc:
        await ctx.error(f"Failed to resolve class types: {exc}")
        raise ToolError(f"Failed to resolve class types: {exc}") from exc
