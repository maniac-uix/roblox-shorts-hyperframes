#!/usr/bin/env python3
"""music-attribution.py — the music attribution text for a video description.

Reads the music entry of config/factory.json and prints the exact text to
copy into the video description (TikTok / YouTube Shorts / Instagram Reels).
No invented credit: if the track has no licence or no author in the config,
the script FAILS instead of printing a guess.

Usage: python3 pipeline/music-attribution.py [--output attribution.txt]
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output")
    args = ap.parse_args()
    cfg = json.loads((PROJECT / "config" / "factory.json").read_text())
    music = cfg.get("music", {})
    for key in ("title", "artist", "license", "source"):
        if not music.get(key):
            print(f"ERROR: config/factory.json music.{key} is missing — "
                  f"cannot print an attribution without inventing it.",
                  file=sys.stderr)
            return 1
    text = (f"Music: {music['title']} by {music['artist']} "
            f"({music['source']}), {music['license']}")
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n")
        print(f"  saved to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
