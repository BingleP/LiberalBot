import math


def fmt_seconds(s: int) -> str:
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def progress_bar(elapsed: float, duration: int, width: int = 12) -> str:
    if duration <= 0:
        return "LIVE"
    progress = min(elapsed / duration, 1.0)
    filled = int(progress * width)
    bar = "\u2593" * filled + "\u2591" * (width - filled)
    return f"`{bar}` `{fmt_seconds(int(elapsed))} / {fmt_seconds(duration)}`"


def total_duration(seconds: int) -> str:
    return fmt_seconds(seconds)
