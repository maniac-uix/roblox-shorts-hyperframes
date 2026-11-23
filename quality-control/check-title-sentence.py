#!/usr/bin/env python3
"""check-title-sentence.py — title/sentence match + title timing gate (Phase 4C).

For every script sentence (metadata.json captions), the on-screen title
of the sentence's scene must share at least one content word with the
sentence, and the title must appear no more than 0.3 s after the
sentence starts (appearing before the sentence is fine).

Method:
  - Scene windows: <div class="scene clip" data-start data-duration>
    in document order (videos/<slug>/index.html).
  - Scene k's title: title-k if present, else head-k (num-k, label-k,
    q-k are numbers/labels/decoration, never titles; sub-k is a
    subtitle, never the title). A scene with neither reports title None
    and its sentences FAIL the match ("no title in scene").
  - Sentences come from metadata.json["captions"]; a sentence belongs
    to the scene whose window contains its start (a start exactly on a
    boundary belongs to the scene starting there).
  - MATCH: tokenize title and sentence (lowercase, strip * and
    punctuation, keep digits, map number-words to digits), drop
    stopwords. A title word matches a sentence word if equal, or one
    is a prefix of the other and the longer is >= 4 chars (covers
    hack/hacker, kid/kids, player/players, block/blocks,
    legend/legends). Match = at least one shared content word.
  - TIMING: first GSAP tween position for the title element id in the
    composition script block (the entrance). No tween: scene 0 means
    visible from t=0 (appearance 0.0); any other scene means timing N/A.
    Timing PASS iff appearance - sentence_start <= 0.3 s.

If the composition file does not exist: verdict N/A, exit 0 (N/A never
blocks).

Usage:
  check-title-sentence.py --mp4 <final.mp4> --metadata videos/<slug>/metadata.json
      --composition videos/<slug>/index.html [--output report.json]

Exit 0 iff PASS or N/A, else 1. The JSON report is the last stdout line.
"""
import argparse
import json
import re
import sys
from pathlib import Path

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been",
    "it", "its", "this", "that", "these", "those", "and", "or",
    "but", "so", "to", "of", "in", "on", "for", "with", "by", "at",
    "as", "from", "you", "your", "he", "she", "they", "we", "i",
    "did", "do", "does", "can", "could", "will", "would", "not",
    "no", "still", "just", "very", "more", "than", "then", "when",
    "what", "how", "why", "who", "whom",
}

NUMBER_WORDS = {
    "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
    "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety", "hundred", "thousand", "million", "billion",
}

# Single number-words only (magnitudes like hundred/thousand/million/
# billion stay words — they are not digits).
NUMBER_WORD_MAP = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14",
    "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20",
    "thirty": "30", "forty": "40", "fifty": "50", "sixty": "60",
    "seventy": "70", "eighty": "80", "ninety": "90",
}

TIMING_LIMIT_S = 0.3


def tokenize(text: str) -> list:
    """Lowercase tokens; * emphasis stripped, punctuation dropped, digits
    kept as tokens, single number-words mapped to digits."""
    toks = re.findall(r"[a-z0-9]+", text.lower().replace("*", " "))
    return [NUMBER_WORD_MAP.get(t, t) for t in toks]


def content_tokens(text: str) -> list:
    """Tokens with stopwords removed, in order, duplicates kept."""
    return [t for t in tokenize(text) if t not in STOPWORDS]


def _prefix_match(a: str, b: str) -> bool:
    """True if one token is a prefix of the other and the longer token
    is >= 4 chars (so kid/kids matches, but 2-3 letter stems do not)."""
    if a == b:
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    return len(long_) >= 4 and long_.startswith(short)


def match_title_sentence(title: str, sentence: str):
    """(match: bool, shared_words: list) — shared words in title order,
    recorded as the shorter (common-prefix) form on a prefix match."""
    t_toks = content_tokens(title)
    s_toks = content_tokens(sentence)
    shared = []
    for t in t_toks:
        for s in s_toks:
            if _prefix_match(t, s):
                word = t if len(t) <= len(s) else s
                if word not in shared:
                    shared.append(word)
                break
    return bool(shared), shared


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def parse_scenes(html: str) -> list:
    """Scene windows [(start, duration)] in document order."""
    scenes = []
    for m in re.finditer(r'<div[^>]*class="scene clip"[^>]*>', html):
        tag = m.group(0)
        start = re.search(r'data-start="([0-9.]+)"', tag)
        dur = re.search(r'data-duration="([0-9.]+)"', tag)
        if start and dur:
            scenes.append((float(start.group(1)), float(dur.group(1))))
    return scenes


def parse_heads(html: str) -> dict:
    """id -> text for elements with id title-N, head-N or sub-N."""
    heads = {}
    pat = re.compile(
        r'<(h1|h2|p|div)[^>]*\bid="(title|head|sub)-(\d+)"[^>]*>(.*?)</\1>',
        re.DOTALL)
    for m in pat.finditer(html):
        kind, num, inner = m.group(2), m.group(3), m.group(4)
        heads[f"{kind}-{num}"] = strip_html(inner)
    return heads


def parse_appearance(html: str, element_id: str):
    """First GSAP tween position for #<id> (the entrance), or None."""
    pat = re.compile(
        r'tl\.(?:fromTo|to)\("#' + re.escape(element_id) + r'",\s*\{[^}]*\}'
        r'(?:,\s*\{[^}]*\})?,\s*([0-9.]+)\)')
    m = pat.search(html)
    return float(m.group(1)) if m else None


def scene_for(start: float, scenes: list) -> int:
    """Scene whose window contains start; a start exactly on a boundary
    belongs to the scene starting there; past the last end, the last."""
    for i, (s, d) in enumerate(scenes):
        if s <= start < s + d:
            return i
    return len(scenes) - 1


def check(mp4: str, metadata_path: Path, composition_path: Path) -> dict:
    meta = json.loads(metadata_path.read_text())
    captions = meta.get("captions", [])
    if not composition_path.exists():
        return {"verdict": "N/A",
                "reason": "no composition timeline available"}
    html = composition_path.read_text()
    scenes = parse_scenes(html)
    heads = parse_heads(html)

    sentences = []
    for i, cap in enumerate(captions, start=1):
        start, end, text = float(cap["start"]), float(cap["end"]), cap["text"]
        scene = scene_for(start, scenes)
        title_id = None
        title = None
        if f"title-{scene}" in heads:
            title_id, title = f"title-{scene}", heads[f"title-{scene}"]
        elif f"head-{scene}" in heads:
            title_id, title = f"head-{scene}", heads[f"head-{scene}"]
        rec = {"index": i, "start_s": round(start, 2), "end_s": round(end, 2),
               "text": text, "scene": scene, "title": title,
               "title_element": title_id}
        if title is None:
            rec.update({"shared_words": [], "match": False,
                        "match_reason": "no title in scene",
                        "appearance_s": None, "timing_gap_s": None,
                        "timing_verdict": "N/A",
                        "timing_reason": "no title in scene"})
        else:
            match, shared = match_title_sentence(title, text)
            rec["shared_words"] = shared
            rec["match"] = match
            if not match:
                rec["match_reason"] = "no shared content word"
            appearance = parse_appearance(html, title_id)
            if appearance is None and scene == 0:
                appearance = 0.0
                rec["appearance_method"] = \
                    "no entrance tween — visible from t=0"
            if appearance is None:
                rec.update({"appearance_s": None, "timing_gap_s": None,
                            "timing_verdict": "N/A",
                            "timing_reason": "no entrance tween found"})
            else:
                gap = round(appearance - start, 2)
                rec.update({"appearance_s": round(appearance, 2),
                            "timing_gap_s": gap,
                            "timing_verdict": "PASS" if gap <= TIMING_LIMIT_S
                                              else "FAIL"})
        sentences.append(rec)

    mismatches = [s["index"] for s in sentences if not s["match"]]
    late = [s["index"] for s in sentences
            if s["timing_gap_s"] is not None
            and s["timing_gap_s"] > TIMING_LIMIT_S]
    verdict = "FAIL" if (mismatches or late) else "PASS"
    return {"mp4": mp4, "metadata": str(metadata_path),
            "composition": str(composition_path),
            "n_sentences": len(sentences), "sentences": sentences,
            "mismatches": mismatches, "late_titles": late,
            "verdict": verdict}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", default="")
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--composition", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()
    report = check(args.mp4, Path(args.metadata), Path(args.composition))
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=1) + "\n")
    if report["verdict"] == "N/A":
        print(f"title-sentence: N/A — {report['reason']}")
    else:
        sents = report["sentences"]
        print(f"title-sentence: {args.metadata} — {len(sents)} sentences, "
              f"{len(report['mismatches'])} mismatch(es) "
              f"{report['mismatches'] or ''}, "
              f"{len(report['late_titles'])} late title(s) "
              f"{report['late_titles'] or ''} — {report['verdict']}")
        for s in sents:
            timing = (f"gap {s['timing_gap_s']:+.2f}s "
                      f"{s['timing_verdict']}"
                      if s["timing_gap_s"] is not None
                      else f"timing {s['timing_verdict']}")
            print(f"  S{s['index']:>2} scene {s['scene']} "
                  f"[{'OK' if s['match'] else 'MISMATCH'}] "
                  f"{s['text'][:52]!r} | title: {s['title']!r} "
                  f"shared={s['shared_words']} | {timing}")
    print(json.dumps(report))
    return 0 if report["verdict"] in ("PASS", "N/A") else 1


if __name__ == "__main__":
    sys.exit(main())
