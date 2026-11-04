from datetime import datetime, timezone


def ensure_utc(value: datetime) -> datetime:
    """Normalize database datetimes to aware UTC values for API serialization."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def utc_isoformat(value: datetime) -> str:
    return ensure_utc(value).isoformat().replace("+00:00", "Z")
