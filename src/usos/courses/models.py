from typing import Annotated
from pydantic import BaseModel, Field, field_validator, model_validator, StringConstraints


class CourseBasicInfo(BaseModel):
    course_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Unique code/identifier of the course"
    )
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Name of the course"
    )
    ects_credits: Annotated[float, Field(ge=0.0, le=60.0)] | None = Field(
        None, description="ECTS credits rewarded for completing the course"
    )
    assessment_criteria: str | None = Field(None, description="Criteria for assessing/passing the course")
    passing_status: str | None = Field(None, description="Authenticated user's passing status")

    @field_validator("passing_status")
    @classmethod
    def validate_passing_status(cls, v: str | None) -> str | None:
        if v is not None:
            valid = {"passed", "failed", "not_yet_passed"}
            if v not in valid:
                raise ValueError(f"passing_status must be one of {valid}")
        return v


class CourseUnitInfo(BaseModel):
    unit_id: Annotated[int, Field(gt=0)] = Field(description="Unique ID of the course unit")
    classtype_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Short ID of the class type"
    )
    class_type_name: str | None = Field(None, description="Resolved human-readable name of the class type")
    topics: str | None = Field(None, description="Topics/programme contents covered in the class")
    learning_outcomes: str | None = Field(None, description="Expected learning outcomes for the unit")
    assessment_criteria: str | None = Field(None, description="Assessment criteria for this unit")


class CourseSyllabus(BaseModel):
    course_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Unique code/identifier of the course"
    )
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Name of the course"
    )
    term_id: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{4}[A-Za-z0-9_\-\/]*$")] = Field(
        description="Term ID of the syllabus edition"
    )
    description: str | None = Field(None, description="General description of the course edition")
    prerequisites: str | None = Field(None, description="Prerequisites or requirements for taking the course")
    bibliography: str | None = Field(None, description="Bibliography/literature list")
    course_units: list[CourseUnitInfo] = Field(default_factory=list, description="Associated course units")


class ExamGroupDetails(BaseModel):
    group_number: Annotated[int, Field(gt=0)] = Field(description="Exam group sequence number")
    exam_start: str = Field(description="Exam start date and time")
    exam_end: str = Field(description="Exam end date and time")
    capacity: Annotated[int, Field(gt=0)] | None = Field(None, description="Maximum seats in this exam group")

    @model_validator(mode="after")
    def validate_dates(self) -> "ExamGroupDetails":
        from datetime import datetime
        try:
            # Replace space with T to normalize ISO strings if needed
            start_str = self.exam_start.replace(" ", "T")
            end_str = self.exam_end.replace(" ", "T")
            start = datetime.fromisoformat(start_str)
            end = datetime.fromisoformat(end_str)
            if start >= end:
                raise ValueError("exam_start must be before exam_end")
        except (ValueError, TypeError) as exc:
            if isinstance(exc, ValueError) and "exam_start must be before exam_end" in str(exc):
                raise ValueError("exam_start must be before exam_end") from exc
        return self


class StudentExam(BaseModel):
    exam_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Unique identifier of the exam"
    )
    course_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Course code/identifier associated with the exam"
    )
    course_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Name of the course"
    )
    term_id: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{4}[A-Za-z0-9_\-\/]*$")] = Field(
        description="Term ID of the exam"
    )
    examination_session_id: str | None = Field(None, description="Exam session identifier")
    groups: list[ExamGroupDetails] = Field(default_factory=list, description="Details of the exam groups")
