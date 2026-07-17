import subprocess
import discord

from config import YT_COOKIE_FILE


class YTDLSource(discord.AudioSource):
    def __init__(self, url: str):
        self.url = url
        self._process: subprocess.Popen | None = None
        self._ffmpeg: subprocess.Popen | None = None
        self._buffer = b""
        self._started = False

    def start(self):
        ytdl_cmd = [
            "yt-dlp", "-f", "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best",
            "-o", "-", "-q", "--no-warnings",
            "--cookies", YT_COOKIE_FILE,
            "--extractor-args", "youtube:player_client=web,ios",
            self.url,
        ]
        self._process = subprocess.Popen(ytdl_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        ffmpeg_cmd = [
            "ffmpeg", "-i", "pipe:0", "-vn",
            "-f", "s16le", "-ar", "48000", "-ac", "2",
            "-loglevel", "quiet",
            "pipe:1",
        ]
        self._ffmpeg = subprocess.Popen(
            ffmpeg_cmd,
            stdin=self._process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        if self._process.stdout:
            self._process.stdout.close()
        self._started = True

    def read(self) -> bytes:
        if not self._started:
            self.start()
        if self._ffmpeg is None or self._ffmpeg.stdout is None:
            return b""

        target = discord.opus.Encoder.FRAME_SIZE
        while len(self._buffer) < target:
            chunk = self._ffmpeg.stdout.read(target - len(self._buffer))
            if not chunk:
                break
            self._buffer += chunk

        if not self._buffer:
            reasons = []
            if self._process and self._process.poll() is not None and self._process.returncode != 0:
                reasons.append(f"yt-dlp (exit {self._process.returncode})")
            if self._ffmpeg and self._ffmpeg.poll() is not None and self._ffmpeg.returncode != 0:
                reasons.append(f"ffmpeg (exit {self._ffmpeg.returncode})")
            if reasons:
                raise RuntimeError("Audio source failed: " + "; ".join(reasons))
            return b""

        if len(self._buffer) < target:
            data = self._buffer
            self._buffer = b""
            return data

        data = self._buffer[:target]
        self._buffer = self._buffer[target:]
        return data

    def is_opus(self) -> bool:
        return False

    def cleanup(self):
        for proc in (self._ffmpeg, self._process):
            if proc and proc.poll() is None:
                proc.kill()
                proc.wait()
