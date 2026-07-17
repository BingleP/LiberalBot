import random
from collections import deque

import discord
from discord.ui import View, Button, Select

from config import COLOUR
from persona import say
from state import get_state


class NowPlayingView(View):
    def __init__(self, guild_id: int, loop_one: bool, loop_queue: bool, is_paused: bool = False):
        super().__init__(timeout=None)
        self.guild_id = guild_id

        self._pp = Button(
            emoji="\u25b6\ufe0f" if is_paused else "\u23ef\ufe0f",
            style=discord.ButtonStyle.secondary,
            row=0,
        )
        self._skip = Button(emoji="\u23ed\ufe0f", style=discord.ButtonStyle.secondary, row=0)
        self._stop = Button(emoji="\u23f9\ufe0f", style=discord.ButtonStyle.danger, row=0)
        self._loop = Button(
            emoji="\U0001f501" if loop_queue else ("\U0001f502" if loop_one else "\U0001f503"),
            style=discord.ButtonStyle.primary if (loop_one or loop_queue) else discord.ButtonStyle.secondary,
            row=1,
        )
        self._shuffle = Button(emoji="\U0001f500", style=discord.ButtonStyle.secondary, row=1)

        self._pp.callback = self._play_pause
        self._skip.callback = self._skip_song
        self._stop.callback = self._stop_playback
        self._loop.callback = self._toggle_loop
        self._shuffle.callback = self._shuffle_queue

        self.add_item(self._pp)
        self.add_item(self._skip)
        self.add_item(self._stop)
        self.add_item(self._loop)
        self.add_item(self._shuffle)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        vc = interaction.guild.voice_client
        if not vc or not vc.channel:
            await interaction.response.send_message(
                say("offline"), ephemeral=True
            )
            return False
        if interaction.user.voice and interaction.user.voice.channel == vc.channel:
            return True
        await interaction.response.send_message(
            say("wrong_voice_channel"), ephemeral=True
        )
        return False

    async def _play_pause(self, interaction: discord.Interaction):
        state = get_state(self.guild_id)
        vc = interaction.guild.voice_client
        if vc.is_playing():
            vc.pause()
            state.is_paused = True
            self._pp.emoji = "\u25b6\ufe0f"
        elif vc.is_paused():
            vc.resume()
            state.is_paused = False
            self._pp.emoji = "\u23ef\ufe0f"
        await interaction.response.edit_message(view=self)

    async def _skip_song(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
        await interaction.response.defer()

    async def _stop_playback(self, interaction: discord.Interaction):
        state = get_state(interaction.guild_id)
        state.cleanup()
        state.queue.clear()
        state.current = None
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            await vc.disconnect()
        embed = discord.Embed(
            description=say("stopped"),
            colour=COLOUR,
        )
        await interaction.response.edit_message(embed=embed, view=None)

    async def _toggle_loop(self, interaction: discord.Interaction):
        state = get_state(interaction.guild_id)
        if state.loop_one:
            state.loop_one = False
            state.loop_queue = True
            self._loop.emoji = "\U0001f501"
            self._loop.style = discord.ButtonStyle.primary
        elif state.loop_queue:
            state.loop_queue = False
            self._loop.emoji = "\U0001f503"
            self._loop.style = discord.ButtonStyle.secondary
        else:
            state.loop_one = True
            self._loop.emoji = "\U0001f502"
            self._loop.style = discord.ButtonStyle.primary
        await interaction.response.edit_message(view=self)

    async def _shuffle_queue(self, interaction: discord.Interaction):
        state = get_state(interaction.guild_id)
        if not state.queue:
            await interaction.response.send_message(
                say("queue_empty"), ephemeral=True
            )
            return
        items = list(state.queue)
        random.shuffle(items)
        state.queue = deque(items)
        await interaction.response.defer()
        embed = discord.Embed(
            description=say("shuffle"),
            colour=COLOUR,
        )
        await state.send(embed=embed)


class SearchSelect(Select):
    def __init__(self, songs: list, guild_id: int, insert_front: bool = False):
        self._guild_id = guild_id
        self._songs = songs
        self._insert_front = insert_front
        options = []
        for i, s in enumerate(songs[:10]):
            label = s.title[:60] if s.title else "Unknown"
            desc = f"{s.requester} | {s.fmt_duration()}"[:50] if s.duration else s.requester[:50]
            options.append(
                discord.SelectOption(label=label, description=desc, value=str(i))
            )
        super().__init__(
            placeholder="Choose a track...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        song = self._songs[idx]
        state = get_state(self._guild_id)
        state.set_channel(interaction.channel)

        if self._insert_front:
            state.queue.appendleft(song)
            position = 1
            event = "playnext"
        else:
            state.queue.append(song)
            position = len(state.queue)
            event = "added_to_queue"

        vc = interaction.guild.voice_client
        if vc is None:
            if interaction.user.voice:
                vc = await interaction.user.voice.channel.connect()

        embed = song.queued_embed(position)
        await interaction.response.edit_message(
            content=say(event, title=song.title),
            embed=embed,
            view=None,
        )

        from player import play_next
        if vc and not vc.is_playing() and not vc.is_paused():
            play_next(vc, state)


class SearchPickerView(View):
    def __init__(self, songs: list, guild_id: int, insert_front: bool = False):
        super().__init__(timeout=60)
        self.add_item(SearchSelect(songs, guild_id, insert_front=insert_front))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
