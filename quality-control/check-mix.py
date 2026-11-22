#!/usr/bin/env python3
"""check-mix.py — voice-above-music gate for mixes with a music bed.

The final silence QC (qc.sh) cannot tell voice from music: a music bed
fills the gaps between sentences, so silencedetect sees no silence at
all. This script measures what qc.sh cannot: in every speech window the
voice must sit clearly above the bed.

Method (rewritten 22 Nov 2026): for each caption span (voice + music),
measure the mean volume in the MP4 and the mean volume of the bed ALONE
at the same time offset (same bed file, same volume), and require
speech - bed >= 6 dB in EVERY window (config voiceMustSitAboveMusicDb).

Why not gaps: the previous version compared the quietest speech window
against the loudest inter-sentence gap. That failed twice on artefacts,
not on a buried voice — a drum transient inside one 0.4 s gap measured
-31.7 dB while the bed's steady level was ~-40 dB, and Whisper word
timestamps are +/-0.2 s off, so gap edges still carry voice tails
(a gap edge once measured -26.6 dB where the bed alone was -40.5 dB).
Comparing voice+bed against bed-only in the SAME window cancels the
bed's own dynamics and transients: only the voice's contribution is
scored. A global loudness number alone proves nothing — loudness is set
by the loudest element, usually the music — so this is per-window.

Usage:
  python3 quality-control/check-mix.py --mp4 output/<slug>.mp4 \
      --metadata videos/<slug>/metadata.json [--min-diff-db 6]

  When the delivered mix was loudness-normalized (v3.1 gate, 22 Nov 2026),
  pass --bed-gain-db <after-before LUFS>: the bed alone is measured with
  the same overall gain the normalization applied to the mix, so the
  comparison stays like-for-like. The dynamic gain variations inside one
  speech window are second-order — the voice dominates the mix level
  there, so the limiter's gain in that window is set by the voice and the
  bed gets the same gain. Without the gain, a normalized mix compared
  against the raw bed overstates the ratio by the normalization gain.
"""
import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent


def mean_volume(path: str, start: float, dur: float, volume: float = None) -> float:
    af = "volumedetect"
    if volume is not None:
        af = f"volume={volume},{af}"
    r = subprocess.run(
        ["ffmpeg", "-v", "info", "-ss", f"{start:.2f}", "-t", f"{dur:.2f}",
         "-i", path, "-vn", "-af", af, "-f", "null", "-"],
        text=True, capture_output=True)
    m = re.search(r"mean_volume:\s*(-?[0-9.]+) dB", r.stderr)
    if not m:
        raise RuntimeError(f"volumedetect failed for {path} "
                           f"{start:.2f}+{dur:.2f}s: {r.stderr[-200:]}")
    return float(m.group(1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True)
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--min-diff-db", type=float, default=6.0)
    ap.add_argument("--bed-gain-db", type=float, default=0.0,
                    help="linear gain (dB) applied to the bed alone, e.g. the "
                         "integrated loudness gain of a normalized mix")
    args = ap.parse_args()

    meta = json.load(open(args.metadata))
    captions = meta["captions"]
    if not captions:
        print("no captions in metadata — cannot check the mix")
        return 1
    music = meta.get("music")
    if music is None:
        print("no music bed in this video — voice-above-music gate not applicable")
        return 0
    bed_path = PROJECT_DIR / music["track"]
    bed_volume = float(music["volume"]) * 10 ** (args.bed_gain_db / 20.0)
    if args.bed_gain_db:
        print(f"bed measured with +{args.bed_gain_db:.2f} dB gain "
              f"(normalization gain, like-for-like with the delivered mix)")

    rows = []
    for c in captions:
        d = c["end"] - c["start"]
        if d < 0.5:
            continue
        speech = mean_volume(args.mp4, c["start"], d)
        bed = mean_volume(str(bed_path), c["start"], d, volume=bed_volume)
        rows.append((c["start"], c["end"], speech, bed, speech - bed))

    print("speech windows: mix (voice+bed) vs bed alone at same offset:")
    for s, e, speech, bed, diff in rows:
        flag = "" if diff >= args.min_diff_db else "  <-- BELOW GATE"
        print(f"  [{s:6.2f}-{e:6.2f}] mix {speech:6.1f} dB | "
              f"bed {bed:6.1f} dB | voice above bed {diff:5.1f} dB{flag}")
    if not rows:
        print("no speech windows >= 0.5 s — gate inconclusive")
        return 1
    worst = min(diff for _, _, _, _, diff in rows)
    print(f"worst window: voice sits {worst:.1f} dB above the bed "
          f"(required >= {args.min_diff_db:.1f} dB)")
    if worst >= args.min_diff_db:
        print("MIX CHECK: PASS — voice sits clearly above the music bed.")
        return 0
    print("MIX CHECK: FAIL — voice is not clearly above the music bed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
