import os

import discord
from discord.ext import commands

import state as state_module
from commands import register_commands
from player import update_presence


GUILD = discord.Object(id=207366864341303296)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
state_module.bot = bot

register_commands(bot)


@bot.event
async def on_ready():
    state_module.bot_loop = bot.loop
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
        from state import get_state
        state = get_state(member.guild.id)
        state.cleanup()
        state.queue.clear()
        state.current = None
        await vc.disconnect()
        await update_presence(None)


if __name__ == "__main__":
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
