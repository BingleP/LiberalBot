import asyncio
import time

import yt_dlp

from audio import YTDLSource
from config import make_ytdl, MAX_STREAM_URL_AGE, YTDL_ENTRY_OPTS
from persona import PersonaEvents, say_embed
from utils import fmt_seconds


def _best_audio_format(entry: dict) -> dict | None:
    """Pick the best audio-only format from a yt-dlp entry."""
    formats = entry.get("formats") or []
    audio_formats = [f for f in formats if f.get("vcodec") == "none" or f.get("acodec") != "none"]
    if not audio_formats:
        # Fallback to any format if no pure audio format is found.
        audio_formats = formats
    if not audio_formats:
        return None

    # Prefer higher bitrate / larger file size.
    def sort_key(fmt: dict) -> tuple:
        abr = fmt.get("abr") or 0
        filesize = fmt.get("filesize") or fmt.get("filesize_approx") or 0
        return (bool(fmt.get("url")), abr, filesize)

    audio_formats.sort(key=sort_key, reverse=True)
    return audio_formats[0]


def _extract_stream_info(entry: dict) -> tuple[str, dict[str, str]]:
    """Return the best audio stream URL and its HTTP headers."""
    fmt = _best_audio_format(entry)
    if fmt is None:
        # Fallback to the top-level URL if no formats are available.
        url = entry.get("url") or entry.get("webpage_url", "")
        return url, {}

    url = fmt.get("url", "")
    headers = fmt.get("http_headers") or {}
    if not headers:
        # yt-dlp may place headers at the entry level for some extractors.
        headers = entry.get("http_headers") or {}
    return url, headers


class Song:
    def __init__(
        self,
        url: str,
        title: str,
        duration: int,
        requester: str,
        thumbnail: str = "",
        webpage_url: str = "",
        stream_url: str = "",
        stream_headers: dict[str, str] | None = None,
    ):
        self.url = url
        self.title = title
        self.duration = duration
        self.requester = requester
        self.thumbnail = thumbnail
        self.webpage_url = webpage_url
        self.stream_url = stream_url
        self.stream_headers = stream_headers or {}
        self.extracted_at = time.time()
        self.retry_count = 0
        self.max_retries = 3
        self.last_error = None

    @classmethod
    async def from_query(cls, query: str, requester: str) -> list["Song"]:
        loop = asyncio.get_event_loop()
        ytdl = make_ytdl()
        entry_ytdl = yt_dlp.YoutubeDL(YTDL_ENTRY_OPTS)

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))

        if "entries" in data:
            songs = []
            for entry in data["entries"]:
                if not entry:
                    continue
                entry = await loop.run_in_executor(
                    None,
                    lambda e=entry: entry_ytdl.extract_info(
                        e.get("url") or e.get("webpage_url") or e["id"],
                        download=False,
                    ),
                )
                songs.append(cls._from_entry(entry, requester))
            return songs

        return [cls._from_entry(data, requester)]

    @classmethod
    def _from_entry(cls, entry: dict, requester: str) -> "Song":
        url = entry.get("url") or entry.get("webpage_url", "")
        title = entry.get("title", "Unknown")
        duration = entry.get("duration") or 0
        thumbnail = entry.get("thumbnail", "")
        webpage_url = entry.get("webpage_url", "")
        stream_url, stream_headers = _extract_stream_info(entry)
        return cls(
            url,
            title,
            duration,
            requester,
            thumbnail,
            webpage_url,
            stream_url,
            stream_headers,
        )

    async def get_stream_url(self, force: bool = False) -> tuple[str, dict[str, str]]:
        """Return the stream URL and headers, re-extracting if stale or forced."""
        age = time.time() - self.extracted_at
        if not force and self.stream_url and age < MAX_STREAM_URL_AGE:
            return self.stream_url, self.stream_headers

        loop = asyncio.get_event_loop()
        entry_ytdl = yt_dlp.YoutubeDL(YTDL_ENTRY_OPTS)
        try:
            entry = await loop.run_in_executor(
                None,
                lambda: entry_ytdl.extract_info(
                    self.webpage_url or self.url,
                    download=False,
                ),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to re-extract stream URL: {e}") from e

        self.stream_url, self.stream_headers = _extract_stream_info(entry)
        self.extracted_at = time.time()
        return self.stream_url, self.stream_headers

    def audio_source(self) -> YTDLSource:
        return YTDLSource(self.stream_url, self.stream_headers)

    def fmt_duration(self) -> str:
        return fmt_seconds(self.duration)

    def _title_link(self) -> str:
        return f"[{self.title}]({self.webpage_url})" if self.webpage_url else self.title

    def now_playing_embed(self, progress: str | None = None) -> "discord.Embed":
        import discord
        from config import COLOUR

        title, description, footer = say_embed(
            PersonaEvents.NOW_PLAYING, title=self.title, requester=self.requester
        )
        embed = discord.Embed(
            title=title or "ON AIR",
            description=self._title_link(),
            colour=COLOUR,
        )
        embed.add_field(name="Duration", value=self.fmt_duration(), inline=True)
        embed.add_field(name="Requested by", value=self.requester, inline=True)
        if progress:
            embed.add_field(name="Progress", value=progress, inline=False)
        if footer:
            embed.set_footer(text=footer)
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        return embed

    def queued_embed(self, position: int) -> "discord.Embed":
        import discord
        from config import COLOUR

        title, description, footer = say_embed(
            PersonaEvents.QUEUED, title=self.title, position=position, requester=self.requester
        )
        embed = discord.Embed(
            title=title or f"Queued — Position #{position}",
            description=self._title_link(),
            colour=COLOUR,
        )
        embed.add_field(name="Duration", value=self.fmt_duration(), inline=True)
        embed.add_field(name="Requested by", value=self.requester, inline=True)
        if footer:
            embed.set_footer(text=footer)
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        return embed
