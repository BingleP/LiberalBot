# LiberalBot

A Discord music bot that plays audio from YouTube into voice channels using slash commands.

## Features

| Command | Description |
|---|---|
| `/play <query>` | Play a song by name, YouTube URL, or playlist URL |
| `/skip` | Skip the current song |
| `/queue` | Show the current queue (up to 20 entries) |
| `/nowplaying` | Show what's currently playing |
| `/pause` | Pause playback |
| `/resume` | Resume paused playback |
| `/stop` | Stop playback and disconnect the bot |
| `/remove <position>` | Remove a song from the queue by position |
| `/clear` | Clear the queue without stopping the current song |
| `/loop <mode>` | Set loop mode: `one` (current song), `queue` (whole queue), or `off` |

**Auto-disconnect:** The bot will automatically leave the voice channel if it's left alone.

## Requirements

- Python 3.10+
- FFmpeg installed and available on your PATH
- A Discord bot token

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/BingleP/LiberalBot.git
cd LiberalBot
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install discord.py yt-dlp
```

### 3. Install FFmpeg

- **Arch/CachyOS:** `sudo pacman -S ffmpeg`
- **Ubuntu/Debian:** `sudo apt install ffmpeg`
- **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **macOS:** `brew install ffmpeg`

### 4. Configure your bot token

Create a `.env` file in the project root:

```
DISCORD_TOKEN=your_bot_token_here
```

### 5. Configure your guild ID

In `bot.py`, update the `GUILD` variable with your server's ID:

```python
GUILD = discord.Object(id=YOUR_GUILD_ID_HERE)
```

### 6. Set up the Discord application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and add a Bot
3. Under **Privileged Gateway Intents**, enable **Message Content Intent**
4. Invite the bot to your server with the `bot` and `applications.commands` scopes and `Connect` + `Speak` voice permissions

### 7. Run the bot

```bash
python bot.py
```

Slash commands are synced to your guild automatically on startup.
