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
