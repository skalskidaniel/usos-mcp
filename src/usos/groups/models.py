from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints


class StudentGroup(BaseModel):
    """A class group that the student belongs to."""

    course_unit_id: Annotated[int, Field(gt=0)] = Field(
        description="The unique ID of the course unit (e.g. 12345)."
    )
    group_number: Annotated[int, Field(gt=0)] = Field(
        description="The group number, unique within the course unit (e.g. 1, 2)."
    )
    class_type: str | None = Field(
        default=None,
        description="The localized type of class (e.g. 'Lecture', 'Laboratory')."
    )
    class_type_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = Field(
        default=None,
        description="USOS class type code (e.g. 'WYK', 'LAB')."
    )
    course_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = Field(
        default=None,
        description="The unique code of the course (e.g. 'INFO-1-1')."
    )
    course_name: str | None = Field(
        default=None,
        description="The localized name of the course."
    )
    term_id: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{4}[ZL]$")] | None = Field(
        default=None,
        description="The academic term ID (e.g. '2023Z')."
    )


class GroupParticipant(BaseModel):
    """Information about a student in a class group (excluding the current user)."""

    id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="The unique ID of the student user."
    )
    first_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="The student's first name."
    )
    last_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="The student's last name."
    )
