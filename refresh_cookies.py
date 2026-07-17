#!/usr/bin/env python3
"""Refresh the YouTube cookies file used by LiberalBot from a browser.

Default source is Firefox (configured in .env via YT_COOKIE_BROWSER). Override with
--browser. Supported: firefox, chrome, chromium, edge, brave, opera, vivaldi, whale, safari.
"""

import argparse
import os
import sys
from pathlib import Path

# Load environment variables from .env if present
def load_dotenv(path=".env"):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key not in os.environ:
                    os.environ[key] = value
    except FileNotFoundError:
        pass


load_dotenv()


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_COOKIE_FILE = os.environ.get(
    "YT_COOKIE_FILE", "/home/bingle/Documents/www.youtube.com_cookies.txt"
)
DEFAULT_BROWSER = os.environ.get("YT_COOKIE_BROWSER", "firefox")
DEFAULT_TEST_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def parse_browser_spec(spec: str):
    """Parse 'browser' or 'browser:profile' into a yt-dlp cookiesfrombrowser tuple."""
    parts = spec.split("+", 1)  # keyring override
    keyring = parts[1] if len(parts) > 1 else None
    spec = parts[0]
    parts = spec.split(":", 2)
    browser = parts[0]
    profile = parts[1] if len(parts) > 1 else None
    container = parts[2] if len(parts) > 2 else None
    return browser, profile, keyring, container


def main():
    parser = argparse.ArgumentParser(description="Refresh LiberalBot YouTube cookies from a browser")
    parser.add_argument(
        "--browser",
        default=DEFAULT_BROWSER,
        help="Browser source, e.g. firefox, firefox:profile, chrome, edge (default: %(default)s)",
    )
    parser.add_argument(
        "--cookie-file",
        default=DEFAULT_COOKIE_FILE,
        help="Path to write the Netscape cookies file (default: %(default)s)",
    )
    parser.add_argument(
        "--test-url",
        default=DEFAULT_TEST_URL,
        help="URL to test extraction after refreshing cookies (default: %(default)s)",
    )
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip the post-refresh extraction test",
    )
    args = parser.parse_args()

    browser_spec = parse_browser_spec(args.browser)

    print(f"Refreshing cookies from browser: {args.browser}")
    print(f"Cookie file: {args.cookie_file}")

    try:
        from yt_dlp import YoutubeDL
    except ImportError as e:
        print(f"Error: yt-dlp is not available in this Python environment: {e}")
        return 1

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "cookiesfrombrowser": browser_spec,
        "cookiefile": args.cookie_file,
        "extractor_args": {"youtube": {"player_client": ["web", "ios"]}},
    }

    with YoutubeDL(ydl_opts) as ydl:
        if not args.no_test:
            info = ydl.extract_info(args.test_url, download=False)
            title = info.get("title", "Unknown")
            print(f"Extraction test passed: {title}")
        # cookiejar is saved automatically when the context manager exits

    # Count cookies written
    cookie_count = 0
    if os.path.isfile(args.cookie_file):
        with open(args.cookie_file, encoding="utf-8", errors="replace") as f:
            cookie_count = sum(1 for line in f if line.strip() and not line.startswith("#"))
    print(f"Cookies written to {args.cookie_file}: {cookie_count} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
