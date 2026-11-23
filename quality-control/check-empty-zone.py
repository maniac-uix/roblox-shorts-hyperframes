#!/usr/bin/env python3
"""check-empty-zone.py — empty image zone (Phase 4C).

Samples the image-card probe crop (see frame_probe.py) at 10 fps and
flags frames where the card is empty: "empty" = grey stddev of the
card crop < 12.0. Reports every maximal empty span (start, end,
duration). FAIL if any span is longer than 0.2 s — at 0.1 s resolution
this means a measured span >= 0.3 s. The first 0.2 s of the video is
included in the measurement (t=0 counts).

Calibration (23 Nov 2026): empty frames stddev 5.9-10.1, image frames
>= ~17. Expected empty spans: Mysteries v4 approx (0.0,0.3),
(6.9,7.4), (13.0,13.5), (19.2,19.7), (28.9,29.3) — max 0.5 s;
Facts v4 approx (0.0,0.1), (2.4,2.6), (8.6,8.8), (11.9,12.2),
(20.0,20.4), (27.4,27.8) — max 0.4 s.

Usage:
  python3 quality-control/check-empty-zone.py --mp4 output/<slug>.mp4 \
      [--output JSON] [--fps 10] [--std-threshold 12.0]
      [--max-empty-s 0.2]

Output: one JSON object on stdout (last line) plus a human summary line.
Exit 0 iff verdict PASS.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame_probe import extract_frames, gray_std, video_duration


def empty_spans(samples, std_threshold, dt):
    """Maximal spans of consecutive empty samples.

    Each span is {start_s, end_s, duration_s} with end_s exclusive
    (last empty frame t + dt).
    """
    spans = []
    cur = None
    for t, std in samples:
        if std < std_threshold:
            if cur is None:
                cur = {"start_s": t, "end_s": t + dt, "n_frames": 1}
            else:
                cur["end_s"] = t + dt
                cur["n_frames"] += 1
        else:
            if cur is not None:
                spans.append(cur)
                cur = None
    if cur is not None:
        spans.append(cur)
    return [{"start_s": round(s["start_s"], 2),
             "end_s": round(s["end_s"], 2),
             "duration_s": round(s["end_s"] - s["start_s"], 2),
             "n_frames": s["n_frames"]} for s in spans]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True)
    ap.add_argument("--output")
    ap.add_argument("--fps", type=float, default=10.0)
    ap.add_argument("--std-threshold", type=float, default=12.0)
    ap.add_argument("--max-empty-s", type=float, default=0.2)
    args = ap.parse_args()

    duration = video_duration(args.mp4)
    dt = 1.0 / args.fps
    samples = [(t, gray_std(img))
               for t, img in extract_frames(args.mp4, args.fps)]
    spans = empty_spans(samples, args.std_threshold, dt)
    max_empty = max((s["duration_s"] for s in spans), default=0.0)
    verdict = "PASS" if max_empty <= args.max_empty_s else "FAIL"
    result = {
        "mp4": str(args.mp4),
        "duration_s": round(duration, 3),
        "fps": args.fps,
        "std_threshold": args.std_threshold,
        "empty_spans": spans,
        "max_empty_s": max_empty,
        "verdict": verdict,
    }
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
    print(f"EMPTY ZONE: {verdict} — max empty span {max_empty:.1f} s "
          f"(limit {args.max_empty_s:.1f} s), {len(spans)} span(s), "
          f"duration {duration:.2f} s")
    print(json.dumps(result))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
