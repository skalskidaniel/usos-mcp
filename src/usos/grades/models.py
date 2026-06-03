from pydantic import BaseModel, Field


class GradeEntry(BaseModel):
    """A single grade from the USOS API."""

    course_id: str = Field(description="ID/code of the course (e.g. S1Inf1>ALG)")
    course_name: str | None = Field(
        default=None, description="Name of the course in English/Polish (if available)"
    )
    term_id: str | None = Field(
        default=None, description="The academic term ID (e.g. 2023Z)"
    )
    type: str = Field(
        description="Grade type: 'course' (final grade for the course) or 'unit' (grade for a course unit)"
    )
    course_unit_id: int | None = Field(
        default=None, description="The unique numeric ID of the course unit component (if type is 'unit')"
    )
    value_symbol: str | None = Field(
        default=None, description="The grade value symbol (e.g. '5.0', '3.5', 'ZAL')"
    )
    value_description: str | None = Field(
        default=None, description="Human-readable grade description (e.g. 'Very good')"
    )
    passes: bool | None = Field(
        default=None,
        description="Whether this grade constitutes passing the course/unit",
    )
    counts_into_average: bool | None = Field(
        default=None, description="Whether this grade counts towards the ECTS GPA"
    )
    exam_session_number: int | None = Field(
        default=1, description="The exam session/attempt number (usually 1 or 2)"
    )
    grade_type_id: str | None = Field(
        default=None, description="USOS internal grade type ID (e.g. STD, EGZ-STD)"
    )
    date_modified: str | None = Field(
        default=None,
        description="Timestamp when the grade was last modified (YYYY-MM-DD HH:MM)",
    )
    comment: str | None = Field(
        default=None, description="Additional comment from the lecturer, if any"
    )


class GradeAverage(BaseModel):
    """Result of an ECTS-weighted GPA calculation."""

    average: float | None = Field(default=None, ge=2.0, le=6.0)
    total_ects: float = Field(default=0.0, ge=0.0)
    grades_counted: int = Field(default=0, ge=0)
    grades_skipped: int = Field(default=0, ge=0)
    term_ids: list[str] = Field(default_factory=list)
