import asyncio
from collections import deque

import discord
from discord.ext import commands


bot: commands.Bot | None = None
bot_loop: asyncio.AbstractEventLoop | None = None


class GuildState:
    def __init__(self):
        self.queue: deque = deque()
        self.current = None
        self.loop_one: bool = False
        self.loop_queue: bool = False
        self.is_paused: bool = False
        self._text_channel: discord.TextChannel | None = None
        self.now_playing_message: discord.Message | None = None
        self.last_error_message: discord.Message | None = None
        self.song_start_time: float = 0.0
        self.progress_task: asyncio.Task | None = None

    def set_channel(self, channel: discord.TextChannel):
        self._text_channel = channel

    async def send(self, embed: discord.Embed | None = None, content: str | None = None):
        if self._text_channel:
            return await self._text_channel.send(content=content, embed=embed)
        return None

    def cleanup(self):
        if self.progress_task and not self.progress_task.done():
            self.progress_task.cancel()
            self.progress_task = None
        self.now_playing_message = None
        self.last_error_message = None


states: dict[int, GuildState] = {}


def get_state(guild_id: int) -> GuildState:
    if guild_id not in states:
        states[guild_id] = GuildState()
    return states[guild_id]
