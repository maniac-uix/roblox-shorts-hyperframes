# voiceover/

Voice generation. Built-in Muse TTS only — no paid service, no HeyGen.

## Generate

```bash
bash voiceover/generate-voice.sh "Your script text here." \
  --output voiceover/narration.mp3
```

- Engine: `/opt/hatch/bin/tts` (Meta Shortwave), voice Helio
  (`avocado_v2:MAI_03`), English, speed 100.
- The text is spoken exactly as written.

## The duration rule (corrected 21 Nov 2026)

**The video duration is derived from the narration, never the reverse.**
See `docs/DIAGNOSIS-audio-test1.md`: Test 001 padded a 5.76 s narration
with 4.24 s of silence to reach a 10 s template — the voice stopped at
~5.3 s and the last 4.7 s were dead air. That must never happen again.

- `generate-voice.sh` measures the real duration and the real end of
  speech and writes `<output>.meta.json` (duration, words, wps,
  lastSpeechEnd, trailing silence).
- `rendering/build_video.py` sets the video duration from those
  measurements: `video = max(narration + 0.3, lastSpeechEnd + 1.0)`.
- Padding exists only to fill the 1.0 s end margin — never to reach a
  pre-set video length. If the script is too long for the target, rewrite
  the script **before** generating the voice; audio is never cut.
- Never deliver a video whose audio stops early. That exact bug shipped
  once (28 s of audio on a 69.7 s video) — and the Test 001 padding bug
  was its mirror image: the fix is to derive duration from content, and
  to check content, not just container durations.

## Files

- `factory-test-narration-raw.mp3` — Phase 1 test narration, 5.76 s, 14 words.
- `factory-test-narration.mp3` — same narration padded to exactly 10.000 s.
- `narration.mp3` — placeholder path referenced by the templates; replaced
  per video (not committed with real content in Phase 1).
