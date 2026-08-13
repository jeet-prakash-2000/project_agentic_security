from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def ist_now():
    return datetime.now(IST)


def format_ist(ts, fmt="%Y-%m-%d %H:%M"):
    if not ts:
        return "—"
    return datetime.fromtimestamp(float(ts), tz=IST).strftime(fmt)
