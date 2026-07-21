from enum import Enum


class MediaError(Enum):
    UNAVAILABLE = "unavailable"
    REGION_LOCKED = "region_locked"
    AGE_RESTRICTED = "age_restricted"
    AUTH_FAILED = "auth_failed"
    NETWORK_ERROR = "network_error"
    FORMAT_ERROR = "format_error"
    STREAM_ERROR = "stream_error"
    STALE_URL = "stale_url"
    UNKNOWN = "unknown"


RETRYABLE_ERRORS = {
    MediaError.NETWORK_ERROR,
    MediaError.STREAM_ERROR,
    MediaError.UNKNOWN,
    MediaError.STALE_URL,
}


def classify_error(error: Exception) -> MediaError:
    msg = str(error).lower()
    if "sign in" in msg or ("age" in msg and "verify" in msg):
        return MediaError.AGE_RESTRICTED
    if "unavailable" in msg or "removed" in msg or "deleted" in msg or "video not found" in msg:
        return MediaError.UNAVAILABLE
    if "region" in msg or "country" in msg or ("blocked" in msg and "age" not in msg):
        return MediaError.REGION_LOCKED
    if "cookie" in msg or "auth" in msg or "http error 401" in msg:
        return MediaError.AUTH_FAILED
    if "http error 403" in msg or "forbidden" in msg or "expired" in msg or "signature" in msg:
        return MediaError.STALE_URL
    if "timeout" in msg or "connection" in msg or "network" in msg or "eof" in msg or "empty" in msg:
        return MediaError.NETWORK_ERROR
    if "format" in msg or "no suitable" in msg or "no compatible" in msg:
        return MediaError.FORMAT_ERROR
    if "exit code" in msg or "process" in msg or "audio source" in msg:
        return MediaError.STREAM_ERROR
    return MediaError.UNKNOWN


def user_friendly_error(err_type: MediaError, title: str, detail: str = "") -> str:
    messages = {
        MediaError.UNAVAILABLE: f"**{title}** is no longer available on YouTube. Try a different track with `/play`.",
        MediaError.REGION_LOCKED: f"**{title}** isn't available in your region. Try a different song.",
        MediaError.AGE_RESTRICTED: f"**{title}** is age-restricted and cannot be played by the bot.",
        MediaError.AUTH_FAILED: f"Failed to authenticate with YouTube for **{title}**. The bot admin needs to refresh cookies.",
        MediaError.FORMAT_ERROR: f"No playable audio format found for **{title}**. Try a different song.",
        MediaError.STREAM_ERROR: f"Failed to stream **{title}**.",
        MediaError.NETWORK_ERROR: f"Network error while loading **{title}**. Check the connection and try again.",
        MediaError.STALE_URL: f"**{title}**'s stream URL expired. Retrying with a fresh one.",
        MediaError.UNKNOWN: f"Failed to play **{title}**. {detail}" if detail else f"Failed to play **{title}**.",
    }
    return messages.get(err_type, messages[MediaError.UNKNOWN])
