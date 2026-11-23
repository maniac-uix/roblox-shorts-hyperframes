#!/usr/bin/env python3
"""check-visual-change.py — visual-change detection for the ROBLOX VIDEO
FACTORY (Phase 4B).

Detects visual changes with ffmpeg frame difference
(``fps=2,select='gt(scene,T)',showinfo``) and computes the longest
stretch of video with NO visual change — the max gap between
consecutive changes, including from 0.0 to the first change and from
the last change to the video end. A motion-rich video changes visuals
every 1-1.5 s (AGENTS.md §4); a frozen card or a static clip has a
max gap close to the video length.

Why fps=2 frame difference, not full-fps scdet (calibration, 23 Nov 2026):
full-fps ``select='gt(scene,T)'`` at T = 0.05/0.08/0.10/0.15 on the 5
existing good videos finds 0-7 changes and max gaps of 10.3-41.8 s —
at T >= 0.08 it finds literally nothing on any good video, because
this factory's motion is smooth slides/zooms, not hard cuts, so the
per-frame (1/30 s) difference never reaches 0.08. Comparing frames
0.5 s apart (fps=2) measures the change the viewer actually sees.
At fps=2, T = 0.01, the 5 good videos give 34-46 changes with max
gaps 3.50-4.50 s, while a 10 s static clip (black, or a frozen frame)
gives 0 changes and max gap = 10.00 s (the full duration). But facts
fails the 4.0 s limit (4.50 s) and top5 / throw-food sit exactly ON it
(4.00 s, zero margin), so the control is a WARNING, not a blocker —
see gate.py. No threshold separates all 5 good videos from frozen
with margin.

Usage:
  python3 quality-control/check-visual-change.py --mp4 output/<slug>.mp4 \
      [--threshold 0.01] [--max-gap 4.0]

Output: one JSON object on stdout (last line) plus a human line:
  {"mp4": ..., "duration_s": ..., "threshold": ..., "max_gap_s": ...,
   "n_changes": ..., "changes_s": [...], "verdict": "PASS"|"FAIL"}
Exit 0 when max_gap_s <= --max-gap, 1 otherwise. The gate decides
whether that exit code blocks delivery (Phase 4B: it does NOT — the
check is recorded as a warning, see gate.py).
"""
import argparse
import json
import re
import subprocess
import sys


def video_duration(mp4: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", mp4],
        text=True, capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"ffprobe failed on {mp4}: {r.stderr.strip()}")
    return float(json.loads(r.stdout)["format"]["duration"])


def scene_changes(mp4: str, threshold: float) -> list:
    """Timestamps (s) of 0.5 s-apart frame pairs whose scene score
    exceeds the threshold. Decimating to 2 fps first makes the score
    measure change over 0.5 s (what the viewer sees), not over 1/30 s.
    The first frame (t=0) always scores above any threshold, so it is
    dropped — the 0.0 -> first-change gap is measured from 0.0 instead.
    """
    vf = f"fps=2,select='gt(scene,{threshold})',showinfo"
    r = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", mp4, "-vf", vf,
         "-f", "null", "-"],
        text=True, capture_output=True)
    times = []
    for m in re.finditer(r"pts_time:([0-9.]+)", r.stderr or ""):
        t = float(m.group(1))
        if t > 0.05:
            times.append(round(t, 3))
    return sorted(set(times))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True)
    ap.add_argument("--threshold", type=float, default=0.01)
    ap.add_argument("--max-gap", type=float, default=4.0)
    args = ap.parse_args()

    duration = video_duration(args.mp4)
    changes = scene_changes(args.mp4, args.threshold)
    bounds = [0.0] + changes + [duration]
    gaps = [round(b - a, 3) for a, b in zip(bounds, bounds[1:])]
    max_gap = max(gaps) if gaps else duration
    verdict = "PASS" if max_gap <= args.max_gap else "FAIL"
    result = {
        "mp4": str(args.mp4),
        "duration_s": round(duration, 3),
        "threshold": args.threshold,
        "max_gap_s": max_gap,
        "n_changes": len(changes),
        "changes_s": changes,
        "max_gap_limit_s": args.max_gap,
        "verdict": verdict,
    }
    print(f"VISUAL CHANGE: {verdict} — max gap {max_gap:.2f} s "
          f"(limit {args.max_gap:.1f} s), {len(changes)} changes, "
          f"threshold {args.threshold} (fps=2 frame-diff), "
          f"duration {duration:.2f} s")
    print(json.dumps(result))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
