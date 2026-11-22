#!/usr/bin/env python3
"""fix-caption-timing.py — re-time the captions of an existing composition.

One-off migration for the v3.1 sync gate (22 Nov 2026): the v3 captions
were timed by COUNT-based slicing of the Whisper word list, which drifted
whenever Whisper's word count differed from the script's ("Brainrot"
heard as "brain rod"), putting later captions up to 2.08 s before the
words they show. This script recomputes the timings by FUZZY alignment
(same logic as the builder now uses) and rewrites ONLY the caption clips
(data-start/data-duration on the track-index=3 divs) and the captions in
metadata.json. Scenes, images, tweens, narration and music are untouched
— the scene still changes at the previous sentence's end (during the
pause); only the caption now appears with its first word.

Usage:
  python3 rendering/fix-caption-timing.py --dir videos/<slug>
"""
import argparse
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "quality-control"))
from caption_timing import corrected_captions  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    args = ap.parse_args()
    d = Path(args.dir)
    meta_path = d / "metadata.json"
    html_path = d / "index.html"
    meta = json.loads(meta_path.read_text())
    wlist = json.loads((d / "transcript.json").read_text())["words"]
    timings = corrected_captions(meta["script"], wlist)
    assert len(timings) == len(meta["captions"]), \
        f"sentence count mismatch: {len(timings)} timings vs {len(meta['captions'])} captions"
    assert all(s is not None for s, _ in timings), "a sentence has no aligned word"
    print(f"{d}: {len(timings)} captions")
    max_delta = 0.0
    for i, ((ns, ne), cap) in enumerate(zip(timings, meta["captions"])):
        delta = ns - cap["start"]
        max_delta = max(max_delta, abs(delta))
        flag = "  <-- MOVED" if abs(delta) > 0.05 else ""
        print(f"  cap {i}: {cap['start']:6.2f}-{cap['end']:6.2f} -> "
              f"{ns:6.2f}-{ne:6.2f} (start {delta:+.2f} s){flag}")
        cap["start"], cap["end"] = round(ns, 2), round(ne, 2)
    meta["captionTimingFix"] = "fuzzy-aligned 22 Nov 2026 (v3.1 sync gate)"
    meta_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n")

    html = html_path.read_text()
    pat = re.compile(
        r'(<div class="clip" data-start=")[0-9.]+(" data-duration=")[0-9.]+(" data-track-index="3")')
    divs = list(pat.finditer(html))
    assert len(divs) == len(timings), \
        f"caption div count mismatch: {len(divs)} divs vs {len(timings)} captions"
    out, pos = [], 0
    for i, m in enumerate(divs):
        ns, ne = timings[i]
        out.append(html[pos:m.start()])
        out.append(f'{m.group(1)}{ns:.2f}{m.group(2)}{ne - ns:.2f}{m.group(3)}')
        pos = m.end()
    out.append(html[pos:])
    html_path.write_text("".join(out))
    print(f"rewrote {len(divs)} caption divs in index.html; "
          f"max |start change| {max_delta:.2f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
