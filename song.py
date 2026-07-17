import asyncio
import yt_dlp

from audio import YTDLSource
from config import make_ytdl, YTDL_ENTRY_OPTS
from utils import fmt_seconds


class Song:
    def __init__(
        self,
        url: str,
        title: str,
        duration: int,
        requester: str,
        thumbnail: str = "",
        webpage_url: str = "",
    ):
        self.url = url
        self.title = title
        self.duration = duration
        self.requester = requester
        self.thumbnail = thumbnail
        self.webpage_url = webpage_url
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
        return cls(url, title, duration, requester, thumbnail, webpage_url)

    def audio_source(self):
        return YTDLSource(self.url)

    def fmt_duration(self) -> str:
        return fmt_seconds(self.duration)

    def _title_link(self) -> str:
        return f"[{self.title}]({self.webpage_url})" if self.webpage_url else self.title

    def now_playing_embed(self, progress: str | None = None) -> "discord.Embed":
        import discord
        from config import COLOUR

        embed = discord.Embed(
            title="ON AIR",
            description=self._title_link(),
            colour=COLOUR,
        )
        embed.add_field(name="Duration", value=self.fmt_duration(), inline=True)
        embed.add_field(name="Requested by", value=self.requester, inline=True)
        if progress:
            embed.add_field(name="Progress", value=progress, inline=False)
        embed.set_footer(text="The globalists don't want you listening to this.")
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        return embed

    def queued_embed(self, position: int) -> "discord.Embed":
        import discord
        from config import COLOUR

        embed = discord.Embed(
            title=f"LOCKED AND LOADED — POSITION #{position}",
            description=self._title_link(),
            colour=COLOUR,
        )
        embed.add_field(name="Duration", value=self.fmt_duration(), inline=True)
        embed.add_field(name="Requested by", value=self.requester, inline=True)
        embed.set_footer(text="They can't stop the signal.")
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        return embed
