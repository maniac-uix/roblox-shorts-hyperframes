#!/usr/bin/env bash
# qc.sh — technical quality control for a rendered MP4.
# Usage: bash quality-control/qc.sh <file.mp4> [--end-margin 1.0]
# Checks: duration, resolution, framerate, codec, audio presence,
# audio/video duration match (±0.1 s), black frames, file sanity,
# CONTENT checks (corrected 21 Nov 2026, Test 001 diagnosis):
#   - final silence within [endMargin - 0.5 s, endMargin + 0.75 s]
#     (the conclusion must breathe, not drown in a dead void)
#   - no mid-narration silence longer than 1.0 s (sentence gaps in
#     Test 001 were 0.71 s — legitimate pauses must pass)
# Exits 0 only when every check passes. Visual checks (subtitle legibility,
# mobile preview) are manual — see quality-control/qc-checklist.md.
# Narration content (transcript vs script) is checked separately by
# quality-control/check-narration.py — a passing qc.sh alone never proves
# the narration is complete.
set -u
FILE="${1:-output/factory-test-standard.mp4}"
END_MARGIN="1.0"
if [ "${2:-}" = "--end-margin" ]; then END_MARGIN="${3:-1.0}"; fi
case "$FILE" in /*) ;; *) FILE="$PWD/$FILE" ;; esac
FAIL=0
ok()   { echo "  PASS  $1"; }
bad()  { echo "  FAIL  $1"; FAIL=1; }

[ -f "$FILE" ] || { echo "FAIL: file not found: $FILE"; exit 1; }
echo "QC: $FILE"
echo "  size: $(du -h "$FILE" | cut -f1)"

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FILE")
W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$FILE")
H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$FILE")
FPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$FILE")
CODEC=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 "$FILE")
HAS_AUDIO=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 "$FILE" || true)
ADUR=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$FILE" 2>/dev/null || echo "")

echo "  duration: ${DUR}s | ${W}x${H} | fps: ${FPS} | codec: ${CODEC} | audio: ${HAS_AUDIO:-none}"

if python3 - "$DUR" <<'EOF'
import sys
d = float(sys.argv[1])
sys.exit(0 if 5 <= d <= 60 else 1)
EOF
then ok "duration sane (${DUR}s)"; else bad "duration is 5-60 s (got ${DUR}s)"; fi
[ "$W" = "1080" ] && [ "$H" = "1920" ] && ok "resolution 1080x1920" || bad "resolution is 1080x1920 (got ${W}x${H})"
[ "$FPS" = "30/1" ] && ok "framerate 30 fps" || bad "framerate is 30 fps (got $FPS)"
[ "$CODEC" = "h264" ] && ok "codec H.264" || bad "codec is H.264 (got $CODEC)"

if [ -n "$HAS_AUDIO" ] && [ -n "$ADUR" ]; then
  ok "audio stream present ($HAS_AUDIO, ${ADUR}s)"
  if python3 - "$DUR" "$ADUR" <<'EOF'
import sys
v, a = float(sys.argv[1]), float(sys.argv[2])
sys.exit(0 if abs(v - a) <= 0.1 else 1)
EOF
  then ok "audio/video duration match (±0.1 s): video ${DUR}s vs audio ${ADUR}s"
  else bad "audio duration == video duration (±0.1 s): video ${DUR}s vs audio ${ADUR}s"; fi
else
  echo "  INFO  no audio stream — allowed only for silent test renders, never for delivery"
fi

BLACK=$(ffmpeg -nostdin -i "$FILE" -vf "blackdetect=d=0.5:pix_th=0.10" -an -f null - 2>&1 | grep -c "black_start" || true)
if [ "$BLACK" = "0" ]; then ok "no black frames >= 0.5 s"; else bad "$BLACK black segment(s) >= 0.5 s detected"; fi

# --- Content checks: where does the speech actually end? ---
# Extract audio and run silencedetect (-40 dB, min 0.3 s). The last silence
# segment gives the final silence; every other segment is a mid-narration gap.
if [ -n "$HAS_AUDIO" ]; then
  TMPWAV="$(mktemp --tmpdir="$(dirname "$0")/../.cache-tmp/tmp" qc-audio-XXXXXX.wav)"
  ffmpeg -y -v error -i "$FILE" -vn -ac 1 -ar 16000 "$TMPWAV"
  SILENCE_LOG=$(ffmpeg -v info -i "$TMPWAV" -af silencedetect=noise=-40dB:d=0.3 -f null - 2>&1)
  rm -f "$TMPWAV"
  python3 - "$DUR" "$END_MARGIN" "$SILENCE_LOG" <<'PYEOF'
import re, sys
dur, margin = float(sys.argv[1]), float(sys.argv[2])
log = sys.argv[3]
starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
segs = list(zip(starts, ends))
fail = []
if not segs:
    print("  INFO  no silence detected at all — narration runs to the end")
else:
    # Trailing silence = the last segment only if it reaches the end of the
    # file; otherwise speech resumes after it and runs to the end (no margin).
    trailing = segs[-1] if segs[-1][1] >= dur - 0.3 else None
    if trailing is None:
        final_silence = 0.0
        mid_segs = segs
    else:
        final_silence = dur - trailing[0]
        mid_segs = segs[:-1]
    lo, hi = margin - 0.5, margin + 0.75
    if lo <= final_silence <= hi:
        print(f"  PASS  final silence {final_silence:.2f} s within "
              f"[{lo:.2f}, {hi:.2f}] s (end margin {margin:.1f} s)")
    else:
        print(f"  FAIL  final silence {final_silence:.2f} s outside "
              f"[{lo:.2f}, {hi:.2f}] s (end margin {margin:.1f} s) — "
              f"last speech ends at {dur - final_silence:.2f} s on a {dur:.2f} s video")
        fail.append("final silence")
    mid = [round(e - s, 2) for s, e in mid_segs]
    long_gaps = [g for g in mid if g > 1.0]
    if not long_gaps:
        print(f"  PASS  no mid-narration silence > 1.0 s (gaps: {mid})")
    else:
        print(f"  FAIL  mid-narration silence > 1.0 s: {long_gaps}")
        fail.append("mid silence")
sys.exit(1 if fail else 0)
PYEOF
  [ $? -eq 0 ] || FAIL=1
else
  bad "no audio stream — content checks cannot run"
fi

echo
if [ "$FAIL" -eq 0 ]; then echo "QC RESULT: PASS"; else echo "QC RESULT: FAIL — do not deliver this file"; fi
exit "$FAIL"
