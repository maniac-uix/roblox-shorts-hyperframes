#!/usr/bin/env bash
# generate-voice.sh — generate an English voiceover with the built-in Muse TTS.
# No paid service. Voice: Helio (avocado_v2:MAI_03), 100 speed, English.
# Usage:
#   bash voiceover/generate-voice.sh "Your script text here." [--output voiceover/narration.mp3] [--voice ID] [--speed 100]
# The text is spoken exactly as written — write numbers and abbreviations as
# they should sound. After synthesis, the script MEASURES the real duration
# and the real end of speech (silencedetect) and writes <output>.meta.json.
# The video duration is derived from these measurements (see
# rendering/build_video.py) — the narration is NEVER padded or cut to fit a
# pre-set video length (corrected 21 Nov 2026, Test 001 diagnosis).
set -u
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEXT="${1:-}"
[ -n "$TEXT" ] || { echo "Usage: bash voiceover/generate-voice.sh \"Text to speak.\" [--output FILE]" >&2; exit 2; }
shift
OUTPUT="$PROJECT_DIR/voiceover/narration.mp3"
VOICE="avocado_v2:MAI_03"
SPEED="100"
while [ $# -gt 0 ]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --voice) VOICE="$2"; shift 2 ;;
    --speed) SPEED="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
case "$OUTPUT" in /*) ;; *) OUTPUT="$PROJECT_DIR/$OUTPUT" ;; esac
mkdir -p "$(dirname "$OUTPUT")"
command -v /opt/hatch/bin/tts >/dev/null 2>&1 || { echo "ERROR: /opt/hatch/bin/tts not found." >&2; exit 1; }
printf '%s' "$TEXT" | /opt/hatch/bin/tts speak --output "$OUTPUT" --text-stdin \
  --voice "$VOICE" --language en --speed "$SPEED"
[ -f "$OUTPUT" ] || { echo "ERROR: TTS produced no file." >&2; exit 1; }
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUTPUT")
WORDS=$(printf '%s' "$TEXT" | wc -w)
WPS=$(python3 -c "print(round($WORDS / float('$DUR'), 2))" 2>/dev/null || echo "null")
# End of speech: start of the final silence segment (silencedetect, -40 dB).
# If the file ends in speech, lastSpeechEnd == duration.
LAST_SPEECH=$(ffmpeg -v info -i "$OUTPUT" -af silencedetect=noise=-40dB:d=0.3 -f null - 2>&1 \
  | grep -oP 'silence_start: [0-9.]+' | tail -1 | awk '{print $2}')
if [ -z "$LAST_SPEECH" ]; then LAST_SPEECH="$DUR"; fi
# Sanity: lastSpeechEnd must not exceed the file duration.
LAST_SPEECH=$(python3 -c "print(min(float('$LAST_SPEECH'), float('$DUR')))")
META="${OUTPUT%.mp3}.meta.json"
python3 - "$META" "$OUTPUT" "$VOICE" "$SPEED" "$DUR" "$WORDS" "$WPS" "$LAST_SPEECH" "$TEXT" <<'PYEOF'
import json, sys
_, meta_path, out, voice, speed, dur, words, wps, last_speech, text = sys.argv
dur_f, last_f = float(dur), float(last_speech)
meta = {
  "file": out,
  "text": text,
  "voice": voice,
  "speed": int(speed),
  "language": "en",
  "durationSeconds": dur_f,
  "words": int(words),
  "wordsPerSecond": float(wps) if wps != "null" else None,
  "lastSpeechEndSeconds": last_f,
  "trailingSilenceSeconds": round(dur_f - last_f, 2),
}
json.dump(meta, open(meta_path, "w"), indent=1)
print("meta:", meta_path)
PYEOF
echo "Voiceover: $OUTPUT"
echo "  duration: ${DUR}s | words: $WORDS | wps: $WPS | last speech ends: ${LAST_SPEECH}s"
echo "  -> video duration = max(duration + 0.3, lastSpeechEnd + endMargin). See rendering/build_video.py."
ls -lh "$OUTPUT"
