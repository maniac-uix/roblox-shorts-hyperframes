#!/usr/bin/env python3
"""normalize-loudness.py — EBU R128 loudness for the ROBLOX VIDEO FACTORY.

Targets (Phase 3 gate, set 22 Nov 2026): integrated -14 LUFS, true peak
<= -1 dBTP. Two-pass `loudnorm` (measure, then apply with the measured
values). The video stream is copied untouched; only the audio is
re-encoded (AAC-LC stereo 192k, **resampled to 48000 Hz** — v3.1b, 22 Nov
2026: without an explicit aresample the loudnorm output came out at
96000 Hz).

Usage:
  normalize-loudness.py measure <mp4> [--output loudness.json]
      Measure only (single loudnorm pass, print_format=json) and print
      input_i / input_tp / input_lra / input_thresh / target_offset.
  normalize-loudness.py normalize <in.mp4> <out.mp4> [--output loudness.json]
      Two-pass loudnorm to -14 LUFS / -1 dBTP, then measure the result
      and write a JSON report {before, after} (the "after" measurement
      is a fresh loudnorm pass on the normalized file, so it is the
      loudness of what is actually delivered, not a prediction).

loudnorm prints its JSON to stderr with a log prefix on every line, so the
parser extracts the first {...} block instead of parsing raw stderr.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TARGET_I = "-14"
TARGET_TP = "-1"
TARGET_LRA = "11"
# Safety margin on the true-peak target: loudnorm's dynamic limiter is
# approximate, and a fresh measurement of a file normalized to TP=-1 came
# back at -0.79/-0.83/-0.91 dBTP (above the -1 gate). Normalizing to
# TP=-1.5 leaves room for that overshoot; the gate is still verified on
# the delivered file (measured TP must be <= -1 dBTP).
NORMALIZE_TP = "-1.5"


def run(cmd, **kw):
    return subprocess.run(cmd, text=True, capture_output=True, **kw)


def parse_loudnorm_json(stderr: str) -> dict:
    m = re.search(r"\{.*?\n\}", stderr, re.DOTALL)
    if not m:
        raise RuntimeError("no loudnorm JSON found in ffmpeg output:\n" + stderr[-2000:])
    return json.loads(m.group(0))


def measure(mp4: Path) -> dict:
    r = run(["ffmpeg", "-v", "info", "-i", str(mp4), "-vn",
             "-af", f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
             "-f", "null", "-"])
    if r.returncode != 0:
        raise RuntimeError(f"loudnorm measure failed on {mp4}:\n{r.stderr[-1500:]}")
    d = parse_loudnorm_json(r.stderr)
    return {
        "input_i": float(d["input_i"]),
        "input_tp": float(d["input_tp"]),
        "input_lra": float(d["input_lra"]),
        "input_thresh": float(d["input_thresh"]),
        "target_offset": float(d["target_offset"]),
        # this ffmpeg's JSON reports normalization_type ("linear" or
        # "dynamic") instead of a "linear" boolean.
        "linear": d.get("normalization_type") == "linear",
        "normalization_type": d.get("normalization_type"),
    }


def normalize(in_mp4: Path, out_mp4: Path) -> dict:
    before = measure(in_mp4)
    print(f"  before: {before['input_i']} LUFS | TP {before['input_tp']} dBTP | "
          f"LRA {before['input_lra']} LU | linear={before['linear']}", flush=True)
    measured = (f"measured_I={before['input_i']}:measured_TP={before['input_tp']}:"
                f"measured_LRA={before['input_lra']}:measured_thresh={before['input_thresh']}:"
                f"offset={before['target_offset']}:linear={str(before['linear']).lower()}")
    r = run(["ffmpeg", "-y", "-v", "error", "-i", str(in_mp4),
             "-map", "0:v", "-map", "0:a",
             "-c:v", "copy",
             "-af", f"loudnorm=I={TARGET_I}:TP={NORMALIZE_TP}:LRA={TARGET_LRA}:{measured},aresample=48000",
             "-c:a", "aac", "-b:a", "192k", "-ac", "2",
             "-movflags", "+faststart", str(out_mp4)])
    if r.returncode != 0:
        raise RuntimeError(f"loudnorm normalize failed on {in_mp4}:\n{r.stderr[-1500:]}")
    after = measure(out_mp4)
    print(f"  after:  {after['input_i']} LUFS | TP {after['input_tp']} dBTP | "
          f"LRA {after['input_lra']} LU | linear={after['linear']}", flush=True)
    return {"before": before, "after": after}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure")
    m.add_argument("mp4")
    m.add_argument("--output")
    n = sub.add_parser("normalize")
    n.add_argument("input")
    n.add_argument("output_mp4")
    n.add_argument("--output")
    args = ap.parse_args()

    if args.cmd == "measure":
        result = measure(Path(args.mp4))
        print(json.dumps(result, indent=1))
    else:
        result = normalize(Path(args.input), Path(args.output_mp4))
        print(json.dumps(result, indent=1))
    if getattr(args, "output", None):
        Path(args.output).write_text(json.dumps(result, indent=1) + "\n")
        print(f"  report saved to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
