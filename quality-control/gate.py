#!/usr/bin/env python3
"""gate.py — the single blocking quality gate for the ROBLOX VIDEO FACTORY.

Runs EVERY blocking check of Phase 3 (Step 3) on a final MP4 and prints
PASS/FAIL per check with the measured value. Exit 0 = all pass, 1 = any
FAIL. **A FAIL blocks delivery. No manual override.** If a FAIL looks
like a false positive, fix the lexicon (quality-control/narration-lexicon.json)
and re-run the gate.

Checks (in order):
  1. format: 1080x1920, 30 fps, H.264, yuv420p (ffprobe)
  2. qc.sh: the 9 scripted technical checks (incl. final silence 0.5-1.75 s,
     no mid-silence > 1.0 s, no blackframes pic_th=0.98)
  3. check-av.py: audio 48 kHz, |audio-video| <= 0.02 s, loudness
     -14 ± 0.5 LUFS, true peak <= -1 dBTP
  4. check-mix.py: voice >= 6 dB above the music in every speech window
     (--bed-gain-db = the loudness gain applied by normalisation, so the
     comparison is like-for-like; 0 if the file was not normalised)
  5. check-narration-fuzzy.py: Whisper small on the final MP4 vs the script
     from metadata.json (lexicon + numbers + difflib >= 0.80), last
     sentence complete and ending before the final silence
  6. check-sync.py: captions within 0.3 s of the spoken words (Whisper tiny)
  7. check-visual-change.py (Phase 4B, RECORDED, non-blocking): longest
     stretch with no visual change (fps=2 frame-diff, threshold 0.01,
     limit 4.0 s). Calibration (23 Nov 2026) proved it cannot block:
     full-fps scdet at 0.05-0.15 finds 0 changes on good videos at
     >= 0.08, and even the fps=2 variant leaves facts at 4.50 s and
     top5 / throw-food exactly at 4.00 s — a blocking limit would fail
     good videos. A frozen clip reads max gap = video length, 0 changes.
  8. check-top5-sum.py: only for --format top5 (displayed + spoken sums
     consistent with the announced total)
  8. words to listen — low-confidence words (< 0.6) plus
     pronunciation-sensitive words the check could not validate
     (heard form + timestamp); recorded, not gated, but a sensitive
     word that is not validated makes the narration check itself FAIL.
     They are the owner's listening list.

Usage:
  python3 quality-control/gate.py --mp4 output/<slug>.mp4 \
      --metadata videos/<slug>/metadata.json \
      [--format facts|top5|mysteries|...] [--bed-gain-db 10.3] \
      [--top5-values pipeline/<slug>/top5-values.json] \
      [--output audit-package/technical-reports/<slug>-gate.json]

Whisper steps use .cache-tmp/venv-transcribe/bin/python when present
(faster-whisper lives there), else python3.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
QC = PROJECT / "quality-control"
VENV_PY = PROJECT / ".cache-tmp" / "venv-transcribe" / "bin" / "python"
PY = str(VENV_PY) if VENV_PY.exists() else sys.executable


def run(cmd, **kw):
    return subprocess.run(cmd, text=True, capture_output=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True)
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--format", default="facts")
    ap.add_argument("--bed-gain-db", type=float, default=0.0)
    ap.add_argument("--top5-values")
    ap.add_argument("--output")
    args = ap.parse_args()
    mp4, meta_path = Path(args.mp4), Path(args.metadata)
    meta = json.loads(meta_path.read_text())
    slug = meta.get("slug") or mp4.stem
    tmp = PROJECT / ".cache-tmp" / "gate"
    tmp.mkdir(parents=True, exist_ok=True)
    checks = {}

    def note(name, verdict, value):
        checks[name] = {"verdict": verdict, "value": value}
        print(f"  {name}: {verdict} — {value}", flush=True)

    print(f"== GATE {slug} ({args.format}) ==", flush=True)

    # 1. format
    info = json.loads(run(["ffprobe", "-v", "quiet", "-print_format", "json",
                           "-show_streams", str(mp4)]).stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next(s for s in info["streams"] if s["codec_type"] == "audio")
    fmt_ok = (v["width"] == 1080 and v["height"] == 1920
              and v["codec_name"] == "h264"
              and v.get("pix_fmt") == "yuv420p"
              and abs(float(v.get("avg_frame_rate", "30/1").split("/")[0])
                      / float(v.get("avg_frame_rate", "30/1").split("/")[1]) - 30) < 0.1)
    note("format 1080x1920/30fps/h264/yuv420p",
         "PASS" if fmt_ok else "FAIL",
         f"{v['width']}x{v['height']} {v['codec_name']} {v.get('pix_fmt')} "
         f"@ {v.get('avg_frame_rate')}")

    # 2. qc.sh
    r = run(["bash", str(QC / "qc.sh"), str(mp4)], cwd=PROJECT)
    (tmp / f"{slug}-qc.log").write_text(r.stdout + r.stderr)
    m = re.search(r"final silence ([0-9.]+) s", r.stdout)
    note("qc.sh (9 checks)", "PASS" if r.returncode == 0 else "FAIL",
         f"exit {r.returncode}; final silence {m.group(1) if m else '?'} s")

    # 3. check-av.py
    av_json = tmp / f"{slug}-av.json"
    r = run([sys.executable, str(QC / "check-av.py"), "--mp4", str(mp4),
             "--output", str(av_json)])
    av = json.loads(av_json.read_text()) if av_json.exists() else {}
    note("audio 48kHz / A-V gap / loudness",
         av.get("overall", "FAIL"),
         "; ".join(f"{k}: {c['value']}"
                   for k, c in av.get("checks", {}).items()
                   if k in ("sample_rate", "av_gap", "loudness_integrated", "true_peak")))

    # 4. check-mix.py
    r = run([sys.executable, str(QC / "check-mix.py"), "--mp4", str(mp4),
             "--metadata", str(meta_path),
             "--bed-gain-db", str(args.bed_gain_db)])
    m = re.search(r"worst window: voice sits ([0-9.]+) dB", r.stdout)
    note("voice above music (>= 6 dB)", "PASS" if r.returncode == 0 else "FAIL",
         f"worst window {m.group(1) if m else '?'} dB "
         f"(bed gain +{args.bed_gain_db} dB)")

    # 5. narration (fuzzy, Whisper small on the final MP4)
    narr_json = tmp / f"{slug}-narration.json"
    r = run([PY, str(QC / "check-narration-fuzzy.py"), "--mp4", str(mp4),
             "--script", meta["script"], "--output", str(narr_json)])
    narr = json.loads(narr_json.read_text()) if narr_json.exists() else {}
    note("narration fuzzy (Whisper small)",
         narr.get("verdict", "FAIL"),
         f"{narr.get('matched', '?')}/{narr.get('script_words', '?')} words, "
         f"missing {len(narr.get('missing', []))}; final sentence "
         f"{'COMPLETE' if narr.get('final_sentence', {}).get('complete') else 'INCOMPLETE'}")
    low = narr.get("low_confidence_words", [])
    note("low-confidence words (< 0.6)", "recorded",
         f"{len(low)} words — see report for timestamps")
    # Words to listen: low-confidence words + pronunciation-sensitive
    # words the narration check could not validate (heard form +
    # timestamp). A sensitive word that is not validated already makes
    # the narration check FAIL; the list tells the owner where to listen.
    listen_words = ([{"word": w["word"], "start": w["start"], "end": w["end"],
                      "prob": w["prob"], "reason": "low-confidence"}
                     for w in low]
                    + narr.get("listen_words", []))
    note("words to listen", "recorded",
         f"{len(listen_words)} words — see report for timestamps")

    # 6. sync (Whisper tiny timings)
    sync_json = tmp / f"{slug}-sync.json"
    r = run([PY, str(QC / "check-sync.py"), "--mp4", str(mp4),
             "--metadata", str(meta_path), "--output", str(sync_json)])
    sync = json.loads(sync_json.read_text()) if sync_json.exists() else {}
    note("caption sync (Whisper tiny)",
         sync.get("verdict", "FAIL"),
         f"max |start gap| {sync.get('max_abs_start_gap_s', '?')} s "
         f"(gate <= 0.3 s)")

    # 7. visual change (Phase 4B, RECORDED — never blocking). The verdict
    # is deliberately "recorded", not PASS/FAIL: the calibration proved
    # no threshold lets all 5 good videos pass with margin (facts
    # 4.50 s, top5 / throw-food exactly 4.00 s at fps=2, thr 0.01), so
    # a FAIL here must not block delivery. The value carries the signal:
    # a frozen video reads max gap = video length with 0 changes.
    vc = {}
    r = run([sys.executable, str(QC / "check-visual-change.py"),
             "--mp4", str(mp4), "--threshold", "0.01", "--max-gap", "4.0"])
    try:
        vc = json.loads(r.stdout.strip().splitlines()[-1])
    except (IndexError, ValueError):
        vc = {}
    vc_over = vc.get("max_gap_s") is not None and vc["max_gap_s"] > 4.0
    note("visual change (max gap <= 4.0 s, fps=2 frame-diff)", "recorded",
         f"{'WARNING — ' if vc_over else ''}max gap "
         f"{vc.get('max_gap_s', '?')} s, {vc.get('n_changes', '?')} changes "
         f"@ thr 0.01 (non-blocking, Phase 4B calibration)")

    # 8. Top 5 sum (only for top5)
    if args.format == "top5":
        if not args.top5_values:
            note("top5 sum", "FAIL", "no --top5-values file given")
        else:
            r = run([sys.executable, str(QC / "check-top5-sum.py"),
                     "--values", args.top5_values])
            m = re.search(r"TOP5 SUM CHECK: (\w+)", r.stdout)
            note("top5 sum", m.group(1) if m else "FAIL",
                 (r.stdout.splitlines()[0] if r.stdout else ""))

    overall = "PASS" if all(c["verdict"] in ("PASS", "recorded")
                            for c in checks.values()) else "FAIL"
    report = {"slug": slug, "format": args.format, "file": str(mp4),
              "overall": overall, "checks": checks,
              "low_confidence_words": low, "listen_words": listen_words,
              "visual_change": vc}
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=1) + "\n")
        print(f"  gate report saved to {args.output}", flush=True)
    print(f"GATE: {overall}", flush=True)
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
