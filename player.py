import asyncio
import time

import discord

from audio import YTDLSource
from config import COLOUR, logger, MAX_STREAM_URL_AGE
from errors import classify_error, RETRYABLE_ERRORS, user_friendly_error, MediaError
from persona import PersonaEvents, say, say_status
import state as state_module
from state import GuildState, get_state
from utils import progress_bar
from views import NowPlayingView


def _run(coro):
    loop = state_module.bot_loop or (state_module.bot.loop if state_module.bot else None) or asyncio.get_event_loop()
    return asyncio.run_coroutine_threadsafe(coro, loop)


async def _notify_error(state: GuildState, msg: str):
    embed = discord.Embed(description=msg, colour=discord.Colour.red())
    state.last_error_message = await state.send(embed=embed)


async def _clear_error_message(state: GuildState):
    if state.last_error_message:
        try:
            await state.last_error_message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass
        state.last_error_message = None


async def audio_source_for(song):
    """Build a PCMVolumeTransformer around an FFmpeg source, re-extracting if the URL is stale."""
    age = time.time() - song.extracted_at
    if age >= MAX_STREAM_URL_AGE or not song.stream_url:
        logger.info(f"Stream URL for '{song.title}' is stale ({age:.0f}s old) or missing, re-extracting...")
        stream_url, headers = await song.get_stream_url(force=True)
    else:
        stream_url, headers = song.stream_url, song.stream_headers
    return discord.PCMVolumeTransformer(YTDLSource(stream_url, headers))


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
            _run(asyncio.sleep(backoff)).result()

            # If the URL looks stale, force a re-extract before retrying.
            if media_error in {MediaError.STREAM_ERROR, MediaError.AUTH_FAILED, MediaError.UNKNOWN}:
                try:
                    _run(state.current.get_stream_url(force=True)).result()
                except Exception as e:
                    logger.warning(f"Could not re-extract stream URL for '{title}': {e}")

            source = _run(audio_source_for(state.current)).result()
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
        logger.info(say(PersonaEvents.SONG_FINISHED, title=state.current.title))
        state.current.retry_count = 0
        state.current.last_error = None

    _run(_clear_error_message(state))

    if state.loop_one and state.current:
        state.is_paused = False
        source = _run(audio_source_for(state.current)).result()
        vc.play(source, after=lambda e: play_next(vc, state, e))
        logger.info(say(PersonaEvents.SONG_STARTED, title=state.current.title))
        return

    if state.loop_queue and state.current:
        state.queue.append(state.current)

    if not state.queue:
        state.current = None
        state.cleanup()
        embed = discord.Embed(
            title="TRANSMISSION ENDED",
            description=say(PersonaEvents.QUEUE_EMPTY),
            colour=COLOUR,
        )
        _run(state.send(embed=embed))
        _run(_update_presence(None))
        return

    song = state.queue.popleft()
    state.current = song
    state.is_paused = False
    state.song_start_time = time.time()
    source = _run(audio_source_for(song)).result()
    vc.play(source, after=lambda e: play_next(vc, state, e))
    logger.info(say(PersonaEvents.SONG_STARTED, title=song.title))

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
    activity = say_status(playing_title=song.title if song else None)
    await state_module.bot.change_presence(
        activity=activity,
        status=discord.Status.online if song else discord.Status.idle,
    )


async def ensure_voice(interaction: discord.Interaction) -> discord.VoiceClient | None:
    if interaction.user.voice is None:
        embed = discord.Embed(
            description=say(PersonaEvents.NO_VOICE_CHANNEL),
            colour=discord.Colour.red(),
        )
        await interaction.followup.send(embed=embed)
        return None

    vc: discord.VoiceClient | None = interaction.guild.voice_client

    if vc is None:
        vc = await interaction.user.voice.channel.connect()
        logger.info(say(PersonaEvents.JOINED_VC))
    elif vc.channel != interaction.user.voice.channel:
        await vc.move_to(interaction.user.voice.channel)
        logger.info(say(PersonaEvents.MOVED_VC))

    return vc


async def update_presence(song):
    await _update_presence(song)


def is_url(query: str) -> bool:
    return query.startswith("http://") or query.startswith("https://")
