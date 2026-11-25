# Technical report — roblox-top5-thanksgiving (Top 5)

Format top5. Publish title "5 Roblox Games for Thanksgiving" (31 chars).
Built 25 Nov 2026. Publication target 26 Nov 2026 (Thanksgiving Day, USA).

## Deliverable

- MP4: `output/roblox-top5-thanksgiving.mp4`
- SHA-256: `6f8d07dda2101388defe6bb30fd5b436191d62147dc12576acd284c1c7df77a3`
- Duration: 43.067 s (video), 43.067 s (audio), gap 0.000 s
- Codec: H.264, 1080×1920, 30 fps; audio AAC 48000 Hz
- Script: 87 words, 8 sentences. Measured narration 42.60 s (2.0 wps).
  Last speech 42.21 s, end margin 1.0 s, final silence 0.63 s.
- Draft kept: `output/roblox-top5-thanksgiving-draft.mp4` (43.067 s, QC PASS).

## Gate — PASS 14/14

Report: `pipeline/roblox-top5-thanksgiving/gate.json`. Bed gain +10.42 dB.

| # | Check | Result |
|---|-------|--------|
| 1 | format 1080x1920/30fps/h264/yuv420p | PASS |
| 2 | qc.sh (9 checks) | PASS — final silence 0.63 s |
| 3 | audio 48kHz / A-V gap / loudness | PASS — 48000 Hz; gap 0.000 s; −14.28 LUFS; TP −1.43 dBTP |
| 4 | voice above music (≥ 6 dB) | PASS — worst window 11.8 dB |
| 5 | narration fuzzy (Whisper small) | PASS — 87/87 words, missing 0; final sentence COMPLETE |
| 6 | caption sync (Whisper tiny) | PASS — max \|start gap\| 0.14 s |
| 7 | duplicate images (max span ≤ 5.0 s, no reuse) | PASS — max span 5.0 s; 0 spans over 5.0 s; reuse: none |
| 8 | title / sentence (match + appear ≤ 0.3 s) | PASS — 8 sentences; mismatches []; late titles [] |
| 9 | empty image zone (never > 0.2 s) | PASS — max empty 0.2 s; 6 spans |
| 10 | first frame (title + image at t=0) | PASS — image std 54.85; title bright px 11353 |
| 11 | hook (≤ 12 words + digit/?/number-word) | PASS — 9 words; digit=True, number-word=True |
| 12 | brand (watermark ≥ 36 px, mascot ≥ 220 px) | PASS — watermark 36.0 px, present; mascot 240.0 px, present |
| 13 | visual change, image-only (≤ 5.0 s) | PASS — longest stretch 5.0 s; 13 image spans |
| 14 | top5 sum | PASS — 5 displayed, 5 spoken |

## Loudness

`pipeline/roblox-top5-thanksgiving/loudness.json`.
Before: −24.70 LUFS, TP −7.13 dBTP, LRA 3.0 LU.
After: −14.28 LUFS, TP −1.43 dBTP, LRA 2.5 LU.
Gain applied: +10.42 dB (single pass, within −14 ± 0.5 LUFS).

## Narration — words to listen (Whisper small, final MP4)

6 low-confidence words (< 0.6), all present in the transcript:

- "Five" 0.00–0.32 s, prob 0.24
- "five," 4.66–5.02 s, prob 0.53
- "giving" 20.84–21.06 s, prob 0.54
- "Thanksgiving" 27.32–28.06 s, prob 0.27
- "challenge" 28.06–28.66 s, prob 0.29
- "Grow" 31.18–31.46 s, prob 0.56

0 pronunciation-sensitive words unvalidated.

## Ranking (verified 25 Nov 2026, Roblox public games API)

Criterion: total visits. #1 Grow a Garden 36.0B, #2 99 Nights in the Forest
30.7B, #3 Fisch 5.2B, #4 Pet Simulator 99 2.7B, #5 NFL Universe Football
1.0B. Sum 75.6B; announced total "over 75 billion visits" (75).
Pills render 1.0B / 2.7B / 5.2B / 30.7B / 36.0B VISITS in scene order #5..#1.
Claims: 12, all verified, `pipeline/roblox-top5-thanksgiving/claims.json`.

## Second shots (mid-sentence splits, v5 precedent)

From the build-2 `transcript.json` word timings (see Limits):

- Scene 1 (#5): 8.50 s → nfl-detail.webp, ends 10.02 s
- Scene 2 (#4): 13.10 s → ps99-detail.webp, ends 16.48 s
- Scene 3 (#3): 20.28 s → fisch-detail.webp, ends 22.68 s
- Scene 4 (#2): 25.44 s → nights-detail.webp, ends 29.64 s
- Scene 5 (#1): 33.92 s → garden-detail.webp, ends 35.34 s
- Scene 6 (payoff): 40.28 s → share-friends.webp, ends 43.06 s

## Factory corrections made during this build

1. `rendering/build_video.py`: the 4C entrance-pinning regex
   `(title|head|num|label|q|sub)-\d+` did not include `game-\d+`, the
   top5 rank-title ids. Rank titles kept their scaled positions (scene
   start + 0.87–1.14 s); two of five appeared more than 0.3 s after their
   sentence started (measured on draft 1: game-1 at 5.23 s vs sentence
   4.82 s; game-5 at 31.48 s vs sentence 31.12 s). Added `game` to the
   regex; game tweens now pin to scene start at fixed 0.45 s.
2. `quality-control/check-title-sentence.py`: a scene's title resolved
   only from `title-N` or `head-N`; top5 rank scenes have neither, so all
   five rank sentences failed as "no title in scene". Added `game-N` as
   the fallback title (parse + resolution).
3. `templates/formats/top5.html`: `.visits-pill` had no z-index; after a
   second-shot crossfade the second image (later in DOM order) covered
   the pill — measured by `hyperframes check` (`text_occluded`,
   #pill-4 at 26.314 s, coveredFraction 1) and visible in draft frames
   (pill absent after the crossfade). Added `z-index: 3` to `.visits-pill`.
   The same one-line change was applied to the built composition
   `videos/roblox-top5-thanksgiving/index.html` to avoid a rebuild.
4. `templates/formats/top5.html`: brand added (watermark 36 px, mascot
   240×240, "FOLLOW NOOBNOMORE") — the template predated the brand and
   had neither.
5. Title-6 shortened from "SEND THESE GAMES TO A FRIEND." (3 rendered
   lines) to "SEND THESE GAMES." (2 lines, max-2-lines standard).
   Shares "games" with the total sentence and "send" with the share
   sentence.
6. `quality-control/narration-lexicon.json`: added phrase
   `"fish giving" → "fischgiving"` (same class as "brain rot" →
   "brainrot"): the TTS pronounces the compound as its two parts and
   Whisper tokenizes it as two words, identically on the clean narration
   and on the final mix. Gate narration: 86/87 before, 87/87 after.

## Publish metadata

`pipeline/roblox-top5-thanksgiving/publish.md` — `write-publish-md.py
--check`: PASS (title 31 chars, fan-made line, Kevin MacLeod CC BY 3.0
attribution, 5 hashtags, TikTok caption, share line verbatim).
Description additionally carries, outside the narration: "Bonus: three
working 99 Nights codes give 15 diamonds each (45 total):
awardwinner_yay, forestwakesup26, afterparty." (verified 25 Nov 2026;
general codes, not a Thanksgiving Challenge reward).
Attribution: `pipeline/roblox-top5-thanksgiving/attribution.txt` —
"Music: Basic Implosion by Kevin MacLeod
(https://incompetech.com/music/royalty-free/mp3-royaltyfree/Basic%20Implosion.mp3),
CC BY 3.0 — attribution required in video description".

## Limits

- Image-run sampling resolution ±0.5 s: the longest image span measures
  exactly 5.0 s (passes; a span of exactly 5.0 s passes). The scene-6
  payoff span is 4.94 s (35.34–40.28 s).
- TTS take is NOT byte-identical across rebuilds on this build: build 1
  narration 43.44 s, build 2 narration 42.60 s, same script text (the
  Facts v4 note of byte-identical rebuilds did not reproduce). Second-shot
  times must always be derived from the current build's transcript.json;
  the build-1 times were re-derived for build 2.
- HyperFrames check on the patched composition: ok=True, 0 errors
  (lint 27 warnings, layout 18 warnings — top-edge safe-zone warnings
  for the label/watermark, by template design — contrast 1, craft 2).
- Frames inspected full-res and at 540×960: t=0 (title + image),
  scene-1 title present at scene start, pills visible before and after
  every second-shot crossfade, final frame (title-6, share image,
  mascot, CTA "FOLLOW NOOBNOMORE").
