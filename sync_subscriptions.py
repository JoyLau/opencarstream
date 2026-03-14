#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["yt-dlp"]
# ///
"""
Fetch your YouTube subscriptions and write subscriptions.json.

Usage (read cookies directly from your browser — no manual export needed):
  uv run sync_subscriptions.py --browser chrome
  uv run sync_subscriptions.py --browser firefox

Usage (with a manually exported Netscape cookies.txt file):
  uv run sync_subscriptions.py --cookies /path/to/cookies.txt

Supported browser values: chrome, chromium, firefox, brave, edge, opera, safari
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BROWSERS = ["chrome", "chromium", "firefox", "brave", "edge", "opera", "safari"]


def fetch_subscriptions(cookies_args: list[str]) -> list[dict]:
    # /feed/channels lists subscribed channels directly (one entry per channel),
    # avoiding the video-level iteration that /feed/subscriptions triggers.
    r = subprocess.run(
        [
            "yt-dlp",
            *cookies_args,
            "--flat-playlist",
            "--print", "%(id)s\t%(title)s\t%(url)s",
            "--no-warnings",
            "https://www.youtube.com/feed/channels",
        ],
        capture_output=True, text=True, timeout=120,
    )

    if r.returncode != 0:
        err = r.stderr.strip() or "(no stderr)"
        print(f"‼ yt-dlp failed (exit {r.returncode}): {err}", file=sys.stderr)
        sys.exit(1)

    seen: set[str] = set()
    channels = []
    for line in r.stdout.strip().splitlines():
        parts = line.split("\t", 2)
        if len(parts) < 2:
            continue
        name = parts[1].strip()
        # prefer explicit URL (col 3), fall back to building from id (col 1)
        if len(parts) >= 3 and parts[2].strip() and parts[2].strip() != "NA":
            url = parts[2].strip()
        else:
            chan_id = parts[0].strip()
            if not chan_id or chan_id == "NA":
                continue
            url = f"https://www.youtube.com/channel/{chan_id}"
        if not name or name == "NA" or url in seen:
            continue
        seen.add(url)
        channels.append({"name": name, "url": url})

    channels.sort(key=lambda c: c["name"].lower())
    return channels


def main():
    parser = argparse.ArgumentParser(
        description="Sync YouTube subscriptions to subscriptions.json."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--browser", metavar="NAME", choices=BROWSERS,
        help=f"Read cookies directly from browser: {', '.join(BROWSERS)}",
    )
    source.add_argument(
        "--cookies", metavar="FILE",
        help="Path to a Netscape-format cookies.txt file",
    )
    parser.add_argument(
        "--output", default="subscriptions.json", metavar="FILE",
        help="Output path (default: subscriptions.json)",
    )
    args = parser.parse_args()

    if args.cookies:
        cookies_path = Path(args.cookies)
        if not cookies_path.is_file():
            print(f"‼ Cookies file not found: {cookies_path}", file=sys.stderr)
            sys.exit(1)
        cookies_args = ["--cookies", str(cookies_path)]
    else:
        cookies_args = ["--cookies-from-browser", args.browser]

    print("Fetching subscriptions from YouTube…")
    channels = fetch_subscriptions(cookies_args)

    out = {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "channels": channels,
    }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"✔ {len(channels)} channels written to {output_path}")


if __name__ == "__main__":
    main()
