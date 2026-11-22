# ROBLOX VIDEO FACTORY

Cloud pipeline that turns a **verified public Roblox URL** into an original,
animated vertical video — ready to publish on **TikTok, YouTube Shorts and
Instagram Reels**.

**Phase 1 — Foundation.** This phase builds the infrastructure only. No
automated production from URLs yet, and no automatic publishing.

```
URL → Research → Analysis → Script → Storyboard → Voiceover
  → HyperFrames animation → MP4 render → Quality control → Delivery
```

## Video standard

| Setting | Value |
|---|---|
| Format | 1080 × 1920, 9:16, vertical |
| Frame rate | 30 fps |
| Codec | H.264 MP4 |
| Duration | 30–45 s (target 35 s) |
| Language | English — voice, on-screen text, metadata |
| Subtitles | Synchronised, word-by-word where possible |
| Music | Royalty-free only, with attribution |
| Identity | Gaming dark theme (deep navy `#0B1026`, teal `#2DD4BF`, Montserrat) |

## Editorial formats

Roblox Mysteries · Roblox Facts · Roblox Top 5 · Roblox Hidden Secrets ·
Roblox Game Discoveries · Roblox Updates · Roblox Stories.

Every video needs an original hook, a structured narration and a relevant
conclusion. **Never invent facts about games or their creators.** Every claim
must come from a verified public source, cited in the video's metadata.

## Requirements

- Node.js ≥ 22, npm, FFmpeg (8.x tested)
- HyperFrames CLI 0.9.78 (pinned in `package.json`)
- Chrome Headless Shell (downloaded once by `npx hyperframes browser ensure`)
- No paid service, no account, no API key required for Phase 1

## Installation

```bash
git clone https://github.com/maniac-uix/roblox-shorts-hyperframes.git
cd roblox-shorts-hyperframes
npm install
npx hyperframes browser ensure
bash scripts/fetch-assets.sh   # Montserrat font (binary, not stored in git)
bash scripts/check-env.sh
```

Binary assets (the Montserrat `.woff2` and voiceover `.mp3` files) are not
stored in git — the GitHub snapshot push accepts UTF-8 text only. The font
is downloaded by `scripts/fetch-assets.sh`; voiceovers are generated per
video with `voiceover/generate-voice.sh`.

If `browser ensure` refuses with a permissions error about `~/.cache` or `~`
being group-writable, run `chmod go-w ~/.cache ~` first (reversible), then
retry. Note: `~` reverted to group-writable once between the audit and the
Phase 1 build (probably on VM replacement) — so `bash scripts/check-env.sh`
checks this every session, and the fix may need re-applying. See
`scripts/check-env.sh` — it checks this for you.

## Configuration

One central file: `config/factory.json`. It holds the language, duration,
resolution, voice, style, safe zone, audio rules and Cloud paths. Change a
value there — do not hard-code it in a template.

## Usage — building a video (narration-driven)

```bash
# 1. Check the environment (Node, FFmpeg, HyperFrames, memory, disk, /tmp)
bash scripts/check-env.sh

# 2. Build the video from its script — duration is DERIVED from the narration.
#    Refuses to generate the voice if the estimated narration exceeds the target.
python3 rendering/build_video.py --slug my-video \
  --script "Your English script here." \
  --template templates/base-vertical/index.html \
  --target-min 30 --target-max 45
#    -> videos/my-video/index.html + narration-mix.mp3 + metadata.json

# 3. Draft render of the built composition (fast, low quality)
bash rendering/render.sh --quality draft \
  --composition videos/my-video/index.html --output output/my-video-draft.mp4

# 4. Quality control on the draft (incl. final-silence + mid-silence checks)
bash quality-control/qc.sh output/my-video-draft.mp4

# 5. Narration content check: fuzzy Whisper transcript vs script
python3 quality-control/check-narration-fuzzy.py --mp4 output/my-video-draft.mp4 \
  --script "Your English script here."

# 6. Final render (only after draft + narration checks pass)
bash rendering/render.sh --quality standard \
  --composition videos/my-video/index.html --output output/my-video.mp4

# 7. The blocking gate on the final file (all Phase 3 checks, no override)
python3 quality-control/gate.py --mp4 output/my-video.mp4 \
  --metadata videos/my-video/metadata.json --format facts
```

`rendering/render.sh` is the **only** supported way to render: it sets the
safe temporary paths, checks free memory, refuses a second heavy render in
parallel, and always renders draft before final. Never call
`npx hyperframes render` directly, and never use `/tmp` for large temp files
(`/tmp` is a 512 MB tmpfs on this VM — renders fail there).

### Rendering a specific composition

```bash
bash rendering/render.sh --quality draft \
  --composition templates/base-vertical/index.html \
  --output output/my-video-draft.mp4
```

## Voiceover

```bash
bash voiceover/generate-voice.sh "Your script text here." \
  --output voiceover/narration.mp3
```

Uses the built-in Muse TTS (`/opt/hatch/bin/tts`, voice Helio). No paid
service. English only. The script is spoken exactly as written — write
numbers and abbreviations as they should sound. The script measures the
real duration and end of speech and writes `<output>.meta.json`; the video
duration is derived from it (see `rendering/build_video.py`) — never pad a
narration to fit a template (Test 001 diagnosis:
`docs/DIAGNOSIS-audio-test1.md`).

## Project structure

```
config/            Central configuration (factory.json)
research/          URL extraction + fact verification (templates + method)
scripting/         Scripts and storytelling (templates)
storyboard/        Scene-by-scene breakdown (templates)
voiceover/         Voice generation (generate-voice.sh)
pipeline/          run.py — the URL → video driver (stages + stop point)
              claims-schema.json — the claims.json format
              music-attribution.py — description attribution text
assets/            Images, fonts, music — rights-cleared only
templates/         Reusable HyperFrames compositions (vertical 1080x1920)
  base-vertical/   Base template — the factory default
  formats/         Per-format variants (facts, top5, mysteries)
rendering/         render.sh — the only render entry point
              build_video.py — narration-driven composition builder
              (duration from narration, Whisper-synced captions)
quality-control/   qc.sh + checklist — technical + visual gates
              gate.py — the single blocking gate (all Phase 3 checks)
              check-narration-fuzzy.py + check-sync.py + check-av.py
              + check-mix.py + check-top5-sum.py + normalize-loudness.py
videos/            Per-video working dirs (script, narration, composition, metadata)
output/            Final MP4s + metadata (MP4s are git-ignored)
scripts/           check-env.sh — environment verification
              fetch-assets.sh — font + music download (binaries not in git)
docs/              Architecture notes
```

## Pipeline — one URL in, one video out (Phase 3)

```bash
python3 pipeline/run.py --url <public Roblox URL> --format facts \
    --slug my-video --stage storyboard   # STOP POINT: owner reviews
# ... green light ...
python3 pipeline/run.py --slug my-video --stage gate
python3 pipeline/run.py --slug my-video --stage deliver
```

Stages: research (claims.json — every claim verified or excluded) →
script (English, 30–45 s) → storyboard (≥ 4 scenes, ≥ 2 motions) →
build → draft → final → normalize → gate → deliver. The driver stops
after the storyboard and waits for the owner's green light before voice
and render. See `pipeline/README.md`.

## Quality control

The blocking gate is `quality-control/gate.py` — one command runs every
Phase 3 check and exits non-zero on any FAIL. **A FAIL blocks delivery;
no manual override.** If a FAIL looks like a false positive, fix the
lexicon (`quality-control/narration-lexicon.json`) and re-run.

| Check | Gate | Tool |
|---|---|---|
| Format | 1080×1920, 30 fps, H.264, yuv420p | `gate.py` (ffprobe) |
| Technical | 9 scripted checks (duration, codec, no blackframes pic_th=0.98, final silence 0.5–1.75 s, no mid-silence > 1.0 s) | `quality-control/qc.sh` |
| Audio | AAC-LC stereo 48 kHz, \|audio − video\| ≤ 0.02 s | `quality-control/check-av.py` |
| Loudness | −14 ± 0.5 LUFS, true peak ≤ −1 dBTP | `quality-control/normalize-loudness.py` |
| Voice vs music | voice ≥ 6 dB above the bed, every speech window | `quality-control/check-mix.py` |
| Narration | fuzzy comparison (lexicon + numbers + difflib ≥ 0.80) of the Whisper-small transcript of the **final MP4** vs the script; last sentence complete | `quality-control/check-narration-fuzzy.py` |
| Sync | captions within 0.3 s of the spoken words (Whisper tiny timings) | `quality-control/check-sync.py` |
| Top 5 sum | displayed + spoken sums consistent with the announced total | `quality-control/check-top5-sum.py` |
| Listening aid | low-confidence Whisper words (< 0.6) with timestamps | in the gate report |

`quality-control/qc.sh` verifies the technical base; the narration,
sync, mix, loudness and A/V checks are separate scripts so each gate has
its own proof file. A render that fails any gate is never delivered. The
owner must listen to the voice before any manual publication.

## Costs — Phase 1

**$0.** HyperFrames (Apache 2.0), Node.js, FFmpeg, Chrome Headless Shell,
Muse TTS, Muse image generation and royalty-free music are all free in this
environment. No paid service is connected. Anything that would need payment
must be flagged to the owner **before** integration.

## Archiving

Final MP4s live in `output/` with a `metadata.json` next to them (source URL,
facts, voice, music attribution, QC result). Permanent archiving on Google
Drive is planned but **not connected yet** — the Drive connector reports
`not_connected` (checked 21 Nov 2026). Until the owner connects it, archive
locally in `output/` and deliver via a temporary Muse link (48 h max).

## Rules

`AGENTS.md` holds the permanent project rules: editorial standards, the
HyperFrames contract, Cloud limits, QC gates and the zero-paid-services
policy. Read it before changing anything.

## Status

- [x] Phase 1 — Foundation (infrastructure, templates, render test)
- [x] Phase 2 — Three videos (Facts, Top 5, Mysteries) — v3.1b delivered
      22 Nov 2026, all gates PASS (loudness −14 LUFS, narration fuzzy,
      sync ≤ 0.3 s, A/V gap ≤ 0.02 s, 48 kHz audio)
- [ ] Phase 3 — Repository + URL → video pipeline (in progress):
      this repo, `pipeline/run.py`, the blocking gate, one test video
      from a new public Roblox URL (stop point after script + claims +
      storyboard, voice and render only after the owner's green light)
