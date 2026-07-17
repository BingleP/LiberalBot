import random
from collections import deque
from time import time

import discord
from discord import app_commands
from discord.ext.commands import Bot

from config import COLOUR, logger
from persona import say
from song import Song
from state import get_state
from player import ensure_voice, is_url, play_next, update_presence, _send_now_playing
from utils import fmt_seconds, progress_bar
from views import NowPlayingView, SearchPickerView


def register_commands(bot: Bot):
    @bot.tree.command(name="play", description="Play a song or YouTube playlist")
    @app_commands.describe(query="Song name, YouTube URL, or playlist URL")
    async def play(interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        vc = await ensure_voice(interaction)
        if vc is None:
            return

        state = get_state(interaction.guild_id)
        state.set_channel(interaction.channel)

        try:
            songs = await Song.from_query(query, interaction.user.display_name)
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            embed = discord.Embed(
                description=f"{say('yt_dlp_error')}\n`{e}`",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed)
            return

        if not songs:
            embed = discord.Embed(
                description=say("no_results"),
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed)
            return

        if not is_url(query) and len(songs) > 1:
            view = SearchPickerView(songs, interaction.guild_id)
            embed = discord.Embed(
                title="SEARCH RESULTS",
                description=f"Found **{len(songs)}** transmissions. Pick one:",
                colour=COLOUR,
            )
            await interaction.followup.send(embed=embed, view=view)
            return

        for song in songs:
            state.queue.append(song)

        if len(songs) == 1:
            if vc.is_playing() or vc.is_paused():
                await interaction.followup.send(embed=songs[0].queued_embed(len(state.queue)))
            else:
                embed = discord.Embed(
                    description=say("added_to_queue", title=songs[0].title),
                    colour=COLOUR,
                )
                await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="PLAYLIST LOADED",
                description=say("queued_multiple", count=len(songs)),
                colour=COLOUR,
            )
            await interaction.followup.send(embed=embed)

        if not vc.is_playing() and not vc.is_paused():
            play_next(vc, state)

    @bot.tree.command(name="playnext", description="Add a song to play next in the queue")
    @app_commands.describe(query="Song name, YouTube URL, or playlist URL")
    async def playnext(interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        vc = await ensure_voice(interaction)
        if vc is None:
            return

        state = get_state(interaction.guild_id)
        state.set_channel(interaction.channel)

        try:
            songs = await Song.from_query(query, interaction.user.display_name)
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            embed = discord.Embed(
                description=f"{say('yt_dlp_error')}\n`{e}`",
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed)
            return

        if not songs:
            embed = discord.Embed(
                description=say("no_results"),
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed)
            return

        if not is_url(query) and len(songs) > 1:
            view = SearchPickerView(songs, interaction.guild_id, insert_front=True)
            embed = discord.Embed(
                title="SEARCH RESULTS",
                description=f"Found **{len(songs)}** transmissions. Pick one to play next:",
                colour=COLOUR,
            )
            await interaction.followup.send(embed=embed, view=view)
            return

        for song in reversed(songs):
            state.queue.appendleft(song)

        if len(songs) == 1:
            embed = discord.Embed(
                description=say("playnext", title=songs[0].title),
                colour=COLOUR,
            )
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="PLAYLIST PRIORITY LOAD",
                description=say("playnext_multiple", count=len(songs)),
                colour=COLOUR,
            )
            await interaction.followup.send(embed=embed)

        if not vc.is_playing() and not vc.is_paused():
            play_next(vc, state)

    @bot.tree.command(name="skip", description="Skip the current song")
    async def skip(interaction: discord.Interaction):
        await interaction.response.defer()
        vc: discord.VoiceClient | None = interaction.guild.voice_client
        state = get_state(interaction.guild_id)

        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            embed = discord.Embed(description=say("skipped"), colour=COLOUR)
            await interaction.followup.send(embed=embed)
            return

        if state.current and state.queue:
            state.current.retry_count = 0
            state.current.last_error = None

            vc = await ensure_voice(interaction)
            if vc is None:
                return

            song = state.queue.popleft()
            state.current = song
            state.is_paused = False
            state.song_start_time = time()

            source = discord.PCMVolumeTransformer(song.audio_source())
            vc.play(source, after=lambda e: play_next(vc, state, e))

            embed = song.now_playing_embed()
            view = NowPlayingView(interaction.guild_id, state.loop_one, state.loop_queue, state.is_paused)
            await _send_now_playing(state, embed, view, interaction.guild_id)
            await update_presence(song)
            embed = discord.Embed(description=say("skipped"), colour=COLOUR)
            await interaction.followup.send(embed=embed)
            return

        embed = discord.Embed(description=say("nothing_playing"), colour=discord.Colour.red())
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="skipto", description="Skip to a specific position in the queue")
    @app_commands.describe(position="Position in the queue to jump to (use /queue to see positions)")
    async def skipto(interaction: discord.Interaction, position: int):
        await interaction.response.defer()
        state = get_state(interaction.guild_id)

        if position < 1 or position > len(state.queue):
            embed = discord.Embed(
                description=say("invalid_position"),
                colour=discord.Colour.red(),
            )
            await interaction.followup.send(embed=embed)
            return

        vc: discord.VoiceClient | None = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            vc = await ensure_voice(interaction)
            if vc is None:
                return

        for _ in range(position - 1):
            state.queue.popleft()

        song = state.queue.popleft()
        state.current = song
        state.is_paused = False
        state.song_start_time = time()

        if vc.is_playing() or vc.is_paused():
            vc.stop()

        source = discord.PCMVolumeTransformer(song.audio_source())
        vc.play(source, after=lambda e: play_next(vc, state, e))

        embed = song.now_playing_embed()
        view = NowPlayingView(interaction.guild_id, state.loop_one, state.loop_queue, state.is_paused)
        await _send_now_playing(state, embed, view, interaction.guild_id)
        await update_presence(song)

        embed = discord.Embed(
            description=say("skipto", position=position),
            colour=COLOUR,
        )
        await interaction.followup.send(embed=embed)

    @bot.tree.command(name="queue", description="Show the current queue")
    async def queue_cmd(interaction: discord.Interaction):
        state = get_state(interaction.guild_id)
        if not state.current and not state.queue:
            embed = discord.Embed(description=say("queue_empty"), colour=discord.Colour.red())
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(title="THE BATTLE PLAN", colour=COLOUR)

        if state.current:
            loop_tag = " (loop one)" if state.loop_one else (" (loop queue)" if state.loop_queue else "")
            embed.add_field(
                name=f"CURRENTLY ON AIR{loop_tag}",
                value=f"{state.current._title_link()} `[{state.current.fmt_duration()}]`",
                inline=False,
            )
            if state.current.thumbnail:
                embed.set_thumbnail(url=state.current.thumbnail)

        if state.queue:
            lines = []
            total = 0
            for i, song in enumerate(state.queue, 1):
                lines.append(
                    f"`{i}.` {song._title_link()} `[{song.fmt_duration()}]` — {song.requester}"
                )
                total += song.duration or 0
                if i >= 20:
                    remaining = len(state.queue) - 20
                    if remaining:
                        lines.append(f"... and {remaining} more")
                    break
            embed.add_field(name="THE RESISTANCE LINEUP", value="\n".join(lines), inline=False)
            embed.set_footer(text=f"Total upcoming time: {fmt_seconds(total)}")

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="nowplaying", description="Show what's currently playing")
    async def nowplaying(interaction: discord.Interaction):
        state = get_state(interaction.guild_id)
        if state.current:
            elapsed = time() - state.song_start_time
            bar = progress_bar(elapsed, state.current.duration) if state.current.duration else None
            embed = state.current.now_playing_embed(progress=bar)
            view = NowPlayingView(interaction.guild_id, state.loop_one, state.loop_queue, state.is_paused)
            await interaction.response.send_message(embed=embed, view=view)
        else:
            embed = discord.Embed(description=say("nothing_playing"), colour=discord.Colour.red())
            await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="pause", description="Pause playback")
    async def pause(interaction: discord.Interaction):
        state = get_state(interaction.guild_id)
        vc: discord.VoiceClient | None = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            state.is_paused = True
            embed = discord.Embed(description=say("paused"), colour=COLOUR)
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(description=say("nothing_playing"), colour=discord.Colour.red())
            await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="resume", description="Resume playback")
    async def resume(interaction: discord.Interaction):
        state = get_state(interaction.guild_id)
        vc: discord.VoiceClient | None = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            state.is_paused = False
            embed = discord.Embed(description=say("resumed"), colour=COLOUR)
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(description=say("not_paused"), colour=discord.Colour.red())
            await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="stop", description="Stop playback and disconnect")
    async def stop(interaction: discord.Interaction):
        state = get_state(interaction.guild_id)
        state.cleanup()
        state.queue.clear()
        state.current = None
        vc: discord.VoiceClient | None = interaction.guild.voice_client
        if vc:
            vc.stop()
            await vc.disconnect()
        embed = discord.Embed(description=say("stopped"), colour=COLOUR)
        await interaction.response.send_message(embed=embed)
        await update_presence(None)

    @bot.tree.command(name="remove", description="Remove a song from the queue by position")
    @app_commands.describe(position="Position in the queue (use /queue to see positions)")
    async def remove(interaction: discord.Interaction, position: int):
        state = get_state(interaction.guild_id)
        if position < 1 or position > len(state.queue):
            embed = discord.Embed(
                description=say("invalid_position"),
                colour=discord.Colour.red(),
            )
            await interaction.response.send_message(embed=embed)
            return
        lst = list(state.queue)
        removed = lst.pop(position - 1)
        state.queue = deque(lst)
        embed = discord.Embed(
            description=say("removed", title=removed.title),
            colour=COLOUR,
        )
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="clear", description="Clear the queue without stopping the current song")
    async def clear(interaction: discord.Interaction):
        state = get_state(interaction.guild_id)
        state.queue.clear()
        embed = discord.Embed(description=say("cleared"), colour=COLOUR)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="shuffle", description="Shuffle the current queue")
    async def shuffle(interaction: discord.Interaction):
        state = get_state(interaction.guild_id)
        if not state.queue:
            embed = discord.Embed(
                description=say("queue_empty"),
                colour=discord.Colour.red(),
            )
            await interaction.response.send_message(embed=embed)
            return
        items = list(state.queue)
        random.shuffle(items)
        state.queue = deque(items)
        embed = discord.Embed(description=say("shuffle"), colour=COLOUR)
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
            embed = discord.Embed(description=say("loop_one"), colour=COLOUR)
        elif mode == "queue":
            state.loop_one = False
            state.loop_queue = True
            embed = discord.Embed(description=say("loop_queue"), colour=COLOUR)
        else:
            state.loop_one = False
            state.loop_queue = False
            embed = discord.Embed(description=say("loop_off"), colour=COLOUR)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="retry", description="Retry playing the current song if it failed")
    async def retry(interaction: discord.Interaction):
        state = get_state(interaction.guild_id)
        vc: discord.VoiceClient | None = interaction.guild.voice_client

        if not state.current:
            embed = discord.Embed(
                description=say("nothing_playing"),
                colour=discord.Colour.red(),
            )
            await interaction.response.send_message(embed=embed)
            return

        if vc and (vc.is_playing() or vc.is_paused()):
            embed = discord.Embed(
                description=say("already_playing"),
                colour=discord.Colour.red(),
            )
            await interaction.response.send_message(embed=embed)
            return

        if not vc or not vc.is_connected():
            if interaction.user.voice:
                vc = await interaction.user.voice.channel.connect()
            else:
                embed = discord.Embed(
                    description=say("no_voice_channel"),
                    colour=discord.Colour.red(),
                )
                await interaction.response.send_message(embed=embed)
                return

        state.current.retry_count = 0
        state.current.last_error = None
        state.is_paused = False
        state.song_start_time = time()

        embed = discord.Embed(
            description=say("retry", title=state.current.title),
            colour=COLOUR,
        )
        await interaction.response.send_message(embed=embed)

        source = discord.PCMVolumeTransformer(state.current.audio_source())
        vc.play(source, after=lambda e: play_next(vc, state, e))

        np_embed = state.current.now_playing_embed()
        view = NowPlayingView(interaction.guild_id, state.loop_one, state.loop_queue, state.is_paused)
        await _send_now_playing(state, np_embed, view, interaction.guild_id)

    @bot.tree.command(name="help", description="Show the command list")
    async def help_cmd(interaction: discord.Interaction):
        embed = discord.Embed(
            title="RESISTANCE PLAYBOOK",
            description=say("help"),
            colour=COLOUR,
        )
        commands_list = [
            ("/play <query>", "Play a song, URL, or playlist"),
            ("/playnext <query>", "Add a song to play next"),
            ("/skip", "Skip the current song"),
            ("/skipto <position>", "Jump to a queue position"),
            ("/queue", "Show the current queue"),
            ("/nowplaying", "Show the current track"),
            ("/pause", "Pause playback"),
            ("/resume", "Resume playback"),
            ("/stop", "Stop and disconnect"),
            ("/remove <position>", "Remove a song from the queue"),
            ("/clear", "Clear the queue"),
            ("/shuffle", "Shuffle the queue"),
            ("/loop <mode>", "Set loop mode: one, queue, off"),
            ("/retry", "Retry the failed current song"),
        ]
        for name, desc in commands_list:
            embed.add_field(name=name, value=desc, inline=False)
        embed.set_footer(text="Use these commands to keep the signal alive.")
        await interaction.response.send_message(embed=embed)
