import asyncio
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.tools import tool
from fastmcp.exceptions import ToolError

from usos.utils import resolve_term_id, extract_localized_str, fetch_classtypes_index
from .models import (
    CourseInfo,
    StudentExam,
    CourseUnitInfo,
    ExamGroupDetails,
)
from .utils import (
    fetch_course_basic_info,
    fetch_syllabus_details,
    fetch_student_exams,
)


@tool(
    name="get_course_info",
    description="Fetch comprehensive details about a course edition (ECTS credits, passing status, description, bibliography, assessment criteria, and course units).",
    tags={"courses"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
    timeout=30,
)
async def get_course_info(
    course_id: str,
    term_id: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """
    Args:
        course_id: The ID of the course to fetch information for.
        term_id: Optional ID of the academic term. If omitted, the system will try to auto-resolve to the current term.
    """
    try:
        from usos.utils import resolve_course_and_term
        course_id, term_id = await asyncio.to_thread(resolve_course_and_term, course_id, term_id)
        resolved_term = await asyncio.to_thread(resolve_term_id, term_id)
        await ctx.info(f"Fetching course info for {course_id} in {resolved_term}")

        raw_info, raw_syllabus, classtypes = await asyncio.gather(
            asyncio.to_thread(fetch_course_basic_info, course_id, resolved_term),
            asyncio.to_thread(fetch_syllabus_details, course_id, resolved_term),
            asyncio.to_thread(fetch_classtypes_index),
        )

        resolved_units = []
        for unit in raw_syllabus.get("course_units", []):
            classtype_id = unit.get("classtype_id")
            resolved_class_name = None
            if classtype_id and classtype_id in classtypes:
                resolved_class_name = extract_localized_str(
                    classtypes[classtype_id].get("name")
                )

            unit_id_raw = unit.get("id")
            unit_id = int(unit_id_raw) if unit_id_raw is not None else 1

            resolved_units.append(
                CourseUnitInfo(
                    unit_id=unit_id,
                    classtype_id=classtype_id or "unknown",
                    class_type_name=resolved_class_name,
                    topics=extract_localized_str(unit.get("topics")),
                    learning_outcomes=extract_localized_str(
                        unit.get("learning_outcomes")
                    ),
                    assessment_criteria=extract_localized_str(
                        unit.get("assessment_criteria")
                    ),
                )
            )

        course_info = CourseInfo(
            course_id=course_id,
            name=raw_info.get("name") or raw_syllabus.get("name") or "unknown",
            term_id=resolved_term,
            ects_credits=raw_info.get("ects_credits"),
            passing_status=raw_info.get("passing_status"),
            description=raw_syllabus.get("description"),
            prerequisites=raw_syllabus.get("prerequisites"),
            bibliography=raw_syllabus.get("bibliography"),
            assessment_criteria=raw_info.get("assessment_criteria") or raw_syllabus.get("assessment_criteria"),
            course_units=resolved_units,
        )
        return course_info.model_dump()
    except Exception as exc:
        await ctx.error(f"Failed to fetch course info: {exc}")
        raise ToolError(f"Failed to fetch course info: {exc}") from exc


@tool(
    name="get_exams",
    description="Check scheduled exam dates and groups for the authenticated student. Defaults to upcoming exams only.",
    tags={"courses"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
    timeout=30,
)
async def get_exams(
    include_past: bool = False,
    ctx: Context = CurrentContext(),
) -> list[dict]:
    """
    Args:
        include_past: If True, includes past exams. If False, only returns upcoming exams.
    """
    try:
        await ctx.info("Fetching student exam calendar.")
        raw_exams = await asyncio.to_thread(fetch_student_exams)

        from datetime import datetime
        now = datetime.now()

        exams = []
        for exam in raw_exams:
            course = exam.get("course") or {}
            term = exam.get("term") or {}

            groups_details = []
            for grp in exam.get("groups", []):
                if "exam_start" in grp and "exam_end" in grp:
                    exam_start_str = grp["exam_start"]
                    if not include_past:
                        try:
                            start_dt = datetime.strptime(exam_start_str, "%Y-%m-%d %H:%M:%S")
                            if start_dt < now:
                                continue
                        except Exception:
                            pass

                    groups_details.append(
                        ExamGroupDetails(
                            group_number=grp.get("number") or 1,
                            exam_start=grp["exam_start"],
                            exam_end=grp["exam_end"],
                            capacity=grp.get("capacity"),
                        )
                    )

            if not groups_details and not include_past:
                continue

            term_id = term.get("id") or "0000Z"

            exams.append(
                StudentExam(
                    exam_id=exam.get("id") or "unknown",
                    course_id=course.get("id") or "unknown",
                    course_name=extract_localized_str(course.get("name")) or "unknown",
                    term_id=term_id,
                    groups=groups_details,
                ).model_dump()
            )
        return exams
    except Exception as exc:
        await ctx.error(f"Failed to fetch exams: {exc}")
        raise ToolError(f"Failed to fetch exams: {exc}") from exc

