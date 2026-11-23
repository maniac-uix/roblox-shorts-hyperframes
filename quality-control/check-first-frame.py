#!/usr/bin/env python3
"""check-first-frame.py — title AND image visible at t=0 (Phase 4C).

Extracts the frames at t=0.0 (first frame) and t=0.1 and checks:

(a) IMAGE: grey stddev of the card probe crop at t=0 must be >= 12.0
    (same "empty" definition as check-empty-zone.py).
(b) TITLE: in the title band (full scale x 120-960, y 340-560;
    half scale 60-480, 170-280) count pixels with luminance > 180
    (white title text on navy). Title visible iff that count is
    >= 200 px at half scale — a 108 px title has thousands of bright
    pixels.

Calibration: on the v4 videos at t=0 the bright-pixel count must be
~0, because the title pop tween starts later with opacity 0 — so the
v4 videos are EXPECTED to FAIL this check on the title (the title is
not yet visible at t=0). FAIL if either the image or the title is
missing at t=0.

Usage:
  python3 quality-control/check-first-frame.py --mp4 output/<slug>.mp4 \
      [--output JSON]

Output: one JSON object on stdout (last line) plus a human summary line.
Exit 0 iff verdict PASS.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame_probe import (EMPTY_STD_THRESHOLD, extract_at_times, gray_std,
                         title_bright_px, video_duration)

TITLE_BRIGHT_MIN_PX = 200


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()

    duration = video_duration(args.mp4)
    frames = dict(extract_at_times(args.mp4, [0.0, 0.1]))
    img0 = frames.get(0.0)
    img01 = frames.get(0.1)
    if img0 is None:
        raise SystemExit(f"could not extract frame at t=0 from {args.mp4}")
    image_std = gray_std(img0)
    bright_px = title_bright_px(img0)
    image_visible = image_std >= EMPTY_STD_THRESHOLD
    title_visible = bright_px >= TITLE_BRIGHT_MIN_PX
    verdict = "PASS" if (image_visible and title_visible) else "FAIL"
    result = {
        "mp4": str(args.mp4),
        "image_std_t0": round(image_std, 2),
        "title_bright_px_t0": bright_px,
        "image_visible": image_visible,
        "title_visible": title_visible,
        "image_std_t01": round(gray_std(img01), 2) if img01 else None,
        "title_bright_px_t01": title_bright_px(img01) if img01 else None,
        "verdict": verdict,
    }
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
    print(f"FIRST FRAME: {verdict} — image std {image_std:.1f} "
          f"(>= {EMPTY_STD_THRESHOLD:.0f}: {'yes' if image_visible else 'no'}), "
          f"title bright px {bright_px} "
          f"(>= {TITLE_BRIGHT_MIN_PX}: {'yes' if title_visible else 'no'})")
    print(json.dumps(result))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
