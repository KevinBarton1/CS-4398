from app.config import (
    BPR_ALPHA,
    BPR_BETA,
    OFFPEAK_HOUR_END,
    OFFPEAK_HOUR_START,
    OFFPEAK_TIME_FACTOR,
    PEAK_HOURS_EVENING,
    PEAK_HOURS_MORNING,
    PEAK_TIME_FACTOR,
)


def bpr_adjusted_time(
    free_flow_minutes: float,
    flow: float,
    capacity: float,
) -> float:
    """Apply the Bureau of Public Roads link-performance function."""
    if capacity <= 0:
        raise ValueError("Road capacity must be positive.")
    if flow == 0:
        return free_flow_minutes
    return free_flow_minutes * (
        1 + BPR_ALPHA * (flow / capacity) ** BPR_BETA
    )


def time_of_day_factor(hour: int) -> float:
    bounded_hour = max(0, min(23, int(hour)))
    if (
        PEAK_HOURS_MORNING[0]
        <= bounded_hour
        <= PEAK_HOURS_MORNING[1]
        or PEAK_HOURS_EVENING[0]
        <= bounded_hour
        <= PEAK_HOURS_EVENING[1]
    ):
        return PEAK_TIME_FACTOR
    if (
        bounded_hour < OFFPEAK_HOUR_END
        or bounded_hour >= OFFPEAK_HOUR_START
    ):
        return OFFPEAK_TIME_FACTOR
    return 1.0
