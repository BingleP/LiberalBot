import asyncio
import time

import discord

from config import COLOUR, logger
from errors import classify_error, RETRYABLE_ERRORS, user_friendly_error
from persona import say
import state as state_module
from state import GuildState, get_state
from utils import progress_bar
from views import NowPlayingView


async def _notify_error(state: GuildState, msg: str):
    embed = discord.Embed(description=msg, colour=discord.Colour.red())
    await state.send(embed=embed)


def _run(coro):
    loop = state_module.bot_loop or (state_module.bot.loop if state_module.bot else None) or asyncio.get_event_loop()
    return asyncio.run_coroutine_threadsafe(coro, loop)


def play_next(vc: discord.VoiceClient, state: GuildState, error=None):
    if error:
        title = state.current.title if state.current else "Unknown"
        logger.error(f"Playback error for '{title}': {error}")
        media_error = classify_error(error)

        if state.current:
            state.current.last_error = media_error

        if (
            state.current
            and state.current.retry_count < state.current.max_retries
            and media_error in RETRYABLE_ERRORS
        ):
            state.current.retry_count += 1
            attempt = state.current.retry_count + 1
            logger.info(f"Retrying '{title}' (attempt {attempt}/{state.current.max_retries + 1}): {media_error.value}")

            _run(
                _notify_error(
                    state,
                    f"Loading **{title}** failed, retrying... (attempt {attempt}/{state.current.max_retries + 1})",
                )
            )

            backoff = 2 ** (state.current.retry_count - 1)
            time.sleep(backoff)

            source = discord.PCMVolumeTransformer(state.current.audio_source())
            vc.play(source, after=lambda e: play_next(vc, state, e))
            return

        if state.current:
            msg = user_friendly_error(media_error, title, str(error))
            logger.error(f"Final failure for '{title}': {media_error.value}")
        else:
            msg = f"The transmission was interrupted. ({error})"

        _run(_notify_error(state, msg))
        _run(_update_presence(None))
        state.cleanup()
        return

    if state.current:
        state.current.retry_count = 0
        state.current.last_error = None

    if state.loop_one and state.current:
        state.is_paused = False
        source = discord.PCMVolumeTransformer(state.current.audio_source())
        vc.play(source, after=lambda e: play_next(vc, state, e))
        return

    if state.loop_queue and state.current:
        state.queue.append(state.current)

    if not state.queue:
        state.current = None
        state.cleanup()
        embed = discord.Embed(
            title="TRANSMISSION ENDED",
            description=say("queue_empty"),
            colour=COLOUR,
        )
        _run(state.send(embed=embed))
        _run(_update_presence(None))
        return

    song = state.queue.popleft()
    state.current = song
    state.is_paused = False
    state.song_start_time = time.time()
    source = discord.PCMVolumeTransformer(song.audio_source())
    vc.play(source, after=lambda e: play_next(vc, state, e))

    embed = song.now_playing_embed()
    view = NowPlayingView(vc.guild.id, state.loop_one, state.loop_queue, state.is_paused)
    _run(_send_now_playing(state, embed, view, vc.guild.id))
    _run(_update_presence(song))


async def _send_now_playing(
    state: GuildState, embed: discord.Embed, view: NowPlayingView, guild_id: int
):
    if state.now_playing_message:
        try:
            await state.now_playing_message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass
        state.now_playing_message = None
    msg = await state.send(embed=embed)
    if msg:
        state.now_playing_message = msg
        _start_progress(guild_id)


async def _progress_loop(guild_id: int):
    state = get_state(guild_id)
    try:
        while state.current and state.now_playing_message:
            await asyncio.sleep(5)
            if not state.current or not state.now_playing_message:
                break
            elapsed = time.time() - state.song_start_time
            bar = progress_bar(elapsed, state.current.duration)
            embed = state.current.now_playing_embed(progress=bar)
            view = NowPlayingView(guild_id, state.loop_one, state.loop_queue, state.is_paused)
            try:
                await state.now_playing_message.edit(embed=embed, view=view)
            except (discord.NotFound, discord.Forbidden):
                break
    except asyncio.CancelledError:
        pass
    finally:
        state.progress_task = None


def _start_progress(guild_id: int):
    state = get_state(guild_id)
    if state.progress_task and not state.progress_task.done():
        state.progress_task.cancel()
    state.progress_task = asyncio.create_task(_progress_loop(guild_id))


async def _update_presence(song):
    if not state_module.bot:
        return
    if song:
        await state_module.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=song.title),
            status=discord.Status.online,
        )
    else:
        await state_module.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name="the globalists | /play to resist"),
            status=discord.Status.idle,
        )


async def ensure_voice(interaction: discord.Interaction) -> discord.VoiceClient | None:
    if interaction.user.voice is None:
        embed = discord.Embed(
            description=say("no_voice_channel"),
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


async def update_presence(song):
    await _update_presence(song)


def is_url(query: str) -> bool:
    return query.startswith("http://") or query.startswith("https://")
