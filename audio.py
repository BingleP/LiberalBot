import os
import subprocess
import sys

import discord

from config import YT_COOKIE_FILE, logger


def _venv_binary(name: str) -> str:
    """Resolve a binary inside the active virtual environment, falling back to PATH."""
    candidate = os.path.join(sys.prefix, "bin", name)
    return candidate if os.path.isfile(candidate) else name


def _build_headers_option(headers: dict[str, str]) -> str:
    """Convert a header dict into an FFmpeg -headers string."""
    lines = [f"{k}: {v}" for k, v in headers.items()]
    return "\r\n".join(lines) + "\r\n" if lines else ""


class YTDLSource(discord.AudioSource):
    def __init__(self, stream_url: str, stream_headers: dict[str, str] | None = None):
        self.stream_url = stream_url
        self.stream_headers = stream_headers or {}
        self._ffmpeg: subprocess.Popen | None = None
        self._buffer = b""
        self._stderr_lines: list[str] = []
        self._start()

    def _start(self):
        if not self.stream_url:
            raise RuntimeError("Audio source failed: no stream URL available")

        headers = dict(self.stream_headers)
        # Ensure a referer is present; YouTube streams often require it.
        if "Referer" not in headers and "referer" not in headers:
            headers["Referer"] = "https://www.youtube.com/"

        user_agent = headers.pop("User-Agent", headers.pop("user-agent", None))
        if not user_agent:
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

        headers_opt = _build_headers_option(headers)

        before_opts = [
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
            "-user_agent", user_agent,
            "-headers", headers_opt,
        ]

        if os.path.isfile(YT_COOKIE_FILE):
            before_opts.extend(["-cookies", YT_COOKIE_FILE])

        ffmpeg_cmd = [
            _venv_binary("ffmpeg"),
            *before_opts,
            "-i", self.stream_url,
            "-vn",
            "-f", "s16le",
            "-ar", "48000",
            "-ac", "2",
            "-loglevel", "error",
            "pipe:1",
        ]

        self._ffmpeg = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _read_stderr(self) -> str:
        """Drain any available stderr output from FFmpeg."""
        if self._ffmpeg is None or self._ffmpeg.stderr is None:
            return ""
        try:
            data = self._ffmpeg.stderr.read(4096).decode("utf-8", errors="replace")
        except (ValueError, AttributeError):
            return ""
        if data:
            self._stderr_lines.append(data)
        return data

    def _ffmpeg_error(self) -> str:
        """Return a formatted error message including FFmpeg stderr."""
        self._read_stderr()
        stderr = "".join(self._stderr_lines).strip()
        if stderr:
            return f"ffmpeg (exit {self._ffmpeg.returncode}): {stderr[:500]}"
        return f"ffmpeg (exit {self._ffmpeg.returncode})"

    def read(self) -> bytes:
        if self._ffmpeg is None or self._ffmpeg.stdout is None:
            return b""

        target = discord.opus.Encoder.FRAME_SIZE
        while len(self._buffer) < target:
            chunk = self._ffmpeg.stdout.read(target - len(self._buffer))
            if not chunk:
                break
            self._buffer += chunk

        if not self._buffer:
            if self._ffmpeg.poll() is not None and self._ffmpeg.returncode != 0:
                raise RuntimeError(f"Audio source failed: {self._ffmpeg_error()}")
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
        if self._ffmpeg and self._ffmpeg.poll() is None:
            self._ffmpeg.kill()
            self._ffmpeg.wait()
