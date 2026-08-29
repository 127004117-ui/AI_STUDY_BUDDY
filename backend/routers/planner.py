"""
Smart Revision Planner router.
Accepts exam date + topics and builds a day-by-day revision schedule.
"""

from fastapi import APIRouter, HTTPException
from datetime import date, timedelta
import math

from models.schemas import PlannerRequest, PlannerResponse, DayPlan

router = APIRouter()


@router.post("/schedule", response_model=PlannerResponse, summary="Generate revision schedule")
async def generate_schedule(req: PlannerRequest):
    """
    Given an exam date, a list of topics, and daily available study hours,
    return an optimized day-by-day revision plan.

    - Topics are distributed evenly across available days.
    - The last 2 days (if available) are reserved for full revision.
    - Topics are cycled for spaced repetition on longer schedules.
    """
    today = date.today()
    if req.exam_date <= today:
        raise HTTPException(
            status_code=400,
            detail="Exam date must be in the future.",
        )

    total_days = (req.exam_date - today).days
    topics = req.topics
    num_topics = len(topics)

    if total_days < 1:
        raise HTTPException(status_code=400, detail="Not enough days before exam.")

    daily_plan: list[DayPlan] = []

    # Reserve last 2 days for revision (if we have more than 3 days)
    revision_buffer = min(2, total_days - 1)
    study_days = total_days - revision_buffer

    # Topics per day (at least 1)
    topics_per_day = max(1, math.ceil(num_topics / max(study_days, 1)))

    # Build schedule
    topic_index = 0
    for day_offset in range(total_days):
        current_date = today + timedelta(days=day_offset)
        is_revision_day = day_offset >= study_days

        if is_revision_day:
            day_topics = ["🔁 Full Revision: " + ", ".join(topics[:3]) + (" + more" if num_topics > 3 else "")]
            hours = req.daily_hours
        else:
            # Assign topics for the day (with wrap-around for spaced repetition)
            day_topics = []
            for _ in range(topics_per_day):
                day_topics.append(topics[topic_index % num_topics])
                topic_index += 1

            # On longer plans, add a light review of an earlier topic
            if study_days > num_topics and day_offset > 0:
                review_topic = topics[(topic_index - topics_per_day - 1) % num_topics]
                if review_topic not in day_topics:
                    day_topics.append(f"📖 Review: {review_topic}")

            hours = req.daily_hours

        daily_plan.append(
            DayPlan(
                date=current_date.strftime("%Y-%m-%d"),
                topics=day_topics,
                hours=hours,
            )
        )

    message = (
        f"📅 {total_days}-day plan covering {num_topics} topic(s). "
        f"Study {req.daily_hours}h/day. "
        f"Last {revision_buffer} day(s) reserved for full revision. Good luck! 🎯"
    )

    return PlannerResponse(
        total_days=total_days,
        daily_plan=daily_plan,
        message=message,
    )
