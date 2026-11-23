#!/usr/bin/env python3
"""check-brand.py — watermark + final mascot (Phase 4C).

Parses the built composition HTML (videos/<slug>/index.html) and
checks the brand elements in the pixels:

- Watermark: declared font-size from the `.watermark { ... font-size:
  Npx` CSS rule; blocking threshold >= 36 px. Presence: sample frames
  at t = 1.0, 5.0, mid, end-1.0 s; count watermark-coloured pixels in
  the top-right zone (RGB distance < 60 from (31, 209, 193)); present
  iff the median count is >= 50. The median glyph bbox height (px,
  half scale) is reported as evidence only — the blocking size
  comparison is the DECLARED font-size, never the pixel height.
- Mascot: declared width from `.mascot { ... width: Npx`, left/top
  from the `#mascot` inline style (or the .mascot rule); blocking
  threshold >= 220 px. Presence: on frames in the last 2 s of the
  video, masked NCC vs the downscaled mascot PNG at the declared box;
  present iff the median NCC is >= 0.5.

If the composition file does not exist: verdict N/A, reason "no
composition available (pre-v4 video)", exit 0 (N/A never blocks).
If the composition has no .watermark rule at all (template predates
brand): verdict N/A, reason "template predates brand (no watermark in
composition)", exit 0.

Calibration (23 Nov 2026, v4 videos): watermark present (~269 px,
glyph height 9 px half scale), declared 30 px -> FAIL on size;
mascot present (NCC 0.953), declared 240 px -> PASS on size. Overall
brand verdict on v4 MUST be FAIL (watermark 30 < 36). The 36 px
threshold is never weakened to manufacture a pass.

Usage:
  python3 quality-control/check-brand.py --mp4 output/<slug>.mp4 \
      --metadata videos/<slug>/metadata.json \
      --composition videos/<slug>/index.html [--output JSON]

Output: one JSON object on stdout (last line) plus a human summary line.
Exit 0 iff PASS or N/A, 1 iff FAIL.
"""
import argparse
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame_probe import (MASCOT_DEFAULT_BOX_FULL, extract_at_times,
                         mascot_ncc, video_duration, watermark_glyph_height,
                         watermark_pixels)

WATERMARK_MIN_FONT_PX = 36
WATERMARK_MIN_MEDIAN_PX = 50
MASCOT_MIN_WIDTH_PX = 220
MASCOT_MIN_NCC = 0.5
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MASCOT_PNG = os.path.join(
    PROJECT_ROOT, "assets", "brand", "noobnomore-mascot-transparent.png")


def _css_rule(html, selector):
    """Body of the first `.selector { ... }` rule, or None."""
    m = re.search(r"\." + re.escape(selector) + r"\s*\{([^}]*)\}",
                  html, re.S)
    return m.group(1) if m else None


def _px(rule_body, prop):
    """Numeric px value of `prop: Npx` inside a CSS rule body, or None."""
    if not rule_body:
        return None
    m = re.search(re.escape(prop) + r"\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*px",
                  rule_body)
    return float(m.group(1)) if m else None


def _median(values):
    vals = sorted(values)
    n = len(vals)
    if n == 0:
        return 0.0
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2


def parse_composition(html):
    """Declared brand sizes/positions from the composition HTML."""
    wm_rule = _css_rule(html, "watermark")
    mascot_rule = _css_rule(html, "mascot")
    font_px = _px(wm_rule, "font-size")
    width_px = _px(mascot_rule, "width")
    left = _px(mascot_rule, "left")
    top = _px(mascot_rule, "top")
    # #mascot inline style wins for left/top when present.
    m = re.search(r'<[^>]*\bid=["\']mascot["\'][^>]*\bstyle=["\']([^"\']*)',
                  html)
    if m:
        style = m.group(1)
        left_s = _px(style, "left")
        top_s = _px(style, "top")
        if left_s is not None:
            left = left_s
        if top_s is not None:
            top = top_s
    if left is None:
        left = MASCOT_DEFAULT_BOX_FULL[0]
    if top is None:
        top = MASCOT_DEFAULT_BOX_FULL[1]
    if width_px is None:
        width_px = MASCOT_DEFAULT_BOX_FULL[2]
    return {"has_watermark_rule": wm_rule is not None,
            "watermark_font_px": font_px,
            "mascot_width_px": width_px,
            "mascot_left": left, "mascot_top": top}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True)
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--composition", required=True)
    ap.add_argument("--mascot-png", default=DEFAULT_MASCOT_PNG)
    ap.add_argument("--output")
    args = ap.parse_args()

    if not args.composition or not os.path.exists(args.composition):
        result = {"mp4": str(args.mp4), "verdict": "N/A",
                  "reason": "no composition available (pre-v4 video)"}
        print("BRAND: N/A — no composition available (pre-v4 video)")
        print(json.dumps(result))
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
        return 0

    with open(args.composition) as f:
        html = f.read()
    decl = parse_composition(html)
    if not decl["has_watermark_rule"]:
        result = {"mp4": str(args.mp4), "verdict": "N/A",
                  "reason": "template predates brand "
                            "(no watermark in composition)"}
        print("BRAND: N/A — template predates brand "
              "(no watermark in composition)")
        print(json.dumps(result))
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
        return 0

    duration = video_duration(args.mp4)

    # Watermark presence at t = 1.0, 5.0, mid, end-1.0.
    wm_times = sorted({1.0, 5.0, round(duration / 2, 2),
                       round(duration - 1.0, 2)})
    wm_counts, wm_heights = [], []
    for t, img in extract_at_times(args.mp4, wm_times):
        if img is None:
            continue
        wm_counts.append(watermark_pixels(img))
        wm_heights.append(watermark_glyph_height(img))
    median_px = _median(wm_counts)
    median_height = _median(wm_heights)
    wm_present = median_px >= WATERMARK_MIN_MEDIAN_PX

    # Mascot presence on frames in the last 2 s.
    mas_times = [round(duration - 1.5, 2), round(duration - 1.0, 2),
                 round(duration - 0.5, 2)]
    box = (decl["mascot_left"], decl["mascot_top"],
           decl["mascot_width_px"], decl["mascot_width_px"])
    nccs = []
    for t, img in extract_at_times(args.mp4, mas_times):
        if img is None:
            continue
        nccs.append(mascot_ncc(img, args.mascot_png, box))
    median_ncc = _median(nccs)
    mascot_present = median_ncc >= MASCOT_MIN_NCC

    wm_size_ok = (decl["watermark_font_px"] is not None
                  and decl["watermark_font_px"] >= WATERMARK_MIN_FONT_PX)
    mascot_size_ok = (decl["mascot_width_px"] is not None
                      and decl["mascot_width_px"] >= MASCOT_MIN_WIDTH_PX)
    verdict = ("PASS" if (wm_size_ok and wm_present and mascot_size_ok
                          and mascot_present) else "FAIL")
    result = {
        "mp4": str(args.mp4),
        "watermark": {
            "declared_font_px": decl["watermark_font_px"],
            "present": wm_present,
            "median_px": median_px,
            "median_glyph_height_half_px": median_height,
        },
        "mascot": {
            "declared_width_px": decl["mascot_width_px"],
            "present": mascot_present,
            "median_ncc": round(median_ncc, 3),
        },
        "verdict": verdict,
    }
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
    print(f"BRAND: {verdict} — watermark declared "
          f"{decl['watermark_font_px']} px (>= {WATERMARK_MIN_FONT_PX}: "
          f"{'yes' if wm_size_ok else 'no'}), present "
          f"(median {median_px:.0f} px, glyph {median_height:.0f} px half-scale: "
          f"{'yes' if wm_present else 'no'}); mascot declared "
          f"{decl['mascot_width_px']} px (>= {MASCOT_MIN_WIDTH_PX}: "
          f"{'yes' if mascot_size_ok else 'no'}), present "
          f"(median NCC {median_ncc:.3f}: "
          f"{'yes' if mascot_present else 'no'})")
    print(json.dumps(result))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
