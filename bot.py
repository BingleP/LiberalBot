import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
from collections import deque

# ── FFMPEG OPTIONS ──────────────────────────────────────────────────────────
FFMPEG_BEFORE_OPTS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTS = {"options": "-vn", "before_options": FFMPEG_BEFORE_OPTS}

YTDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "noplaylist": False,
    "extract_flat": "in_playlist",
    "source_address": "0.0.0.0",
}


def make_ytdl():
    return yt_dlp.YoutubeDL(YTDL_OPTS)


# ── SONG ────────────────────────────────────────────────────────────────────
class Song:
    def __init__(self, url: str, title: str, duration: int, requester: str):
        self.url = url
        self.title = title
        self.duration = duration
        self.requester = requester

    @classmethod
    async def from_query(cls, query: str, requester: str) -> list["Song"]:
        loop = asyncio.get_event_loop()
        ytdl = make_ytdl()

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))

        if "entries" in data:
            songs = []
            for entry in data["entries"]:
                if not entry:
                    continue
                entry = await loop.run_in_executor(
                    None,
                    lambda e=entry: make_ytdl().extract_info(
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
        return cls(url, title, duration, requester)

    def audio_source(self) -> discord.FFmpegPCMAudio:
        return discord.FFmpegPCMAudio(self.url, **FFMPEG_OPTS)

    def fmt_duration(self) -> str:
        m, s = divmod(self.duration, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# ── GUILD STATE ─────────────────────────────────────────────────────────────
class GuildState:
    def __init__(self):
        self.queue: deque[Song] = deque()
        self.current: Song | None = None
        self.loop_one: bool = False
        self.loop_queue: bool = False
        self._text_channel: discord.TextChannel | None = None

    def set_channel(self, channel: discord.TextChannel):
        self._text_channel = channel

    async def send(self, content: str):
        if self._text_channel:
            await self._text_channel.send(content)


# ── BOT ──────────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
states: dict[int, GuildState] = {}


def get_state(guild_id: int) -> GuildState:
    if guild_id not in states:
        states[guild_id] = GuildState()
    return states[guild_id]


# ── PLAYBACK ─────────────────────────────────────────────────────────────────
def play_next(vc: discord.VoiceClient, state: GuildState, error=None):
    if error:
        print(f"Playback error: {error}")

    if state.loop_one and state.current:
        source = discord.PCMVolumeTransformer(state.current.audio_source())
        vc.play(source, after=lambda e: play_next(vc, state, e))
        return

    if state.loop_queue and state.current:
        state.queue.append(state.current)

    if not state.queue:
        state.current = None
        asyncio.run_coroutine_threadsafe(state.send("Queue finished. See you next time!"), bot.loop)
        return

    song = state.queue.popleft()
    state.current = song
    source = discord.PCMVolumeTransformer(song.audio_source())
    vc.play(source, after=lambda e: play_next(vc, state, e))

    msg = f"Now playing: **{song.title}** `[{song.fmt_duration()}]` — requested by {song.requester}"
    asyncio.run_coroutine_threadsafe(state.send(msg), bot.loop)


async def ensure_voice(interaction: discord.Interaction) -> discord.VoiceClient | None:
    if interaction.user.voice is None:
        await interaction.followup.send("You need to be in a voice channel first.")
        return None

    vc: discord.VoiceClient | None = interaction.guild.voice_client

    if vc is None:
        vc = await interaction.user.voice.channel.connect()
    elif vc.channel != interaction.user.voice.channel:
        await vc.move_to(interaction.user.voice.channel)

    return vc


# ── SLASH COMMANDS ────────────────────────────────────────────────────────────
@bot.tree.command(name="play", description="Play a song or YouTube playlist")
@app_commands.describe(query="Song name, YouTube URL, or playlist URL")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()

    vc = await ensure_voice(interaction)
    if vc is None:
        return

    state = get_state(interaction.guild_id)
    state.set_channel(interaction.channel)

    songs = await Song.from_query(query, interaction.user.display_name)

    if not songs:
        await interaction.followup.send("Could not find anything for that query.")
        return

    for song in songs:
        state.queue.append(song)

    if len(songs) == 1:
        if vc.is_playing() or vc.is_paused():
            await interaction.followup.send(
                f"Added to queue: **{songs[0].title}** `[{songs[0].fmt_duration()}]`"
            )
        else:
            await interaction.followup.send(f"Loading **{songs[0].title}**...")
    else:
        await interaction.followup.send(f"Added **{len(songs)}** songs to the queue.")

    if not vc.is_playing() and not vc.is_paused():
        play_next(vc, state)


@bot.tree.command(name="skip", description="Skip the current song")
async def skip(interaction: discord.Interaction):
    vc: discord.VoiceClient | None = interaction.guild.voice_client
    if vc is None or not (vc.is_playing() or vc.is_paused()):
        await interaction.response.send_message("Nothing is playing right now.")
        return
    vc.stop()
    await interaction.response.send_message("Skipped!")


@bot.tree.command(name="queue", description="Show the current queue")
async def queue_cmd(interaction: discord.Interaction):
    state = get_state(interaction.guild_id)
    if not state.current and not state.queue:
        await interaction.response.send_message("The queue is empty.")
        return

    lines = []
    if state.current:
        lines.append(f"**Now playing:** {state.current.title} `[{state.current.fmt_duration()}]`")

    for i, song in enumerate(state.queue, 1):
        lines.append(f"`{i}.` {song.title} `[{song.fmt_duration()}]` — {song.requester}")
        if i >= 20:
            lines.append(f"… and {len(state.queue) - 20} more")
            break

    await interaction.response.send_message("\n".join(lines))


@bot.tree.command(name="nowplaying", description="Show what's currently playing")
async def nowplaying(interaction: discord.Interaction):
    state = get_state(interaction.guild_id)
    if state.current:
        await interaction.response.send_message(
            f"Now playing: **{state.current.title}** `[{state.current.fmt_duration()}]`"
            f" — requested by {state.current.requester}"
        )
    else:
        await interaction.response.send_message("Nothing is playing.")


@bot.tree.command(name="pause", description="Pause playback")
async def pause(interaction: discord.Interaction):
    vc: discord.VoiceClient | None = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("Paused.")
    else:
        await interaction.response.send_message("Nothing is playing.")


@bot.tree.command(name="resume", description="Resume playback")
async def resume(interaction: discord.Interaction):
    vc: discord.VoiceClient | None = interaction.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("Resumed.")
    else:
        await interaction.response.send_message("Nothing is paused.")


@bot.tree.command(name="stop", description="Stop playback and disconnect")
async def stop(interaction: discord.Interaction):
    state = get_state(interaction.guild_id)
    state.queue.clear()
    state.current = None
    vc: discord.VoiceClient | None = interaction.guild.voice_client
    if vc:
        vc.stop()
        await vc.disconnect()
    await interaction.response.send_message("Stopped and disconnected.")


@bot.tree.command(name="remove", description="Remove a song from the queue by position")
@app_commands.describe(position="Position in the queue (use /queue to see positions)")
async def remove(interaction: discord.Interaction, position: int):
    state = get_state(interaction.guild_id)
    if position < 1 or position > len(state.queue):
        await interaction.response.send_message(
            f"Invalid position. Queue has {len(state.queue)} song(s)."
        )
        return
    lst = list(state.queue)
    removed = lst.pop(position - 1)
    state.queue = deque(lst)
    await interaction.response.send_message(f"Removed: **{removed.title}**")


@bot.tree.command(name="clear", description="Clear the queue without stopping the current song")
async def clear(interaction: discord.Interaction):
    state = get_state(interaction.guild_id)
    state.queue.clear()
    await interaction.response.send_message("Queue cleared.")


@bot.tree.command(name="loop", description="Set loop mode")
@app_commands.describe(mode="one = loop current song, queue = loop whole queue, off = disable")
@app_commands.choices(mode=[
    app_commands.Choice(name="one (current song)", value="one"),
    app_commands.Choice(name="queue", value="queue"),
    app_commands.Choice(name="off", value="off"),
])
async def loop_cmd(interaction: discord.Interaction, mode: str):
    state = get_state(interaction.guild_id)
    if mode == "one":
        state.loop_one = True
        state.loop_queue = False
        await interaction.response.send_message("Looping current song.")
    elif mode == "queue":
        state.loop_one = False
        state.loop_queue = True
        await interaction.response.send_message("Looping queue.")
    else:
        state.loop_one = False
        state.loop_queue = False
        await interaction.response.send_message("Loop disabled.")


# ── EVENTS ────────────────────────────────────────────────────────────────────
GUILD = discord.Object(id=207366864341303296)


@bot.event
async def on_ready():
    bot.tree.copy_global_to(guild=GUILD)
    await bot.tree.sync(guild=GUILD)
    print(f"Logged in as {bot.user} ({bot.user.id})")
    print("Slash commands synced to guild.")


@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    vc: discord.VoiceClient | None = member.guild.voice_client
    if vc and len(vc.channel.members) == 1:
        state = get_state(member.guild.id)
        state.queue.clear()
        state.current = None
        await vc.disconnect()


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os

    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        try:
            with open(".env") as f:
                for line in f:
                    if line.startswith("DISCORD_TOKEN="):
                        token = line.split("=", 1)[1].strip()
        except FileNotFoundError:
            pass

    if not token:
        print("Error: DISCORD_TOKEN not set. Create a .env file with DISCORD_TOKEN=your_token")
        raise SystemExit(1)

    bot.run(token)
