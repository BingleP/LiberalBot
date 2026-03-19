import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
from collections import deque

COLOUR = 0x9B59B6  # purple accent

# ── FFMPEG OPTIONS ──────────────────────────────────────────────────────────
FFMPEG_BEFORE_OPTS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTS = {"options": "-vn", "before_options": FFMPEG_BEFORE_OPTS}

YTDL_OPTS = {
    "format": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "noplaylist": True,
    "extract_flat": "in_playlist",
    "playlistend": 25,
    "source_address": "0.0.0.0",
    "cookiefile": "/home/bingle/Documents/www.youtube.com_cookies.txt",
    "extractor_args": {"youtube": {"player_client": ["web", "ios"]}},
    "remote_components": ["ejs:github"],
}

YTDL_ENTRY_OPTS = {**YTDL_OPTS, "extract_flat": False, "noplaylist": True}


def make_ytdl():
    return yt_dlp.YoutubeDL(YTDL_OPTS)


# ── SONG ────────────────────────────────────────────────────────────────────
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

    def audio_source(self) -> discord.FFmpegPCMAudio:
        return discord.FFmpegPCMAudio(self.url, **FFMPEG_OPTS)

    def fmt_duration(self) -> str:
        m, s = divmod(self.duration, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    def _title_link(self) -> str:
        return f"[{self.title}]({self.webpage_url})" if self.webpage_url else self.title

    def now_playing_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="\U0001f4e1 LADIES AND GENTLEMEN, WE ARE ON AIR",
            description=self._title_link(),
            colour=COLOUR,
        )
        embed.add_field(name="Time on Air", value=self.fmt_duration(), inline=True)
        embed.add_field(name="Patriot on Deck", value=self.requester, inline=True)
        embed.set_footer(text="The globalists DO NOT want you listening to this.")
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        return embed

    def queued_embed(self, position: int) -> discord.Embed:
        embed = discord.Embed(
            title=f"\u26a0\ufe0f LOCKED AND LOADED \u2014 POSITION #{position}",
            description=self._title_link(),
            colour=COLOUR,
        )
        embed.add_field(name="Time on Air", value=self.fmt_duration(), inline=True)
        embed.add_field(name="Patriot on Deck", value=self.requester, inline=True)
        embed.set_footer(text="They can't stop the signal.")
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        return embed


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

    async def send(self, embed: discord.Embed | None = None, content: str | None = None):
        if self._text_channel:
            await self._text_channel.send(content=content, embed=embed)


# ── BOT ──────────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
states: dict[int, GuildState] = {}


def get_state(guild_id: int) -> GuildState:
    if guild_id not in states:
        states[guild_id] = GuildState()
    return states[guild_id]


async def update_presence(song: Song | None):
    if song:
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=song.title),
            status=discord.Status.online,
        )
    else:
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name="the globalists | /play to resist"),
            status=discord.Status.idle,
        )


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
        embed = discord.Embed(
            title="\U0001f6a8 THE TRANSMISSION HAS ENDED",
            description="They finally silenced us\u2026 for now. Use `/play` to take back the airwaves, PATRIOTS!",
            colour=COLOUR,
        )
        asyncio.run_coroutine_threadsafe(state.send(embed=embed), bot.loop)
        asyncio.run_coroutine_threadsafe(update_presence(None), bot.loop)
        return

    song = state.queue.popleft()
    state.current = song
    source = discord.PCMVolumeTransformer(song.audio_source())
    vc.play(source, after=lambda e: play_next(vc, state, e))

    asyncio.run_coroutine_threadsafe(state.send(embed=song.now_playing_embed()), bot.loop)
    asyncio.run_coroutine_threadsafe(update_presence(song), bot.loop)


async def ensure_voice(interaction: discord.Interaction) -> discord.VoiceClient | None:
    if interaction.user.voice is None:
        embed = discord.Embed(
            description="LADIES AND GENTLEMEN, you are NOT in a voice channel! They've locked you out! Get in there and fight back!",
            colour=discord.Colour.red(),
        )
        await interaction.followup.send(embed=embed)
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
        embed = discord.Embed(
            description="THE GLOBALISTS HAVE SCRUBBED IT! I couldn't find anything for that query \u2014 they don't want you to hear it!",
            colour=discord.Colour.red(),
        )
        await interaction.followup.send(embed=embed)
        return

    for song in songs:
        state.queue.append(song)

    if len(songs) == 1:
        if vc.is_playing() or vc.is_paused():
            await interaction.followup.send(embed=songs[0].queued_embed(len(state.queue)))
        else:
            embed = discord.Embed(description=f"INITIATING BROADCAST\u2026 They can't stop **{songs[0].title}** from reaching your ears!", colour=COLOUR)
            await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title="\U0001f3b6 THE DEEP STATE IS SHAKING",
            description=f"**{len(songs)}** songs locked and loaded in the battle plan! The information war continues!",
            colour=COLOUR,
        )
        await interaction.followup.send(embed=embed)

    if not vc.is_playing() and not vc.is_paused():
        play_next(vc, state)


@bot.tree.command(name="skip", description="Skip the current song")
async def skip(interaction: discord.Interaction):
    vc: discord.VoiceClient | None = interaction.guild.voice_client
    if vc is None or not (vc.is_playing() or vc.is_paused()):
        embed = discord.Embed(description="THERE'S NOTHING PLAYING! The globalists have already silenced the feed!", colour=discord.Colour.red())
        await interaction.response.send_message(embed=embed)
        return
    vc.stop()
    embed = discord.Embed(description="NEXT! The people demand a new transmission \u2014 moving on!", colour=COLOUR)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="queue", description="Show the current queue")
async def queue_cmd(interaction: discord.Interaction):
    state = get_state(interaction.guild_id)
    if not state.current and not state.queue:
        embed = discord.Embed(description="THE BATTLE PLAN IS EMPTY! The globalists have won\u2026 for now. Use `/play` to reclaim the airwaves!", colour=discord.Colour.red())
        await interaction.response.send_message(embed=embed)
        return

    embed = discord.Embed(title="\U0001f4cb THE BATTLE PLAN", colour=COLOUR)

    if state.current:
        loop_tag = " \U0001f502" if state.loop_one else (" \U0001f501" if state.loop_queue else "")
        embed.add_field(
            name=f"\U0001f4e1 CURRENTLY ON AIR{loop_tag}",
            value=f"{state.current._title_link()} `[{state.current.fmt_duration()}]`",
            inline=False,
        )
        if state.current.thumbnail:
            embed.set_thumbnail(url=state.current.thumbnail)

    if state.queue:
        lines = []
        for i, song in enumerate(state.queue, 1):
            lines.append(
                f"`{i}.` {song._title_link()} `[{song.fmt_duration()}]` \u2014 {song.requester}"
            )
            if i >= 20:
                remaining = len(state.queue) - 20
                if remaining:
                    lines.append(f"\u2026 and {remaining} more")
                break
        embed.add_field(name="\u2694\ufe0f THE RESISTANCE LINEUP", value="\n".join(lines), inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="nowplaying", description="Show what's currently playing")
async def nowplaying(interaction: discord.Interaction):
    state = get_state(interaction.guild_id)
    if state.current:
        await interaction.response.send_message(embed=state.current.now_playing_embed())
    else:
        embed = discord.Embed(description="SILENCE! They've cut the feed! Use `/play` to fight back!", colour=discord.Colour.red())
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="pause", description="Pause playback")
async def pause(interaction: discord.Interaction):
    vc: discord.VoiceClient | None = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        embed = discord.Embed(description="BROADCAST PAUSED! Catching our breath before the next assault on the globalist agenda!", colour=COLOUR)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(description="THERE'S NOTHING PLAYING! They already silenced us!", colour=discord.Colour.red())
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="resume", description="Resume playback")
async def resume(interaction: discord.Interaction):
    vc: discord.VoiceClient | None = interaction.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        embed = discord.Embed(description="WE'RE BACK ON AIR! They tried to stop us\u2014 they FAILED!", colour=COLOUR)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(description="NOTHING IS PAUSED! Full transmission already in progress, folks!", colour=discord.Colour.red())
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="stop", description="Stop playback and disconnect")
async def stop(interaction: discord.Interaction):
    state = get_state(interaction.guild_id)
    state.queue.clear()
    state.current = None
    vc: discord.VoiceClient | None = interaction.guild.voice_client
    if vc:
        vc.stop()
        await vc.disconnect()
    embed = discord.Embed(description="GOING DARK! Disconnecting from the grid\u2014 but we will NEVER stop the fight. 1776 WILL COMMENCE AGAIN!", colour=COLOUR)
    await interaction.response.send_message(embed=embed)
    await update_presence(None)


@bot.tree.command(name="remove", description="Remove a song from the queue by position")
@app_commands.describe(position="Position in the queue (use /queue to see positions)")
async def remove(interaction: discord.Interaction, position: int):
    state = get_state(interaction.guild_id)
    if position < 1 or position > len(state.queue):
        embed = discord.Embed(
            description=f"THAT POSITION DOESN'T EXIST, FOLKS! The battle plan only has {len(state.queue)} song(s)\u2014 are you being deceived by disinformation?!",
            colour=discord.Colour.red(),
        )
        await interaction.response.send_message(embed=embed)
        return
    lst = list(state.queue)
    removed = lst.pop(position - 1)
    state.queue = deque(lst)
    embed = discord.Embed(description=f"ELIMINATED from the battle plan: **{removed.title}**! Cut it\u2014 we don't need that track in the resistance!", colour=COLOUR)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="clear", description="Clear the queue without stopping the current song")
async def clear(interaction: discord.Interaction):
    state = get_state(interaction.guild_id)
    state.queue.clear()
    embed = discord.Embed(description="BATTLE PLAN PURGED! Starting fresh\u2014 like 1776! The resistance rebuilds!", colour=COLOUR)
    await interaction.response.send_message(embed=embed)


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
        embed = discord.Embed(description="\U0001f502 ON REPEAT UNTIL THE TRUTH SETS YOU FREE! They can't make me stop playing this!", colour=COLOUR)
    elif mode == "queue":
        state.loop_one = False
        state.loop_queue = True
        embed = discord.Embed(description="\U0001f501 THE ENTIRE BATTLE PLAN ON LOOP! Endless transmission\u2014 the globalists are HORRIFIED!", colour=COLOUR)
    else:
        state.loop_one = False
        state.loop_queue = False
        embed = discord.Embed(description="Loop protocol DISABLED. Moving forward\u2014 like a true patriot.", colour=COLOUR)
    await interaction.response.send_message(embed=embed)


# ── EVENTS ────────────────────────────────────────────────────────────────────
GUILD = discord.Object(id=207366864341303296)


@bot.event
async def on_ready():
    bot.tree.copy_global_to(guild=GUILD)
    await bot.tree.sync(guild=GUILD)
    await update_presence(None)
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
        await update_presence(None)


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
