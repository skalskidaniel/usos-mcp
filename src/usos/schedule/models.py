from datetime import date, datetime

from pydantic import BaseModel, Field



class Activity(BaseModel):
    type: str
    start_time: datetime
    end_time: datetime
    name: dict[str, str] | str
    url: str | None = None


class ClassgroupActivity(Activity):
    course_id: str | None = None
    course_unit_id: int | None = None
    course_name: dict[str, str] | str | None = None
    classtype_name: dict[str, str] | str | None = None
    building_name: dict[str, str] | str | None = None
    room_number: str | None = None
    room_id: str | None = None
    lecturer_ids: list[int | str] = Field(default_factory=list)
    group_number: int | None = None
    frequency: str | None = None


class ExamActivity(Activity):
    course_id: str | None = None
    course_name: dict[str, str] | str | None = None
    building_name: dict[str, str] | str | None = None
    room_number: str | None = None
    room_id: str | None = None


class CalendarEvent(BaseModel):
    id: str
    name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    type: str | None = None
    is_day_off: bool = False


class Term(BaseModel):
    id: str
    name: dict[str, str] | str
    start_date: date
    end_date: date
    finish_date: str
    is_active: bool = False


class Faculty(BaseModel):
    id: str
    name: dict[str, str] | str
