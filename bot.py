import asyncio
import os

import discord
from discord.ext import commands

import state as state_module
from commands import register_commands
from config import make_ytdl, WARMUP_URL
from persona import PersonaEvents, say, say_status, validate_persona
from player import update_presence


STATUS_ROTATION_INTERVAL = 5 * 60  # 5 minutes


GUILD = discord.Object(id=207366864341303296)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
state_module.bot = bot

register_commands(bot)


def _any_guild_playing() -> bool:
    """Return True if any guild has an active song."""
    from state import states
    return any(state.current is not None for state in states.values())


async def _warmup_ytdlp():
    """Run a dummy extraction so the EJS solver and caches are ready before playback."""
    loop = asyncio.get_event_loop()
    ytdl = make_ytdl()
    try:
        await loop.run_in_executor(None, lambda: ytdl.extract_info(WARMUP_URL, download=False))
    except Exception as e:
        print(f"Warning: yt-dlp warm-up failed: {e}")


async def _rotate_idle_status():
    """Background task that rotates the bot's status while idle."""
    while True:
        try:
            await asyncio.sleep(STATUS_ROTATION_INTERVAL)
            if not _any_guild_playing():
                await state_module.bot.change_presence(
                    activity=say_status(),
                    status=discord.Status.idle,
                )
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Status rotation task error: {e}")


@bot.event
async def on_ready():
    state_module.bot_loop = bot.loop
    bot.tree.copy_global_to(guild=GUILD)
    await bot.tree.sync(guild=GUILD)
    await _warmup_ytdlp()

    issues = validate_persona()
    if issues:
        print("Persona validation warnings:")
        for issue in issues:
            print(f"  - {issue}")

    bot.loop.create_task(_rotate_idle_status())
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
        print(say(PersonaEvents.DISCONNECT_EMPTY))


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
