#!/usr/bin/env python3
"""write-publish-md.py — publish.md GENERATOR (for future videos) + checker.

Generation assembles publish.md from videos/<slug>/metadata.json
(script, captions), pipeline/<slug>/attribution.txt (Kevin MacLeod
CC BY 3.0 text — the file's content, never invented) and the given
--title. Structure mirrors the existing v4 publish.md files:
  "# Publish — <title> (<Format> <version?>)"
  "## Title (<N> characters)" + title
  "## Description (YouTube Shorts)" + description
  "## TikTok / Reels caption" + caption
  "## Share line" + "Send this to a friend who plays Roblox"
Description = the script sentences (asterisks stripped) as the body
+ "From noob to pro. New Roblox videos every week!"
+ the fan-made / not-affiliated line
+ the attribution.txt content
+ hashtags (format-specific, max 5).
TikTok caption default: the hook sentence + format tags, truncated to
150 chars.

VALIDATES before writing (refuses, exit 1, if any fails):
  title <= 60 chars; description contains "not affiliated with or
  endorsed by Roblox"; description contains "Kevin MacLeod" and
  "CC BY 3.0"; hashtags <= 5; TikTok caption present; share line
  exactly "Send this to a friend who plays Roblox".

--check mode reads an existing publish.md and verifies the same five
elements, printing PASS/FAIL per element; exit 0 iff all pass.

Usage:
  write-publish-md.py --slug <slug> --title "<title, <= 60 chars>"
      [--tiktok-caption "<short caption>"]
      [--output pipeline/<slug>/publish.md]
  write-publish-md.py --check pipeline/<slug>/publish.md
"""
import argparse
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
PIPELINE = PROJECT / "pipeline"
VIDEOS = PROJECT / "videos"

FANMADE = ("Fan-made channel, not affiliated with or endorsed by Roblox "
           "Corporation. Roblox is a trademark of Roblox Corporation.")
TAGLINE = "From noob to pro. New Roblox videos every week!"
SHARE = "Send this to a friend who plays Roblox"
MAX_TITLE = 60
MAX_TIKTOK = 150

HASHTAGS = {
    "facts": ["#Roblox", "#RobloxFacts", "#Shorts", "#Gaming", "#NoobNoMore"],
    "mysteries": ["#Roblox", "#RobloxMystery", "#Shorts", "#Gaming",
                  "#NoobNoMore"],
    "top5": ["#Roblox", "#RobloxFacts", "#Shorts", "#Gaming", "#NoobNoMore"],
    "game-discoveries": ["#Roblox", "#RobloxFacts", "#Shorts", "#Gaming",
                         "#NoobNoMore"],
}
TIKTOK_TAGS = {
    "facts": "#Roblox #RobloxFacts #NoobNoMore",
    "mysteries": "#Roblox #RobloxMystery #NoobNoMore",
    "top5": "#Roblox #RobloxFacts #NoobNoMore",
    "game-discoveries": "#Roblox #RobloxFacts #NoobNoMore",
}
DISPLAY_FORMAT = {
    "facts": "Facts", "mysteries": "Mysteries", "top5": "Top 5",
    "game-discoveries": "Game Discoveries",
    "hidden-secrets": "Hidden Secrets", "updates": "Updates",
    "stories": "Stories",
}


def split_sentences(text: str) -> list:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip())
            if s.strip()]


def get_format(slug: str) -> str:
    fmt_path = PIPELINE / slug / "format.txt"
    if fmt_path.exists():
        return fmt_path.read_text().strip()
    meta_path = VIDEOS / slug / "metadata.json"
    if meta_path.exists():
        tpl = json.loads(meta_path.read_text()).get("template", "")
        m = re.search(r"formats/([a-z-]+)\.html", tpl)
        if m:
            return m.group(1)
    return "facts"


def get_version(slug: str) -> str:
    m = re.search(r"-v(\d+)$", slug)
    return f"v{m.group(1)}" if m else ""


def hashtags_for(fmt: str) -> list:
    return HASHTAGS.get(fmt, HASHTAGS["facts"])


def tiktok_caption_for(fmt: str, hook: str, override=None) -> str:
    if override:
        caption = override.strip()
    else:
        tags = TIKTOK_TAGS.get(fmt, TIKTOK_TAGS["facts"])
        caption = f"{hook} {tags}"
    if len(caption) > MAX_TIKTOK:
        tags = TIKTOK_TAGS.get(fmt, TIKTOK_TAGS["facts"])
        room = MAX_TIKTOK - len(tags) - 1
        caption = f"{hook[:room].rstrip()} {tags}"
    return caption


def build_publish_md(slug: str, title: str, tiktok_caption=None) -> str:
    meta = json.loads((VIDEOS / slug / "metadata.json").read_text())
    script = meta.get("script", "").replace("*", "")
    sents = split_sentences(script)
    body = " ".join(sents)
    attribution = (PIPELINE / slug / "attribution.txt").read_text().strip()
    fmt = get_format(slug)
    tags = hashtags_for(fmt)
    hook = sents[0] if sents else ""
    caption = tiktok_caption_for(fmt, hook, tiktok_caption)
    version = get_version(slug)
    header = f"# Publish — {title} ({DISPLAY_FORMAT.get(fmt, fmt)}" \
        + (f" {version}" if version else "") + ")"
    description = "\n\n".join([body, TAGLINE, FANMADE, attribution,
                                " ".join(tags)])
    return (f"{header}\n\n"
            f"## Title ({len(title)} characters)\n\n{title}\n\n"
            f"## Description (YouTube Shorts)\n\n{description}\n\n"
            f"## TikTok / Reels caption\n\n{caption}\n\n"
            f"## Share line\n\n{SHARE}\n")


def parse_publish_md(text: str) -> dict:
    """Split a publish.md into {title, description, tiktok, share}."""
    sections = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"##\s+(.+)", line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    def section(name):
        for key, lines in sections.items():
            if key.lower().startswith(name):
                return "\n".join(lines).strip()
        return ""
    title_lines = [ln.strip() for ln in
                   section("title").splitlines() if ln.strip()]
    return {"title": title_lines[0] if title_lines else "",
            "description": section("description"),
            "tiktok": section("tiktok"),
            "share": section("share line")}


def validate_parts(title: str, description: str, tiktok: str,
                   share: str) -> dict:
    """The five elements (attribution split out for clarity)."""
    tags = re.findall(r"#\w+", description)
    return {
        "title_length": {
            "pass": len(title) <= MAX_TITLE,
            "detail": f"title is {len(title)} chars (max {MAX_TITLE})"},
        "fan_made": {
            "pass": "not affiliated with or endorsed by Roblox"
                    in description,
            "detail": "description contains the not-affiliated line"},
        "music_attribution": {
            "pass": "Kevin MacLeod" in description
                    and "CC BY 3.0" in description,
            "detail": "description contains 'Kevin MacLeod' and "
                      "'CC BY 3.0'"},
        "hashtags": {
            "pass": len(tags) <= 5,
            "detail": f"{len(tags)} hashtag(s) in description (max 5): "
                      f"{' '.join(tags)}"},
        "tiktok_caption": {
            "pass": bool(tiktok.strip()),
            "detail": "TikTok / Reels caption present"},
        "share_line": {
            "pass": share.strip() == SHARE,
            "detail": f"share line is exactly {SHARE!r}"},
    }


def generate(slug: str, title: str, tiktok_caption, output: Path) -> int:
    text = build_publish_md(slug, title, tiktok_caption)
    parts = parse_publish_md(text)
    checks = validate_parts(parts["title"], parts["description"],
                            parts["tiktok"], parts["share"])
    failed = [k for k, v in checks.items() if not v["pass"]]
    for k, v in checks.items():
        print(f"  [{'PASS' if v['pass'] else 'FAIL'}] {k}: {v['detail']}")
    if failed:
        print(f"publish.md NOT written — validation failed: "
              f"{', '.join(failed)}", file=sys.stderr)
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text)
    print(f"publish.md written: {output}")
    return 0


def check_file(path: Path) -> int:
    parts = parse_publish_md(path.read_text())
    checks = validate_parts(parts["title"], parts["description"],
                            parts["tiktok"], parts["share"])
    print(f"publish.md check: {path}")
    print(f"  title: {parts['title']!r}")
    for k, v in checks.items():
        print(f"  [{'PASS' if v['pass'] else 'FAIL'}] {k}: {v['detail']}")
    ok = all(v["pass"] for v in checks.values())
    print(f"  verdict: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug")
    ap.add_argument("--title")
    ap.add_argument("--tiktok-caption")
    ap.add_argument("--check")
    ap.add_argument("--output")
    args = ap.parse_args()
    if args.check:
        return check_file(Path(args.check))
    if not args.slug or not args.title:
        ap.error("--slug and --title are required to generate publish.md")
    output = Path(args.output) if args.output else \
        PIPELINE / args.slug / "publish.md"
    return generate(args.slug, args.title, args.tiktok_caption, output)


if __name__ == "__main__":
    sys.exit(main())
