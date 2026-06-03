from typing import Annotated
from pydantic import BaseModel, Field, field_validator, StringConstraints

class AcademicTitles(BaseModel):
    """Academic titles of an employee/lecturer."""
    before: str | None = Field(default=None, description="Title before the name (e.g. dr, dr hab.)")
    after: str | None = Field(default=None, description="Title after the name (e.g. PhD)")

    @field_validator("before", "after")
    @classmethod
    def clean_spaces(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            return v if v else None
        return None

class Lecturer(BaseModel):
    """Details of a lecturer/employee."""
    id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Unique USOS identifier of the lecturer"
    )
    first_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="First name"
    )
    last_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Last name"
    )
    titles: AcademicTitles | None = Field(default=None, description="Academic titles")
    email: str | None = Field(default=None, description="Institutional email address")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                return None
            import re
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
                raise ValueError(f"Invalid email format: {v}")
            return v
        return None

class LecturerGroup(BaseModel):
    """A class group taught by the lecturer."""
    course_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Course code/identifier"
    )
    course_name: dict[str, str] | str | None = Field(default=None, description="Localized course name")
    term_id: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{4}[ZL]$")] | None = Field(
        default=None, description="Academic term ID"
    )
    group_number: Annotated[int, Field(gt=0)] | None = Field(
        default=None, description="Class group number"
    )
    class_type_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = Field(
        default=None, description="USOS class type code"
    )
