import logging
from logging.handlers import RotatingFileHandler

# ── BOT IDENTITY ────────────────────────────────────────────────────────────
COLOUR = 0x9B59B6  # purple accent

# ── PERSONA ─────────────────────────────────────────────────────────────────
PERSONA_ENABLED = True

# ── WARM-UP / STREAM URL FRESHNESS ──────────────────────────────────────────
WARMUP_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
MAX_STREAM_URL_AGE = 30 * 60  # 30 minutes

# ── PATHS ───────────────────────────────────────────────────────────────────
YT_COOKIE_FILE = "/home/bingle/Documents/www.youtube.com_cookies.txt"

# ── FFMPEG OPTIONS ──────────────────────────────────────────────────────────
FFMPEG_BEFORE_OPTS = (
    "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    ' -user_agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"'
    ' -headers "Referer: https://www.youtube.com\\r\\n"'
    f' -cookies "{YT_COOKIE_FILE}"'
)
FFMPEG_OPTS = {"options": "-vn", "before_options": FFMPEG_BEFORE_OPTS}

# ── YT-DLP OPTIONS ──────────────────────────────────────────────────────────
YTDL_OPTS = {
    "format": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "noplaylist": True,
    "extract_flat": "in_playlist",
    "playlistend": 25,
    "source_address": "0.0.0.0",
    "cookiefile": YT_COOKIE_FILE,
    "extractor_args": {"youtube": {"player_client": ["web", "ios"]}},
    "remote_components": ["ejs:github"],
}

YTDL_ENTRY_OPTS = {**YTDL_OPTS, "extract_flat": False, "noplaylist": True}

# ── LOGGING ─────────────────────────────────────────────────────────────────
logger = logging.getLogger("liberalbot")
logger.setLevel(logging.INFO)
_handler = RotatingFileHandler("bot.log", maxBytes=10 * 1024 * 1024, backupCount=5)
_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(_handler)


def make_ytdl():
    import yt_dlp
    return yt_dlp.YoutubeDL(YTDL_OPTS)
