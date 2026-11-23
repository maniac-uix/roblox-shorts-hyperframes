# PHASE 4C — Pipeline and Gate Adjustments

Date: 2026-11-23. Scope: factory only (pipeline, gate, templates, builder). No new video, no voice, no render of a new video, no publication.

## 1. Regression run

Full updated gate run on all 6 existing videos, sequentially, 2026-11-23 20:27:19–20:33:09 UTC (log: `.cache-tmp/gate-4c/regression-4c.log`; reports: `audit-package/technical-reports/<slug>-gate-4c.json`). Bed gains used: Facts v4 +11.1 dB, Mysteries v4 +11.26 dB, Top 5 v3.1b +11.7 dB, Age check v3 +10.0 dB, Facts v3.1b +10.3 dB, Mysteries v3.1b +10.1 dB.

**Overall result: all 6 videos FAIL** (expected — every video fails at least one new blocking control; see table). All expected detections triggered on regression run #1. Zero internal fix cycles consumed of the 3 allowed.

### 1.1 Regression table (video × control, measured values)

| Control | Facts v4 (37.50 s) | Mysteries v4 (36.80 s) | Top 5 v3.1b (41.77 s, published) | Age check v3 (32.20 s, published) | Facts v3.1b (35.10 s) | Mysteries v3.1b (41.30 s) |
|---|---|---|---|---|---|---|
| 1 format 1080×1920/30fps | PASS | PASS | PASS | PASS | PASS | PASS |
| 2 qc.sh (9 checks) | PASS, final silence 0.61 s | PASS, 0.62 s | PASS, 0.75 s | PASS, 0.76 s | PASS, 0.75 s | PASS, 0.75 s |
| 3 audio 48 kHz / gap / loudness | PASS −14.16 LUFS / TP −1.49, gap 0.000 s | PASS −14.35 / −1.48, 0.000 s | PASS −14.11 / −1.36, 0.001 s | PASS −14.27 / −1.49, 0.000 s | PASS −14.39 / −1.03, 0.000 s | PASS −14.25 / −1.23, 0.000 s |
| 4 voice ≥ 6 dB above music | PASS, worst 10.7 dB | PASS, 10.7 dB | PASS, 10.3 dB | PASS, 12.2 dB | PASS, 10.9 dB | PASS, 11.3 dB |
| 5 narration fuzzy (Whisper small) | PASS 99/99, final sentence COMPLETE | PASS 98/98, COMPLETE | PASS 98/98, COMPLETE | **FAIL 106/107**, missing "selfie" heard "sucky" 8.38 s (prob 0.82), final sentence COMPLETE | PASS 94/94, COMPLETE | PASS 102/102, COMPLETE |
| 6 caption sync | PASS, max 0.12 s | PASS, 0.16 s | PASS, 0.12 s | PASS, 0.12 s | PASS, 0.16 s | PASS, 0.18 s |
| 7 duplicate images | **FAIL** max span 9.0 s; 2 spans over 5.0 s; reuse `assets/images/origin.webp` scenes [1, 2] | **FAIL** max 8.5 s; 5 spans over 5.0 s; reuse none | **FAIL** max 6.5 s; 3 spans over 5.0 s; reuse none (outro exception applied) | **FAIL** max 5.5 s; 2 spans over 5.0 s; reuse none | **FAIL** max 7.0 s; 3 spans over 5.0 s; reuse none | **FAIL** max 10.5 s; 4 spans over 5.0 s; reuse none |
| 8 title / sentence | **FAIL** 11 sentences; mismatches [3, 6, 8, 10]; late titles [2, 5, 7] | **FAIL** 10 sentences; mismatches [2, 5, 8, 9]; late titles [1, 3, 4, 5] | N/A — no composition timeline (pre-Phase-3 video) | **FAIL** 8 sentences; mismatches [6, 7]; late title [5] | N/A — no composition timeline | N/A — no composition timeline |
| 9 empty image zone | **FAIL** max empty 0.4 s; 6 spans | **FAIL** max 0.6 s; 5 spans | **FAIL** max 0.3 s; 7 spans | **FAIL** max 0.6 s; 6 spans | **FAIL** max 0.4 s; 6 spans | **FAIL** max 0.7 s; 5 spans |
| 10 first frame (t=0) | **FAIL** image std 5.91; title bright px 0 | **FAIL** std 8.07; title 0 px | **FAIL** std 5.85; title 0 px | **FAIL** std 5.91; title 0 px | **FAIL** std 5.91; title 0 px | **FAIL** std 8.05; title 0 px |
| 11 hook | PASS — 8 words; digit, ? | PASS — 12 words; ?, number-word "one" | PASS — 11 words; digit, number-word "five" | **FAIL** — 11 words; no digit, no ?, no number-word | **FAIL** — 6 words; no signal | **FAIL** — 16 words; number-word only |
| 12 brand | **FAIL** watermark declared 30.0 px (present, median 231.5 px, glyph 9 px half-scale); mascot declared 240.0 px, present NCC 0.959 | **FAIL** watermark 30.0 px (present, median 237.0 px); mascot 240.0 px, NCC 0.956 | N/A — no composition (pre-v4 video) | N/A — template predates brand (no watermark in composition) | N/A — no composition | N/A — no composition |
| 13 visual change, image-only | **FAIL** longest stretch 9.0 s; 7 image spans | **FAIL** 8.5 s; 7 spans | **FAIL** 6.5 s; 7 spans | **FAIL** 5.5 s; 7 spans | **FAIL** 7.0 s; 6 spans | **FAIL** 10.5 s; 8 spans |
| 14 Top 5 sum | — | — | PASS — count 5/5; displayed 311.3 ≥ announced 311; spoken 311.5 ≥ 311; \|311.3 − 311.5\| = 0.2 (≤ 1.0) | — | — | — |
| **Overall** | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |

### 1.2 Image spans (pixel measurement, 0.5 s sampling; only spans ≥ 1.0 s listed)

- Facts v4: hero 0.0–2.0 (2.0), robot 3.0–8.0 (5.0) + 9.0–11.5 (2.5), scale 12.5–19.5 (7.0), kids 21.0–24.0 (3.0), creator 24.0–27.0 (3.0), platform 28.5–37.5 (9.0).
- Mysteries v4: shadow 0.5–6.5 (6.0), book 7.5–13.0 (5.5), glitch 13.5–19.0 (5.5), admin 20.0–28.5 (8.5), legend 29.5–37.0 (7.5); plus two 1.0 s transition runs (19.0–20.0, 28.5–29.5).
- Top 5 v3.1b: podium 0.5–4.0 (3.5), garden 4.5–9.0 (4.5), pets 10.0–15.0 (5.0), sea 16.0–21.5 (5.5), brainrot 22.5–27.5 (5.0), town #1 28.5–35.0 (6.5), town outro 36.0–42.0 (6.0).
- Age check v3: 0.5–2.5 (2.0), 3.5–6.5 (3.0), 7.5–10.5 (3.0), 11.5–14.5 (3.0), bands 16.0–21.5 (5.5), 21.5–24.5 (3.0), lock 26.5–32.0 (5.5).
- Facts v3.1b: 0.0–1.5 (1.5), 2.5–7.5 (5.0), 8.5–14.0 (5.5), 15.0–19.5 (4.5), 21.0–28.0 (7.0), 29.5–35.0 (5.5).
- Mysteries v3.1b: 0.5–8.0 (7.5), 8.0–9.0 (1.0), 9.0–14.0 (5.0), 14.5–20.5 (6.0), 20.5–22.0 (1.5), 22.0–32.5 (10.5), 32.5–33.5 (1.0), 33.5–41.5 (8.0).

A span of exactly 5.0 s passes (Facts v3.1b 2.5–7.5; Mysteries v3.1b 9.0–14.0; Top 5 pets 10.0–15.0 and brainrot 22.5–27.5). A 5.5 s span is one 0.5 s sample above the limit and fails.

### 1.3 Empty-zone spans (10 fps; only spans > 0.2 s fail)

- Facts v4: max 0.4 s — (20.0, 20.4), (27.4, 27.8); also (0.0, 0.1), (2.4, 2.6), (8.6, 8.8), (11.9, 12.2) at ≤ 0.3 s.
- Mysteries v4: max 0.6 s — (6.8, 7.4), (19.1, 19.7); also (0.0, 0.3), (13.0, 13.5), (28.9, 29.3).
- Top 5 v3.1b: max 0.3 s — (4.0, 4.3), (15.4, 15.7), (27.9, 28.2); also (0.0, 0.1), (9.3, 9.5), (21.8, 22.0), (35.5, 35.7).
- Age check v3: max 0.6 s — (25.5, 26.1); also (14.9, 15.3) 0.4 s, (0.0, 0.1), (2.8, 3.0), (6.9, 7.1), (11.0, 11.2).
- Facts v3.1b: max 0.4 s — (8.0, 8.4); also (0.0, 0.1), (1.9, 2.1), (14.3, 14.6), (20.1, 20.4), (28.6, 28.9).
- Mysteries v3.1b: max 0.7 s — (20.8, 21.5); also (0.0, 0.3), (8.0, 8.6), (14.0, 14.5), (32.7, 33.2).

### 1.4 Title / sentence detail (composition timeline + caption timings)

Facts v4 (11 sentences): mismatches S3 ("Roblox itself means robots plus blocks." vs "STARTED IN 2004 AS DYNABLOCKS"), S6 ("Back in 2020, this is what Roblox said." vs "85 MILLION PLAYERS A DAY"), S8 ("And since 2013, creators can turn their Roblox…" vs "OVER HALF OF AMERICAN KIDS"), S10 ("So Roblox is not just a game." vs "BUILT BY ITS PLAYERS."); late titles S2 +0.70 s, S5 +0.67 s, S7 +0.74 s (S1 +0.18 s, S4 −0.11 s, S9 +0.20 s pass).

Mysteries v4 (10 sentences): mismatches S2 ("His name was 1x1x1x1." vs "THE ROBLOX HACKER MYTH."), S5 ("But in 2011, a Roblox admin revealed the truth…" vs "A TEST ACCOUNT, NOT A HACKER"), S8 ("The hacker never existed." vs "THE LEGEND LIVES ON."), S9 ("So the answer is no." vs "THE LEGEND LIVES ON."); late titles S1 +1.25 s, S3 +0.58 s, S4 +0.32 s, S5 +0.96 s (S8 +0.10 s passes).

Age check v3 (8 sentences): mismatches S6 ("A twelve-year-old can reach up to fifteen…" vs "6 AGE GROUPS"), S7 ("Chat stays off under nine unless a parent agrees." vs "YOUR AGE, NOT YOUR BIRTHDAY."); late title S5 +1.23 s (S1 +0.21 s, S2 +0.22 s, S3 +0.13 s, S4 +0.11 s, S7 +0.07 s pass).

## 2. Acceptance criteria — verified

- **Facts v4 MUST FAIL — confirmed.** Robot image `assets/images/origin.webp` reused in scenes [1, 2] (images map); pixel spans robot 5.0 s + 2.5 s (timeline view: 9.56 s continuous across the two scenes); platform 9.0 s and scale 7.0 s also over 5.0 s. Titles contradicting the voice: S6 "Back in 2020…" under "85 MILLION PLAYERS A DAY"; S8 "real money" sentence under "OVER HALF OF AMERICAN KIDS". Empty zone max 0.4 s. First frame empty (std 5.91, title 0 px). Brand fails on the 30 px watermark. Visual change image-only: longest stretch 9.0 s.
- **Mysteries v4 MUST FAIL — confirmed.** Empty image zones 0.3–0.6 s at scene changes (max 0.6 s at 6.8–7.4 and 19.1–19.7); all 5 images over 5.0 s (6.0, 5.5, 5.5, 8.5, 7.5); S8 "The hacker never existed." under "THE LEGEND LIVES ON.". First frame empty (std 8.07, title 0 px). Brand fails on the 30 px watermark. Visual change image-only: longest stretch 8.5 s.
- **Top 5 v3.1b / Age check v3 / Facts v3.1b / Mysteries v3.1b — reported in full in §1.1.** No threshold was loosened for any of them (see §4).

## 3. Implementations — the 7 new blocking controls

Gate rewritten: `quality-control/gate.py` (14 checks; checks 1–6 unchanged; check 14 = Top 5 sum, top5 only). Overall PASS iff every verdict is PASS, recorded, or N/A. Per-check JSONs saved under `.cache-tmp/gate/`; report carries `image_runs`, `title_sentence`, `empty_zone`, `first_frame`, `hook`, `brand`, `visual_change` sub-objects. New `--composition` argument (default `videos/<slug>/index.html`).

### 3.1 Duplicate images (check 7) — `quality-control/check-image-runs.py`, `quality-control/frame_probe.py`

- Image identity: 4×4×4 RGB histogram (64 bins) of the probe crop, sampled every 0.5 s, running-mean reference, join threshold 0.20, adjacent-run merge 0.15. Calibration on Facts v4 + Mysteries v4: same image hist_dist ≈ 0.03–0.04, different images ≥ 0.24. aHash/dHash were REJECTED (within-scene consecutive Hamming up to 41/45 — zoom jump-cuts fragment runs).
- Probe crop (full-scale): x 140–940, y 850–1130. Inside the image for all scenes; avoids the mascot zone (x 690–930, y 1134–1374), source-note zone, captions (y 1520), CTA (y 1760).
- Duration rule uses pixel spans (transition time excluded — the span ends when the image stops being visible). Reuse rule uses `metadata.json["images"]` (scene → file); keys like "4b" are second shots inside one scene, NOT reuse. Pixel clustering is fallback only: it does NOT group Top 5's two town spans (hist_dist 0.209 > 0.15) because the outro reframes the image — the threshold was not raised to force the grouping.
- **Top 5 outro exception (named, explicit):** format == top5 AND the reappearing span is the last image span AND its previous span is the immediately preceding span AND the image equals the #1 scene's image. Applied on Top 5 v3.1b (`outro_exception_applied: true`; reuse reported as none). The outro span itself (6.0 s) still fails the duration rule — the exception waives reuse only, never duration.
- Runs < 1.0 s are transition fragments and are not counted as image spans.

### 3.2 Title / sentence (check 8) — `quality-control/check-title-sentence.py`

- Inputs: scene windows + head texts + first GSAP tween position per head id, parsed from the composition `videos/<slug>/index.html`; sentence timings from `metadata.json` captions.
- Match: shared content word (lowercased, stopwords removed, prefix match ≥ 4 chars for plurals / hack–hacker, number-words mapped to digits). Timing: PASS iff the title appears ≤ sentence_start + 0.3 s (appearing early is fine).
- N/A without a composition timeline (Top 5 v3.1b, Facts v3.1b, Mysteries v3.1b — pre-Phase-3 videos; the missing input is recorded, never invented).

### 3.3 Empty zone (check 9) — `quality-control/check-empty-zone.py`

- Definition of "empty": probe-crop grayscale stddev < 12, sampled at 10 fps. Calibration: empty frames stddev 5.9–10.1; image frames ≥ ~17 (p10 20.0 Mysteries / 33.9 Facts). FAIL if any empty span > 0.2 s.
- Mechanism (from the built compositions): the outgoing slide-out ends exactly at the scene end; the incoming slide-in (0.45 s template × global factor ~3.1–3.7 × scene factor, e.g. 1.72 s in Mysteries v4) needs ~0.4 s to cover the crop after the boundary. Facts v4 fails this control too (max 0.4 s) — same slide mechanism, honest finding.

### 3.4 First frame (check 10) — `quality-control/check-first-frame.py`

- At t=0: image stddev in the probe crop (PASS ≥ 12) AND title bright pixels in the title band x 120–960, y 340–560 (> 0). All 6 videos: image std 5.85–8.07, title 0 px. Cause: title-0 tween starts 0.18 s (Facts v4) / 1.25 s (Mysteries v4) with opacity 0 before; the scene-0 image slides in from an empty frame.

### 3.5 Hook (check 11) — `quality-control/check-hook.py`

- From the script in `metadata.json`: first sentence ≤ 12 words AND a digit, a question mark, or a number-word. "Surprising statement" is not automatically checkable, so a hook must carry a number or a question to pass (same rule as `run.py`'s script stage).

### 3.6 Brand (check 12) — `quality-control/check-brand.py`

- Watermark: presence is measured on pixels (pixels within RGB distance 60 of #1FD1C1 in the top-right zone x 630–930, y 145–195; v4 median ~232–237 px), but the blocking comparison is the DECLARED font-size from the composition CSS (≥ 36 px). Finding: a pixel-measured "≥ 36 px tall" threshold could never pass with a 36 px font — a 30 px font renders glyphs ≈ 18 px tall at full scale (9 px at half-scale), i.e. ~0.6em.
- Mascot: size = declared width from the composition CSS (≥ 220 px); presence = masked NCC against the downscaled mascot PNG at the declared position (threshold 0.5; present 0.953–0.959, absent −0.16 / 0.20).
- N/A pre-v4 (no composition, or template predates brand). Applies only to videos built from v4 templates onwards.
- **Watermark finding (real, not a control bug):** both v4 videos were built with a 30 px watermark under the Phase 4B rule, so against the new ≥ 36 px minimum they FAIL this control. Not re-rendered, control not weakened. Templates updated to 36 px for future videos (§6).

### 3.7 Visual change, image-only (check 13)

- From the same image-runs spans as check 7. FAIL if any span > 5.0 s without a new image. Zooms, pans and fades do not count.
- **Supersedes the Phase 4B frame-diff warning** (`quality-control/check-visual-change.py` is no longer called by the gate; a supersession note was added to its header; the file is kept for calibration history). The 4B instrument measured 2.0 s max gaps on the v4 videos because it counted zooms; the image-only control measures 9.0 s / 8.5 s on the same files.

## 4. Failures on owner-validated videos — why the thresholds were not loosened

- **Top 5 v3.1b (published at the owner's request):** fails duplicate-images (sea 5.5 s, town #1 6.5 s, town outro 6.0 s), empty-zone (max 0.3 s, 7 spans), first-frame, visual-change (6.5 s). Reuse passes (outro exception applied). Top 5 sum passes. These are real defects by the 4C standard: the over-5.0 s spans are 5.5–6.5 s (above the ±0.5 s sampling resolution), the empty spans are 0.3 s (3 consecutive empty frames at 10 fps, above 0.2 s). The video is published and is NOT re-rendered.
- **Age check v3 (published by the owner himself):** fails narration 106/107 (pre-existing Phase 3 finding — "selfie" heard as "sucky" at 8.38 s, prob 0.82; unchanged by 4C), duplicate-images (bands 16.0–21.5 and lock 26.5–32.0, both 5.5 s), title/sentence (mismatches S6, S7; late S5 +1.23 s), empty-zone (max 0.6 s at 25.5–26.1), first-frame, hook (11 words, no signal), visual-change (5.5 s). Brand N/A (template predates brand). Published, not re-rendered.
- **Facts v3.1b / Mysteries v3.1b:** superseded by the v4 videos for the same topics; they fail the same new controls (max spans 7.0 s / 10.5 s; hooks fail; title/sentence and brand N/A for lack of a composition). Their failure is consistent with the v4 findings — the pipeline defect predates Phase 4B.

## 5. Storyboard model — validator and dry-run

`pipeline/validate-storyboard.py`: strict `beats.json` mode (one beat = `{ phrase, titre, image, durée }`; checks titre–phrase match, image ≤ 5.0 s per beat, no image reused across scenes except the named Top 5 outro exception) + `--legacy` dry-run mode that derives beats from an existing storyboard + `metadata.json` (captions, images map, scene windows) and reports violations without rendering.

`pipeline/run.py` stage_storyboard now REQUIRES `beats.json` (blocking; failure message points at the validator). The image-generation path for future videos exists in the model (generate a distinct image per beat when no existing image truly illustrates the sentence) but was not called in this phase — no new images were generated.

Dry-run (legacy) against the existing v4 storyboards:

- Facts v4: 11 beats, **9 violations, FAIL** — titre-match beats 2/5/7/9; `origin.webp` reused scenes [1, 2]; segments over 5.0 s: origin 9.56 s, scale 8.20 s, platform 9.86 s; kids 3.56 s + creator 3.88 s pass.
- Mysteries v4: 10 beats, **9 violations, FAIL** — titre-match beats 1/4/7/8; every scene image over 5.0 s: shadow 7.14 s, book 6.06 s, glitch 6.08 s, admin 9.82 s, legend 7.67 s; no reuse.

Two measurement angles for image spans: pixel runs exclude transition time (Facts origin 5.0 + 2.5 s); legacy timeline segments use full scene windows (origin 9.56 s continuous). Both detect the same defect; the pixel view is the gate's, the timeline view is the storyboard validator's.

Extra finding: Facts v4 `metadata.json` records the second-shot image as `assets/images/creator.webp`, which does NOT exist (real file is `assets/images/facts/creator.webp`); the render is unaffected (a copy sits in `videos/roblox-facts-older-than-you-think-v4/assets/images/`).

## 6. Templates and builder (for future videos)

- Watermark 36 px in `templates/formats/facts.html` + `mysteries.html` (was 30 px). Scene-0 slide-in + title-pop tweens removed in facts/mysteries (slide-outs kept). Placeholder heads (`HEADLINE — NOT SET`) on all storyboard-driven head/title/sub elements: facts 7, mysteries 6, top5 9, game-discoveries 7. Untouched: num-*, label-*, q-0, CTA, pill.
- `rendering/build_video.py` §5c4b: fails if `HEADLINE — NOT SET` survives substitution, or if no `--heads` was passed (no-op for templates without the placeholder). §5e `repl_tween`: `#inner-*` slide in/out fixed 0.45 s (slide-in at scene start, slide-out ending at scene end); `#title|head|num|label|q|sub-*` entrances pinned to scene start at 0.45 s; img-* zooms, progress/glows, CTA/mascot, source notes untouched. Dry simulation on Mysteries v4 numbers: head-3 → position 19.28, duration 0.45; inner-3 slide-out → 28.65, 0.45; inner-4 slide-in → 29.10, 0.45; img-3 zoom → 3.30 s (still scaled, correctly NOT 0.45).
- `pipeline/run.py` deliver stage: generates `publish.md` when `pipeline/<slug>/publish-title.txt` exists; never invents a title.
- publish.md generator: `pipeline/write-publish-md.py` (+ `--check` mode). Verified: `--check` passes all six elements on both existing v4 `publish.md` files (titles 45 / 31 chars; description carries "fan-made, not affiliated with or endorsed by Roblox", Kevin MacLeod CC BY 3.0 attribution, ≤ 5 hashtags; short TikTok/Reels caption; share line "Send this to a friend who plays Roblox"). Neither v4 `publish.md` file was rewritten.

## 7. Files changed / created

- `quality-control/gate.py` — rewritten (14 checks).
- `quality-control/frame_probe.py`, `check-image-runs.py`, `check-empty-zone.py`, `check-first-frame.py`, `check-brand.py`, `check-title-sentence.py`, `check-hook.py` — new check scripts.
- `quality-control/check-visual-change.py` — header supersession note (no longer called by the gate; file kept for calibration history).
- `pipeline/validate-storyboard.py`, `pipeline/write-publish-md.py` — new.
- `pipeline/run.py` — storyboard stage requires `beats.json`; deliver stage generates `publish.md`.
- `rendering/build_video.py` — placeholder survival check + fixed 0.45 s tween logic.
- `templates/formats/facts.html`, `mysteries.html`, `top5.html`, `game-discoveries.html` — 36 px watermark, placeholder heads, scene-0 slide-in removed (facts/mysteries only).
- `AGENTS.md` — new §11 (Phase 4C rules); §10 corrected (watermark 30 px → 36 px; visual-change control marked SUPERSEDED in Phase 4C; mascot position corrected bottom-left → bottom-right, `left:690px; top:1134px`).
- `audit-package/PHASE4C-REPORT.md` — this file.
- `audit-package/technical-reports/top5-v3.1b-values.json` — Top 5 sum reference values (displayed badges verified first-hand from rendered frames: 36.0 / 45.5 / 65.6 / 74.5 / 89.7; spoken from the script: 36, about 45.5, about 65.5, about 74.5, almost 90 → sum 311.5; displayed sum 311.3; announced total 311).
- `audit-package/technical-reports/<slug>-gate-4c.json` — the 6 regression gate reports (evidence for §1).

## 8. Bugs encountered and limits

- Template header comments nearly broke the placeholder check (the literal string inside `<!-- -->` would have failed every build) — fixed by rewording the comments.
- `top5.html` visits pills are `<span>`s, so the `--heads` regex (h1/p only) cannot substitute them — stale counts could render on a future Top 5. Follow-up, not fixed in this phase.
- First-frame template fix scoped to facts/mysteries only — top5/game-discoveries still slide scene 0 in. Follow-up, not fixed in this phase.
- HyperFrames check-cache trap (latent since Phase 3, NOT fixed in code): `npx hyperframes check` returns a cached report with no "report saved to" line, and `build_video.py` judges the check only by that line → false FAILED. Workaround: delete `videos/<slug>/.hyperframes/cache/check.json` before the run.
- Sampling resolution: image spans ±0.5 s (0.5 s sampling); empty spans ±0.1 s (10 fps). Transition frames can form short self-similar runs (e.g. two 1.0 s runs in Mysteries v4) that count as image spans but never affect a verdict (≤ 1.0 s).
- Title/sentence check requires a composition timeline; pre-Phase-3 videos record N/A for it, and brand records N/A pre-v4. N/A means "the input does not exist for this video", never a pass.
- `set_duration` in `build_video.py` only rewrites an existing `duration:` key; the effective duration is still 0.45 s (verified by dry simulation).
- No new video was produced in this phase; all template/builder changes are unproven on a real render until the next video build.
