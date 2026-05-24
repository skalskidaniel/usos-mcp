from usos.registry import registry


@registry.prompt(
    name="check_schedule_today",
    description="Guide for checking today's classes and presenting room/location details.",
)
def check_schedule_today() -> str:
    return "\n".join(
        [
            "Use this workflow to check today's student schedule.",
            "1. Call `get_my_schedule` with `days=1` and no start_date.",
            "2. If response contains error, explain authentication/config issue and suggest using setup prompt.",
            "3. Present activities ordered by start time.",
            "4. For each activity include: course name, class type, start-end time, building name, and room number.",
            "5. If there are no activities, say there are no classes today.",
        ]
    )


@registry.prompt(
    name="resolve_faculty_for_calendar",
    description="Guidance for resolving faculty_id before using calendar tools.",
)
def resolve_faculty_for_calendar() -> str:
    return "\n".join(
        [
            "Use this flow before calendar tools if faculty_id is unknown.",
            "1. Call `get_my_faculties` first.",
            "2. If exactly one faculty is returned, use its `id`.",
            "3. If multiple faculties are returned, ask the user to choose or call `search_faculties`.",
            "4. If no faculty is returned, use `search_faculties` with a name/code query.",
            "5. Call calendar tools with explicit faculty_id when ambiguity remains.",
        ]
    )
