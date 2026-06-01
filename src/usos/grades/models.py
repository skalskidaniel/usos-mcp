from pydantic import BaseModel, Field


class GradeEntry(BaseModel):
    """A single grade from the USOS API."""
    value_symbol: str | None = None
    value_description: dict[str, str] | str | None = None
    passes: bool | None = None
    counts_into_average: bool | None = None
    exam_id: int | None = Field(default=None, ge=0)
    exam_session_number: int | None = Field(default=None, ge=1)
    date_modified: str | None = None
    date_acquisition: str | None = None
    grade_type_id: str | None = None
    comment: str | None = None


class GradeAverage(BaseModel):
    """Result of an ECTS-weighted GPA calculation."""
    average: float | None = Field(default=None, ge=2.0, le=6.0)
    total_ects: float = Field(default=0.0, ge=0.0)
    grades_counted: int = Field(default=0, ge=0)
    grades_skipped: int = Field(default=0, ge=0)
    term_ids: list[str] = Field(default_factory=list)
