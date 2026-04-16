from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def start_of_day(dt: datetime | None = None) -> datetime:
    d = dt or utc_now()
    return d.replace(hour=0, minute=0, second=0, microsecond=0)


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"