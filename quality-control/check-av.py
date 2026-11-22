#!/usr/bin/env python3
"""check-av.py — the two v3.1b blocking controls (Amine, 22 Nov 2026),
plus the standing loudness gate. All measured on the DELIVERED file.

  1. audio sample rate == 48000 Hz exactly
     (the v3.1 files came out at 96000 Hz — loudnorm re-encoded the
     audio without an explicit sample rate; the fix is aresample=48000)
  2. |audio duration - video duration| <= 0.02 s
     (the v3.1 files had the audio 0.06-0.10 s LONGER than the video —
     AAC padding from the loudnorm re-encode; the old qc.sh gate was
     only ±0.1 s, so it passed)
  3. loudness gate: integrated -14 LUFS ± 0.5, true peak <= -1 dBTP
     (measured via normalize-loudness.py on the delivered file)

Also recorded (not gated): codec (must be aac), channels (must be 2),
audio bitrate (~192k).

Usage: check-av.py --mp4 <file> [--output report.json]
Exit 0 = PASS, 1 = FAIL. The verdict is authoritative: a FAIL blocks
delivery, no manual override.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

GATE_SR = 48000
GATE_GAP_S = 0.02
GATE_I = (-14.5, -13.5)
GATE_TP = -1.0


def probe(mp4: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                        "-show_format", "-show_streams", str(mp4)],
                       text=True, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {mp4}:\n{r.stderr[-1000:]}")
    return json.loads(r.stdout)


def loudness(mp4: Path) -> dict:
    script = Path(__file__).parent / "normalize-loudness.py"
    r = subprocess.run([sys.executable, str(script), "measure", str(mp4)],
                       text=True, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"loudness measure failed on {mp4}:\n{r.stderr[-1000:]}")
    return json.loads(r.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()
    mp4 = Path(args.mp4)
    info = probe(mp4)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
    v_dur = float(video["duration"])
    a_dur = float(audio["duration"])
    gap = abs(a_dur - v_dur)
    sr = int(audio["sample_rate"])
    loud = loudness(mp4)

    checks = {
        "sample_rate": {
            "verdict": "PASS" if sr == GATE_SR else "FAIL",
            "value": f"{sr} Hz (required {GATE_SR})",
            "measured": sr},
        "av_gap": {
            "verdict": "PASS" if gap <= GATE_GAP_S else "FAIL",
            "value": (f"audio {a_dur:.3f} s vs video {v_dur:.3f} s, "
                      f"gap {gap:.3f} s (gate <= {GATE_GAP_S} s)"),
            "measured": gap,
            "audio_duration_s": a_dur, "video_duration_s": v_dur},
        "loudness_integrated": {
            "verdict": "PASS" if GATE_I[0] <= loud["input_i"] <= GATE_I[1] else "FAIL",
            "value": f"{loud['input_i']} LUFS (gate -14 ± 0.5)",
            "measured": loud["input_i"]},
        "true_peak": {
            "verdict": "PASS" if loud["input_tp"] <= GATE_TP else "FAIL",
            "value": f"{loud['input_tp']} dBTP (gate <= -1)",
            "measured": loud["input_tp"]},
        "lra": {"verdict": "recorded", "value": f"{loud['input_lra']} LU",
                "measured": loud["input_lra"]},
        "audio_codec": {
            "verdict": "PASS" if audio["codec_name"] == "aac" else "FAIL",
            "value": f"{audio['codec_name']}, {audio['channels']} ch, "
                     f"~{int(audio.get('bit_rate', 0)) // 1000} kb/s"},
    }
    overall = "PASS" if all(c["verdict"] in ("PASS", "recorded")
                            for c in checks.values()) else "FAIL"
    report = {"file": str(mp4), "overall": overall, "checks": checks}
    for name, c in checks.items():
        print(f"  {name}: {c['verdict']} — {c['value']}")
    print(f"AV CHECK: {overall}")
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=1) + "\n")
        print(f"  report saved to {args.output}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
