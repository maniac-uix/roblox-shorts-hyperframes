#!/usr/bin/env python3
"""gate.py — the single blocking quality gate for the ROBLOX VIDEO FACTORY.

Runs EVERY blocking check on a final MP4 and prints PASS/FAIL per check
with the measured value. Exit 0 = all pass, 1 = any FAIL. **A FAIL blocks
delivery. No manual override.** If a FAIL looks like a false positive,
fix the input (lexicon, storyboard, template) and re-run the gate.

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
  7. check-image-runs.py (Phase 4C, BLOCKING): duplicate images — 64-bin
     RGB histogram of the image card every 0.5 s; FAIL if any image span
     exceeds 5.0 s or the same image file is used in two different scenes
     (Top 5 outro reusing the #1 image is the single named exception).
  8. check-title-sentence.py (Phase 4C, BLOCKING): from the storyboard
     titles and the composition timeline, the active title must match the
     current sentence (shared content word) and appear <= 0.3 s after the
     sentence starts. N/A when no composition timeline is available
     (pre-Phase-3 videos) — never invented.
  9. check-empty-zone.py (Phase 4C, BLOCKING): the image card zone
     (grayscale stddev < 12 = empty) must never stay empty more than
     0.2 s, including the first 0.2 s of the video.
 10. check-first-frame.py (Phase 4C, BLOCKING): at t=0 the first image
     AND the scene-1 title must already be visible (no empty screen at
     the start, no pop-in delay for the hook).
 11. check-hook.py (Phase 4C, BLOCKING): first sentence <= 12 words AND
     a digit, a "?", or a spelled-out number word (the enforceable form
     of the hook rule; a "surprising statement" alone is not checkable).
 12. check-brand.py (Phase 4C, BLOCKING, v4 templates onwards):
     watermark "NoobNoMore" present in pixels with declared font-size
     >= 36 px; final mascot present in pixels with declared width
     >= 220 px. N/A for pre-v4 videos (no composition / no watermark
     rule) — not PASS, not FAIL.
 13. visual change, image-only (Phase 4C, BLOCKING): longest stretch
     without a NEW image <= 5.0 s, from the check-image-runs spans.
     Zooms, pans and fades do NOT count as a change. This SUPERSEDES the
     Phase 4B fps=2 frame-diff warning (quality-control/
     check-visual-change.py): that instrument counted zooms and measured
     2.0 s max gaps on the v4 videos while the same image was held for
     5.5-9.9 s — it could not detect the defect. The script file is kept
     for calibration history; the gate no longer calls it.
 14. check-top5-sum.py: only for --format top5 (displayed + spoken sums
     consistent with the announced total)
 15. words to listen — low-confidence words (< 0.6) plus
     pronunciation-sensitive words the check could not validate
     (heard form + timestamp); recorded, not gated, but a sensitive
     word that is not validated makes the narration check itself FAIL.
     They are the owner's listening list.

Usage:
  python3 quality-control/gate.py --mp4 output/<slug>.mp4 \
      --metadata videos/<slug>/metadata.json \
      [--format facts|top5|mysteries|...] [--bed-gain-db 10.3] \
      [--composition videos/<slug>/index.html] \
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


def last_json(stdout):
    """The check scripts print a human line, then one JSON object as the
    last stdout line. Return {} when no JSON line parses."""
    for line in reversed((stdout or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True)
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--format", default="facts")
    ap.add_argument("--bed-gain-db", type=float, default=0.0)
    ap.add_argument("--composition")
    ap.add_argument("--top5-values")
    ap.add_argument("--output")
    args = ap.parse_args()
    mp4, meta_path = Path(args.mp4), Path(args.metadata)
    meta = json.loads(meta_path.read_text())
    slug = meta.get("slug") or mp4.stem
    tmp = PROJECT / ".cache-tmp" / "gate"
    tmp.mkdir(parents=True, exist_ok=True)
    checks = {}
    details = {}

    def note(name, verdict, value):
        checks[name] = {"verdict": verdict, "value": value}
        print(f"  {name}: {verdict} — {value}", flush=True)

    # Composition timeline (Phase 4C checks 8 and 12 need it). Default:
    # videos/<slug>/index.html. Absent for pre-Phase-3 videos (their
    # video dirs hold metadata.json only) — those checks record N/A.
    if args.composition:
        comp_path = Path(args.composition)
    else:
        comp_path = PROJECT / "videos" / slug / "index.html"
    comp_exists = comp_path.exists()

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

    # 7. duplicate images (Phase 4C, BLOCKING)
    runs_json = tmp / f"{slug}-image-runs.json"
    r = run([sys.executable, str(QC / "check-image-runs.py"),
             "--mp4", str(mp4), "--metadata", str(meta_path),
             "--output", str(runs_json)])
    runs = json.loads(runs_json.read_text()) if runs_json.exists() else last_json(r.stdout)
    details["image_runs"] = runs
    spans = runs.get("spans", [])
    image_spans = [s for s in spans if not s.get("fragment")]
    over = [s for s in image_spans if s.get("duration_s", 0) > 5.0]
    reuse = runs.get("reuse", [])
    note("duplicate images (max span <= 5.0 s, no reuse)",
         runs.get("verdict", "FAIL"),
         f"max span {runs.get('max_span_s', '?')} s; "
         f"{len(over)} span(s) over 5.0 s; reuse: "
         + (", ".join(f"{u['image']} scenes {u['scenes']}" for u in reuse)
            if reuse else "none")
         + (f" (method {runs.get('reuse_method', '?')})"
            if runs.get("outro_exception_applied") else ""))

    # 8. title / sentence (Phase 4C, BLOCKING; N/A without a composition)
    if not comp_exists:
        note("title / sentence (match + appear <= 0.3 s)", "N/A",
             "no composition timeline available (pre-Phase-3 video)")
        details["title_sentence"] = {"verdict": "N/A",
                                     "reason": "no composition timeline available"}
    else:
        ts_json = tmp / f"{slug}-title-sentence.json"
        r = run([sys.executable, str(QC / "check-title-sentence.py"),
                 "--mp4", str(mp4), "--metadata", str(meta_path),
                 "--composition", str(comp_path), "--output", str(ts_json)])
        ts = json.loads(ts_json.read_text()) if ts_json.exists() else last_json(r.stdout)
        details["title_sentence"] = ts
        note("title / sentence (match + appear <= 0.3 s)",
             ts.get("verdict", "FAIL"),
             f"{ts.get('n_sentences', '?')} sentences; mismatches "
             f"{ts.get('mismatches', '?')}; late titles "
             f"{ts.get('late_titles', '?')}")

    # 9. empty zone (Phase 4C, BLOCKING)
    ez_json = tmp / f"{slug}-empty-zone.json"
    r = run([sys.executable, str(QC / "check-empty-zone.py"),
             "--mp4", str(mp4), "--output", str(ez_json)])
    ez = json.loads(ez_json.read_text()) if ez_json.exists() else last_json(r.stdout)
    details["empty_zone"] = ez
    note("empty image zone (never > 0.2 s)",
         ez.get("verdict", "FAIL"),
         f"max empty {ez.get('max_empty_s', '?')} s; "
         f"{len(ez.get('empty_spans', []))} span(s)")

    # 10. first frame (Phase 4C, BLOCKING)
    ff_json = tmp / f"{slug}-first-frame.json"
    r = run([sys.executable, str(QC / "check-first-frame.py"),
             "--mp4", str(mp4), "--output", str(ff_json)])
    ff = json.loads(ff_json.read_text()) if ff_json.exists() else last_json(r.stdout)
    details["first_frame"] = ff
    note("first frame (title + image at t=0)",
         ff.get("verdict", "FAIL"),
         f"image std {ff.get('image_std_t0', '?')}; title bright px "
         f"{ff.get('title_bright_px_t0', '?')}")

    # 11. hook (Phase 4C, BLOCKING)
    hook_json = tmp / f"{slug}-hook.json"
    r = run([sys.executable, str(QC / "check-hook.py"),
             "--metadata", str(meta_path), "--output", str(hook_json)])
    hook = json.loads(hook_json.read_text()) if hook_json.exists() else last_json(r.stdout)
    details["hook"] = hook
    note("hook (<= 12 words + digit/?/number-word)",
         hook.get("verdict", "FAIL"),
         f"{hook.get('n_words', '?')} words; digit={hook.get('has_digit')}, "
         f"?={hook.get('has_question')}, number-word={hook.get('has_number_word')}")

    # 12. brand (Phase 4C, BLOCKING for v4 templates onwards)
    if not comp_exists:
        note("brand (watermark >= 36 px, mascot >= 220 px)", "N/A",
             "no composition available (pre-v4 video)")
        details["brand"] = {"verdict": "N/A",
                            "reason": "no composition available"}
    else:
        br_json = tmp / f"{slug}-brand.json"
        r = run([sys.executable, str(QC / "check-brand.py"),
                 "--mp4", str(mp4), "--metadata", str(meta_path),
                 "--composition", str(comp_path), "--output", str(br_json)])
        br = json.loads(br_json.read_text()) if br_json.exists() else last_json(r.stdout)
        details["brand"] = br
        if br.get("verdict") == "N/A":
            note("brand (watermark >= 36 px, mascot >= 220 px)", "N/A",
                 br.get("reason", "not applicable"))
        else:
            wm = br.get("watermark", {})
            mc = br.get("mascot", {})
            note("brand (watermark >= 36 px, mascot >= 220 px)",
                 br.get("verdict", "FAIL"),
                 f"watermark {wm.get('declared_font_px', '?')} px, "
                 f"present={wm.get('present')}; mascot "
                 f"{mc.get('declared_width_px', '?')} px, present="
                 f"{mc.get('present')}")

    # 13. visual change, image-only (Phase 4C, BLOCKING — supersedes the
    # Phase 4B frame-diff warning, which counted zooms). Same underlying
    # spans as check 7, different framing: the longest stretch without a
    # NEW image. A zoom, pan or fade is not a new image.
    if runs:
        max_span = runs.get("max_span_s")
        vc_verdict = ("PASS" if max_span is not None and max_span <= 5.0
                      else "FAIL")
        details["visual_change"] = {
            "verdict": vc_verdict, "max_span_s": max_span,
            "n_image_spans": len(image_spans),
            "method": "image-runs (Phase 4C)",
            "note": ("supersedes Phase 4B fps=2 frame-diff warning "
                     "(check-visual-change.py): that instrument counted "
                     "zooms and measured 2.0 s max gaps on the v4 videos "
                     "while the same image was held 5.5-9.9 s")}
        note("visual change, image-only (<= 5.0 s without a new image)",
             vc_verdict,
             f"longest stretch {max_span} s; {len(image_spans)} image spans "
             f"(zooms do not count)")
    else:
        details["visual_change"] = {"verdict": "FAIL",
                                    "reason": "image-runs produced no spans"}
        note("visual change, image-only (<= 5.0 s without a new image)",
             "FAIL", "image-runs produced no spans")

    # 14. Top 5 sum (only for top5)
    if args.format == "top5":
        if not args.top5_values:
            note("top5 sum", "FAIL", "no --top5-values file given")
        else:
            r = run([sys.executable, str(QC / "check-top5-sum.py"),
                     "--values", args.top5_values])
            m = re.search(r"TOP5 SUM CHECK: (\w+)", r.stdout)
            note("top5 sum", m.group(1) if m else "FAIL",
                 (r.stdout.splitlines()[0] if r.stdout else ""))

    overall = "PASS" if all(c["verdict"] in ("PASS", "recorded", "N/A")
                            for c in checks.values()) else "FAIL"
    report = {"slug": slug, "format": args.format, "file": str(mp4),
              "overall": overall, "checks": checks,
              "low_confidence_words": low, "listen_words": listen_words,
              "image_runs": runs,
              "title_sentence": details.get("title_sentence", {}),
              "empty_zone": details.get("empty_zone", {}),
              "first_frame": details.get("first_frame", {}),
              "hook": details.get("hook", {}),
              "brand": details.get("brand", {}),
              "visual_change": details.get("visual_change", {})}
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=1) + "\n")
        print(f"  gate report saved to {args.output}", flush=True)
    print(f"GATE: {overall}", flush=True)
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
