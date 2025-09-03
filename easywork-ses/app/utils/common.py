def clean_dict(d: dict):
    return {k: v for k, v in d.items() if not (isinstance(v, str) and v.strip() == "")}


def to_hhmm(value) -> str:
    if value is None:
        return "00:00"

    # timedelta（MySQL TIME）
    if hasattr(value, "total_seconds"):
        total_seconds = int(value.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}"

    # datetime.time
    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")

    # 字符串
    if isinstance(value, str):
        return value[:5]  # 只取HH:MM

    return str(value)
