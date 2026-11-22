# Diagnosis — Audio "truncation" in factory-test.mp4 (Test 001)

Date: 21 Nov 2026. Reported by Amine: voice seems truncated — 10 s video,
voice until ~5.27 s, silence on the last 4.73 s, while the generated voice
file is 5.76 s.

## Verdict

**Nothing was truncated at any stage.** The narration is complete in the
raw TTS file, complete in the integrated audio, and complete in the final
MP4. The real defect is a design error, not a cut:

> The video duration was fixed FIRST (10 s template), the narration was
> shorter (5.76 s), and the narration was padded with 4.24 s of silence to
> satisfy a QC gate that compared *container* durations (audio file length
> vs video length) instead of *content* (where the speech actually ends).
> The listener hears the voice stop at ~5.3 s and then 4.7 s of dead air
> while scenes keep playing — it feels like a cut, and the conclusion gets
> a void instead of a breathing margin.

## Evidence, stage by stage

Script sent to TTS (14 words, 3 sentences):
"Roblox hides secrets in plain sight. Every world has one. This factory finds them."

| Stage | Measurement | Result |
|---|---|---|
| 1. TTS text | 14 words, 3 sentences | as written |
| 2. Raw TTS file `voiceover/factory-test-narration-raw.mp3` | ffprobe: **5.760 s** | complete file |
| 3. Speech inside the raw file | silencedetect (−40 dB): speech 0–2.01 s, 2.72–3.79 s, 4.33–**5.34 s**; silence 2.01–2.72 s (0.71 s, sentence gap), 3.79–4.33 s (0.54 s, sentence gap), 5.34–5.76 s (**0.42 s TTS trailing silence**) | last word ends 5.34 s |
| 4. Spoken content | **Whisper tiny transcription of the raw file**: "[0.00-2.20] Roblox hides secrets in plain sight. [2.78-3.94] Every world has one. [4.42-5.50] This factory finds them." — **14/14 words, word-for-word, in order** | narration complete, last sentence fully spoken |
| 5. Integrated audio `voiceover/factory-test-narration.mp3` | ffprobe: 10.000 s (raw + `apad` silence). RMS per 0.25 s window vs raw: differences 0–162 (~5%, AAC re-encode only), voice windows at identical positions and levels | voice untouched, only silence appended |
| 6. Timeline `index.html` | root `data-duration="10"`, `<audio data-start="0" data-duration="10">`, scenes 0–10 s | no trimming property anywhere; nothing could cut the audio |
| 7. Final MP4 `output/factory-test.mp4` | 10.000 s, audio 10.005 s. silencedetect: silence starts at **2.015 / 3.741 / 5.344 s — identical to the raw file**. RMS per 0.25 s window identical to raw (0 after 5.5 s in both) | render mixed the audio intact |

## The 5.76 s vs 5.27 s discrepancy — explained

Both numbers are correct; they measure different things:

- **5.76 s** = length of the TTS file, including 0.42 s of trailing silence
  the TTS engine appends after the last word.
- **~5.27–5.34 s** = end of the last spoken word ("them."), measured by
  silence detection and by Whisper word timings (last word ends 5.50 s
  in Whisper's timing, which includes the word's tail).

## Root cause

1. Duration was decided by the template (10 s), not by the narration.
2. The QC gate "audio duration == video duration (±0.1 s)" was satisfied
   by padding the narration with silence — the gate verified the container,
   never the content.
3. No check existed for: where speech ends, how long the final silence is,
   or whether the spoken words match the script.

## Fix (implemented in this correction)

- **Duration is derived from the narration, never the reverse.**
  `rendering/build_video.py`: estimate duration from word count before
  generating the voice; if the estimate exceeds the target, refuse and
  rewrite the script — never cut audio. After TTS, measure the real
  duration and the real end of speech (silencedetect), then set
  `video_duration = last_speech_end + end_margin` (margin 1.0 s from
  `config/factory.json`), with a floor of `narration_duration + 0.3 s`
  so the file is never truncated.
- **Captions are synchronised with the narration**: Whisper word timings
  (local faster-whisper tiny, venv in `.cache-tmp/venv-transcribe/`) give
  real sentence boundaries; fallback is proportional word-count timing,
  explicitly labelled as estimated.
- **QC now checks content**: `quality-control/qc.sh` verifies the final
  silence is within [margin − 0.5 s, margin + 0.75 s] and that no
  mid-narration silence exceeds 1.0 s; `quality-control/check-narration.py`
  transcribes the MP4 audio and compares it word-for-word with the script.
- **No more `apad` to a template length.** Padding exists only to fill the
  end margin (≤ ~1 s), never to reach a pre-set video length.

## Files changed by this correction

- `docs/DIAGNOSIS-audio-test1.md` (this file)
- `config/factory.json` — duration policy + end margin
- `voiceover/generate-voice.sh` — auto-measure + `<output>.meta.json`
- `rendering/build_video.py` (new) — narration-driven composition builder
- `quality-control/qc.sh` — content checks (final silence, mid silence)
- `quality-control/check-narration.py` (new) — Whisper transcript vs script
- `quality-control/transcribe.py` (new) — shared Whisper helper (venv)
- `AGENTS.md`, `README.md`, `docs/ARCHITECTURE.md`, `voiceover/README.md`
- Test 002: `videos/factory-test-2/` (script, narration, composition,
  metadata, transcript) + `output/factory-test-2.mp4`
