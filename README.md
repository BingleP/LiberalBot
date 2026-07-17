# LiberalBot

A Discord music bot that plays audio from YouTube into voice channels using slash commands. The bot keeps its scope strictly to music playback and queue management, wrapped in an Alex Jones-style broadcast persona.

## Features

| Command | Description |
|---|---|
| `/play <query>` | Play a song by name, YouTube URL, or playlist URL |
| `/playnext <query>` | Add a song to play next in the queue |
| `/skip` | Skip the current song (also works if the current song failed to play) |
| `/skipto <position>` | Jump to a specific position in the queue |
| `/queue` | Show the current queue (up to 20 entries) and total upcoming time |
| `/nowplaying` | Show what's currently playing |
| `/pause` | Pause playback |
| `/resume` | Resume paused playback |
| `/stop` | Stop playback and disconnect the bot |
| `/remove <position>` | Remove a song from the queue by position |
| `/clear` | Clear the queue without stopping the current song |
| `/shuffle` | Shuffle the current queue |
| `/loop <mode>` | Set loop mode: `one` (current song), `queue` (whole queue), or `off` |
| `/retry` | Retry playing the current song if it failed |
| `/help` | Show the command list |

### Now-playing controls

The `/nowplaying` message includes interactive buttons:

- Play/Pause
- Skip
- Stop
- Loop toggle
- Shuffle

Only functional control emojis are used. Decorative emojis have been removed from embeds and messages.

### Queue management

- `/playnext` inserts songs at the front of the queue. If nothing is playing, it starts immediately.
- `/skipto` drops the songs before the target position and starts playing it.
- `/shuffle` only affects queued songs, not the currently playing track.
- `/queue` shows the current track, the upcoming lineup, and the total remaining duration.

### Error handling

When a song fails to play, the bot automatically retries up to 3 times with exponential backoff (1s, 2s, 4s) before giving up. Retryable errors include network timeouts and stream failures.

After all retries are exhausted, the bot stops playback and shows a specific error message explaining what went wrong:

| Error | Message |
|---|---|
| Video unavailable | Song is no longer available on YouTube |
| Region-locked | Song isn't available in your region |
| Age-restricted | Video is age-restricted and cannot be played |
| Auth failure | YouTube cookies need to be refreshed |
| Format error | No playable audio format available |
| Network error | Connection issue detected |

After a final failure, use `/retry` to try the same song again or `/skip` to move to the next track.

### Auto-disconnect

The bot automatically leaves the voice channel if it's left alone.

## Project structure

The bot is split into focused modules:

| File | Responsibility |
|---|---|
| `bot.py` | Entry point, events, token loading |
| `commands.py` | Slash command handlers |
| `player.py` | Playback engine, progress loop, voice helpers |
| `views.py` | Now-playing buttons and search picker |
| `song.py` | Song model and yt-dlp lookup |
| `audio.py` | yt-dlp → FFmpeg audio source |
| `state.py` | Per-guild playback state |
| `errors.py` | Media error classification |
| `persona.py` | Randomized Alex Jones-style response pools |
| `config.py` | Constants, yt-dlp/FFmpeg options, logging |
| `utils.py` | Formatting helpers |

## Persona

Command responses use randomized quotes from `persona.py`. The tone is Alex Jones / InfoWars broadcast energy: globalists, the resistance, transmissions, 1776, etc. The responses are unfiltered for private server use.

## Logging

All errors and retry attempts are logged to `bot.log` with automatic rotation (10MB max, 5 backups). Use the log to diagnose persistent playback issues.

## Requirements

- Python 3.10+
- FFmpeg installed and available on your PATH
- Deno installed and available on your PATH (used by yt-dlp to solve YouTube's JS challenges)
- A Discord bot token
- A YouTube cookies file (to bypass YouTube bot detection)

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/BingleP/LiberalBot.git
cd LiberalBot
```

### 2. Create a virtual environment and install dependencies

```bash
python3.12 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install FFmpeg

- **Arch/CachyOS:** `sudo pacman -S ffmpeg`
- **Ubuntu/Debian:** `sudo apt install ffmpeg`
- **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **macOS:** `brew install ffmpeg`

### 4. Install Deno

- **Arch/CachyOS:** `sudo pacman -S deno`
- **Linux/macOS:** `curl -fsSL https://deno.land/install.sh | sh`
- **Windows:** `irm https://deno.land/install.ps1 | iex`

### 5. Export YouTube cookies

YouTube requires authentication to serve audio streams. Export your cookies from a browser where you're logged into YouTube:

```bash
yt-dlp --cookies-from-browser firefox --cookies cookies.txt --skip-download "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Then update the `YT_COOKIE_FILE` path in `config.py` to point to your cookies file. Cookies expire periodically and will need to be re-exported when they do.

### 6. Configure your bot token

Create a `.env` file in the project root (see `.env.example`):

```
DISCORD_TOKEN=your_bot_token_here
```

### 7. Configure your guild ID

In `bot.py`, update the `GUILD` variable with your server's ID:

```python
GUILD = discord.Object(id=YOUR_GUILD_ID_HERE)
```

### 8. Set up the Discord application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and add a Bot
3. Under **Privileged Gateway Intents**, enable **Message Content Intent**
4. Invite the bot to your server with the `bot` and `applications.commands` scopes and `Connect` + `Speak` voice permissions

### 9. Run the bot

```bash
python bot.py
```

Slash commands are synced to your guild automatically on startup.
