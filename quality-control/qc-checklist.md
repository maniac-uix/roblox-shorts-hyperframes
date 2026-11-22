# quality-control/

Technical QC is scripted (`qc.sh`); visual QC is manual (this checklist).
Both must pass before any delivery.

```bash
bash quality-control/qc.sh output/factory-test.mp4
```

## Automated checks (`qc.sh`)

- [ ] File exists, non-empty
- [ ] Duration sane (5–60 s for tests; 30–45 s for production)
- [ ] Resolution 1080 × 1920
- [ ] Framerate 30 fps
- [ ] Codec H.264
- [ ] Audio stream present (production) and audio duration == video
      duration (±0.1 s)
- [ ] No black segment ≥ 0.5 s (`blackdetect`)

## Manual checks (do them yourself, on the rendered file)

- [ ] Frame 0 is the hook, never black, never a logo alone
- [ ] Motion in every scene — extract frames 0.5 s apart and confirm
      something changes every 1–1.5 s (no frozen card, no full-screen wipe
      flash, no sparse title-only frame)
- [ ] Titles/subtitles: no overlap, no text touching the edges, no text
      under the platform UI (safe zone x 120–888, y 288–1248)
- [ ] Subtitles legible at phone size (540 × 960): read the frames yourself
- [ ] Voice content is the right script (transcribe a sample or correlate
      against the narration file — durations alone do not prove it)
- [ ] Voice clearly above the music in speech windows (per-window levels,
      not a global loudness number)
- [ ] No missing scene, no frozen last frame held for seconds
- [ ] Watch the whole video once, start to finish, at phone size

## Rule

A file that fails QC is never delivered. Fix it, re-render under a **new
filename**, and QC again.
