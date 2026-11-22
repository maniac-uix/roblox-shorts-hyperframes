# Architecture — ROBLOX VIDEO FACTORY (Phase 1)

## Pipeline (future)

```
URL → research/ → scripting/ → storyboard/ → voiceover/
  → templates/ → rendering/ → quality-control/ → output/
```

Phase 1 builds the boxes and the wiring. Phase 2 connects them for one
video at a time, on the owner's go-ahead. Nothing here runs automatically.

## Module map

| Module | Role | Entry point |
|---|---|---|
| `config/` | Single source of truth (language, duration, voice, style, Cloud limits) | `config/factory.json` |
| `research/` | URL extraction + fact verification | `research/brief-template.md` |
| `scripting/` | English scripts, written to be spoken | `scripting/script-template.md` |
| `storyboard/` | Scene-by-scene breakdown, one visual per scene | `storyboard/storyboard-template.md` |
| `voiceover/` | Built-in Muse TTS | `voiceover/generate-voice.sh` |
| `assets/` | Rights-cleared images, fonts, music | `assets/README.md` |
| `templates/` | Reusable HyperFrames compositions (vertical) | `templates/base-vertical/index.html` |
| `rendering/` | The only render entry point | `rendering/render.sh` |
| `quality-control/` | Technical QC script + manual checklist | `quality-control/qc.sh` |
| `output/` | Final MP4s + `metadata.json` (MP4s git-ignored) | — |
| `scripts/` | Environment verification | `scripts/check-env.sh` |

## Rendering flow

1. `scripts/check-env.sh` — Node, FFmpeg, HyperFrames, memory, disk, /tmp.
2. `rendering/build_video.py` — builds the video from its script: estimates
   narration duration (refuses if over target — rewrite the script, never
   cut audio), generates the voice, measures real duration + end of speech,
   derives `video = max(narration + 0.3, last_speech + 1.0)`, transcribes
   with local Whisper for real caption timings, scales the template to the
   derived duration. (Corrected 21 Nov 2026 — see
   `docs/DIAGNOSIS-audio-test1.md`.)
3. `rendering/render.sh --quality draft` — draft render, safe temp paths,
   memory gate, single-render lock.
4. `quality-control/qc.sh` on the draft + `check-narration.py` (Whisper
   transcript vs script) + manual frame inspection.
5. `rendering/render.sh --quality standard` — final render, only after the
   draft passes.
6. `quality-control/qc.sh` + `check-narration.py` on the final file + full
   watch at phone size.
7. Delivery: MP4 + summary. Archive: `output/` locally; Google Drive once
   connected (status 21 Nov 2026: not connected).

## Why HyperFrames

HTML/CSS/GSAP is the source of truth, so a video is a reviewable file, not
a black-box render. The same composition renders identically every time
(paused timeline, frame-by-frame seek), and the owner can edit it in the
HyperFrames desktop app.

## Known limits (audit, 21 Nov 2026)

- `/tmp` is a 512 MB tmpfs — all temp files live under `.cache-tmp/`.
- Free RAM at render time was 0.6–0.9 GB — long renders (60 s+, 1080×1920)
  are untested and may fail; draft first, always.
- Software GPU only; capture falls back to screenshot mode when BeginFrame
  does not run (slower).
- Docker is not installed — no containerised reproducible renders.
- No paid service is connected (no HeyGen, no Runway, no Krea, no Drive).
  Music generation is the one gap: royalty-free library only.
- No automatic publishing to TikTok / YouTube / Instagram is configured
  or verified.
