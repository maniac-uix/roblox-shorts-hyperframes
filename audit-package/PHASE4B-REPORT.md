# PHASE 4B REPORT — Brand and Retention (v4)

Date: 23 Nov 2026. Scope: Facts v4 (`roblox-facts-older-than-you-think-v4`)
and Mysteries v4 (`roblox-mystery-1x1x1x1-v4`). Both re-rendered from the
Phase 2 v3.1b topics with the same claims.json sources; no new facts.
Gate: `quality-control/gate.py` — blocking, no manual override. No stop
point in Phase 4B; the gate decides.

## 1. Deliverables

| Video | File | Duration | SHA-256 |
|---|---|---|---|
| Facts v4 | `output/roblox-facts-older-than-you-think-v4.mp4` | 37.50 s | `4a3c751990832d18fd55ca7c533a1f3fce88012897d053a27a063d7b9887f115` |
| Mysteries v4 | `output/roblox-mystery-1x1x1x1-v4.mp4` | 36.80 s | `7740be6758803e8fd0f9366277f61f0f8df05bbf0939d897677c646354e07eef` |

Both 1080×1920, 30 fps, H.264, AAC 48 kHz. Gate reports:
`pipeline/<slug>/gate.json`; loudness:
`pipeline/<slug>/loudness.json`; attribution:
`pipeline/<slug>/attribution.txt`; publish text:
`pipeline/<slug>/publish.md`.

## 2. Gate results — final runs (PASS)

### Facts v4 — gate run #3, PASS

- format: PASS — 1080×1920 h264 yuv420p @ 30/1
- qc.sh (9 checks): PASS — final silence **0.61 s**
- audio: PASS — 48000 Hz; A/V gap 0.000 s (gate ≤ 0.02 s);
  **−14.16 LUFS** (gate −14 ± 0.5); TP **−1.49 dBTP** (gate ≤ −1)
- voice above music (≥ 6 dB): PASS — worst window **10.7 dB**
  (bed gain +11.1 dB)
- narration fuzzy (Whisper small): PASS — **99/99 words**, missing 0;
  final sentence COMPLETE
- caption sync (Whisper tiny): PASS — max |start gap| **0.12 s**
  (gate ≤ 0.3 s)
- visual change: recorded — max gap **2.0 s**, 55 changes @ thr 0.01
  (non-blocking, §5)

Loudness before: −25.26 LUFS / TP −7.86 / LRA 2.2; after: −14.16 LUFS /
TP −1.49 / LRA 1.9. Script: 99 words, 11 sentences; measured narration
37.08 s, last speech 36.63 s; video 37.48 s (build) / 37.50 s (render).

Listen-to list (low-confidence, 0 pronunciation-sensitive):
"robots" 7.28 s (prob 0.29).

### Mysteries v4 — gate run #3, PASS

- format: PASS — 1080×1920 h264 yuv420p @ 30/1
- qc.sh (9 checks): PASS — final silence **0.62 s**
- audio: PASS — 48000 Hz; A/V gap 0.000 s;
  **−14.35 LUFS**; TP **−1.48 dBTP**
- voice above music (≥ 6 dB): PASS — worst window **10.7 dB**
  (bed gain +11.26 dB)
- narration fuzzy (Whisper small): PASS — **98/98 words**, missing 0;
  final sentence COMPLETE
- caption sync (Whisper tiny): PASS — max |start gap| **0.16 s**
- visual change: recorded — max gap **2.0 s**, 47 changes @ thr 0.01
  (non-blocking, §5)

Loudness before: −25.61 LUFS / TP −5.94 / LRA 3.6; after: −14.35 LUFS /
TP −1.48 / LRA 3.5. Script: 98 words, 10 sentences; measured narration
36.36 s, last speech 35.92 s; video 36.77 s (build) / 36.80 s (render).

Listen-to list (low-confidence, 0 pronunciation-sensitive):
"exploiters" 14.02 s (0.59); "for" 35.32 s (0.50); "Sagan." 35.48 s
(0.54) — the "Forsaken" hearing, see §4.3.

## 3. Failed gate runs and fixes

### Facts v4

- Run #1: FAIL — qc.sh final silence 0.45 s (gate [0.50, 1.75] s).
  Cause: loudnorm's +9.54 dB gain lifts the music-bed fade tail above
  the silence threshold; raw render measured 0.56 s, normalised file
  0.45 s. Fix: `run.py --end-margin` default 0.6 → **0.85** (gate
  threshold unchanged). Evidence: `gate-run1-fail.json`,
  `loudness-run1.json`.
- Run #2: FAIL — narration fuzzy 98/100, missing 2; final sentence
  COMPLETE. Missing: script "1" heard as "1st" (S4 "September 1,
  2006" — TTS correctly says "first"); script "as" heard as "says"
  (S5 "As of February 2025" — all three models hear "says" on the
  clean narration: tiny p=0.99, base p=0.67, small p=0.58 — genuine
  TTS defect). Fixes: added `"1st": "1"` to the lexicon (ordinal form,
  same class as "18th"); rephrased S5 to "In February 2025, over
  *85 million* players log in daily." (same dated fact, same claim).
  No masking variant was added for "says". Evidence:
  `gate-run2-fail.json`, `loudness-run2.json`, `narration-run2.json`.
- Build #3 precheck (clean narration): 98/99 at first, missing
  "dynablocks" heard as "dynablux" (prob 0.56). Three-model segment
  test: tiny "Dynoblocks." (0.54), base "Dynablox." (0.57), small
  "Dynabloks" (0.57) — all the DynaBlocks family, unstable Whisper
  decoding of a proper noun, same class as existing variants
  "dinoblocks"/"dinoblox"/"dynablox". Added `"dynablux":
  "dynablocks"` to the lexicon; re-ran precheck: PASS 99/99.
  Evidence: `narration-run3-precheck.json`.

### Mysteries v4

- Run #1: FAIL — narration fuzzy 98/99, missing 1; caption sync FAIL,
  max |start gap| 0.78 s. Missing: script "the" (S3 "The name first
  appeared…") heard as "his" by all three models on the clean
  narration (tiny p=0.97, base p=0.39, small p=0.10) — genuine TTS
  defect, no variant added. Sync: caption 5 (S6 "1x1x1x1 was a test
  account…") start gap −0.78 s. Root cause: the TTS spells "1x1x1x1"
  slowly (~2.2 s, "one x one x…") in sentence-initial position;
  speech onset ≈ 24.4 s (all three models hear the username in the
  isolated 24.0–26.2 s window; RMS energy 24.4–26.5 s), while small
  latched the caption at 26.20 s (near the end of the spelling) and
  tiny re-anchored across the mid-word pause to 26.92 s. Fixes:
  rephrased S3 to "It first appeared in 2007, …" and S6 to "It was a
  test account, …" (same facts; "It" = the name / 1x1x1x1 from S2).
  Evidence: `gate-run1-fail.json`, `loudness-run1.json`,
  `narration-run1.json`, `sync-run1.json`.
- Run #2: FAIL — narration fuzzy 97/98, missing 1; final sentence
  INCOMPLETE. Sync PASS (0.16 s). Missing: script "forsaken" (last
  word) heard as "for" + "sagan". Three-model test on the final
  sentence: clean narration — tiny "for Sagan", base "for Saken",
  small "Forsaken"; mix — tiny "for second", base "for Sagan",
  small "for Sagan". Small hears "Forsaken" exactly on the clean
  narration, so the voice renders the word correctly; the /k/→/g/
  voicing confusion appears only under the music bed. Fix: added
  `"sagan": "forsaken"` (variant) and `"for sagan": "forsaken"`
  (phrase) to the lexicon — same class as the existing
  "saken"/"for saken" variants for this word. The word stays on the
  listen list ("Sagan." 35.48 s, prob 0.54) for a human ear check.
  Evidence: `narration-run2.json` (run #2 gate report was overwritten
  by run #3; run #2 values are recorded here).
- Build #2 precheck (clean narration): PASS 98/98, missing [].
  Evidence: `narration-run2-precheck.json`.

## 4. What changed in Phase 4B

### 4.1 Brand (templates, not per video)

- `templates/formats/facts.html`, `templates/formats/mysteries.html`:
  persistent "NoobNoMore" watermark (top-right, right edge 1080−150 px,
  top 150 px, 30 px Montserrat 800, #1FD1C1, opacity 0.85); last scene
  mascot (240×240 px) + CTA **"FOLLOW NOOBNOMORE"** (replaces "FOLLOW
  FOR MORE"); 3-segment zoom per scene (jump cuts at 1/3 and 2/3).
  Brand palette: turquoise #1FD1C1 / amber #FFB020 / purple #7A4DF0.
  Format accents unchanged (Facts teal, Mysteries purple).
- Mascot: `assets/brand/noobnomore-mascot-transparent.png` (1600×1600,
  SHA-256 `58bfc9216dee17e61e1c4ccc38d359a010eb998322688c26cf70732b2d013b6b`),
  copy of `~/workspace/noobnomore/noobnomore-mascot-transparent.png`.
  **Local-only, git-ignored, never pushed.** `build_video.py` copies it
  into each video folder at build time and warns if a template
  references a missing brand asset.
- Watermark/mascot/CTA positions verified on rendered frames (full-res
  + 540×960 phone size): watermark clear of pill and progress bar;
  mascot bottom 1374, clear of caption (y1520) and CTA zone (y1760).

### 4.2 Pipeline rules

- Hook (blocking, `pipeline/run.py` stage_script): first sentence ≤ 12
  words AND digit / `?` / spelled-out number word (one..twenty,
  thirty…ninety, hundred, thousand, million, billion). "Surprising
  statement" is not automatically checkable, so the enforceable rule is
  digit-or-question. Facts hook: 8 words, digit, question-mark — PASS.
  Mysteries hook: 12 words, question-mark, number-word "one" — PASS.
- Loop (report-only): shared content word between first and last
  sentence, excluding stopwords. Facts: PASS (22, years). Mysteries:
  PASS (game).
- Rhythm: 3-segment zoom cut per scene (see §4.1); no scene split into
  extra scenes; existing images only.
- Final silence: `--end-margin` default 0.85 (was 0.6); gate threshold
  unchanged (0.5–1.75 s). Measured final silence: Facts 0.61 s,
  Mysteries 0.62 s (target band 0.5–0.7 s).
- Source-note fade-out (`rendering/build_video.py`): a note belongs to
  the FIRST sentence of its scene and fades out 0.2 s after that
  sentence's caption ends. Facts v4: Feb 2025 note in 12.74 s / out
  17.72 s; Apr 2020 note in 21.42 s / out 24.54 s (build #1 timings;
  re-timed per build).
- Second shot (`pipeline/second-shot.py`, new): parameterized crossfade
  to a second image mid-scene. Facts v4 scene 4: kids → creator at
  23.74 s (build #3), Ken Burns 3.88 s to 27.62 s.
- `pipeline/run.py`: `--end-margin` argparse; `stage_source_notes`
  `_date_citations()` handles "undated" (never citable by date),
  "YYYY", "YYYY-MM", "YYYY-MM-DD" without fabricating a day/month;
  storyboard `"*"` removal on both sides (no stray space before a
  period).

### 4.3 Lexicon additions (all Whisper respellings, none masking a voice defect)

- `"1st": "1"` (ordinal, same class as "18th").
- `"dynablux": "dynablocks"` (proper noun, three-model evidence §3).
- `"sagan": "forsaken"` + phrase `"for sagan": "forsaken"` (proper
  noun, small hears "Forsaken" on the clean narration; /k/→/g/
  voicing confusion under the bed only).
- "selfie" remains the only pronunciation-sensitive word; no variant
  was added for any genuinely misrendered word ("says", "his").

### 4.4 Scripts (same claims, hooks and endings rewritten)

- Facts v4: 99 words, 11 sentences. Hook: "Did you know Roblox is 22
  years old?" Ending loops back: "22 years later, it is still built by
  its own players." First-scene title: "22 YEARS OLD."
- Mysteries v4: 98 words, 10 sentences. Hook: "Could one username hack
  your account, destroy your game, and ban you?" Ending loops back:
  "But the legend lives on, as a killer in the game Forsaken."
  First-scene title: "THE ROBLOX HACKER MYTH."

## 5. Visual-change gate control — calibration and decision

New: `quality-control/check-visual-change.py` (`--mp4 --threshold
--max-gap`); gate check 7 runs it at threshold 0.01 / max-gap 4.0 s and
records the result as a **non-blocking warning** (never PASS/FAIL).

Calibration on the 5 existing videos (all good, motion-rich):

| Method | Facts v3.1b | Top 5 v3.1b | Mysteries v3.1b | Age-check v3 | Throw Food |
|---|---|---|---|---|---|
| scdet full-fps T=0.05 (changes / max gap s) | 4 / 18.33 | 2 / 20.07 | 6 / 19.93 | 3 / 15.70 | 7 / 10.33 |
| scdet T=0.08/0.10/0.15 | 0 / full dur. | 0 / full dur. | 0 / full dur. | 0 / full dur. | 0 / full dur. |
| frame-diff fps=2 T=0.01 | 39 / 4.50 | 45 / 4.00 | 46 / 3.50 | 38 / 3.50 | 34 / 4.00 |
| frame-diff fps=2 T=0.02 | 32 / 5.50 | 34 / 4.77 | 37 / 5.00 | 28 / 4.00 | 26 / 4.50 |

Decision: **warning, not blocking.** Full-fps scdet never reaches 0.08
on any good video (factory motion is smooth slides/zooms, not hard
cuts). Even the best instrument (fps=2 frame-diff, T=0.01) leaves Facts
at 4.50 s (> 4.0 s) and Top 5 / Throw Food exactly on the limit at
4.00 s — zero margin; at T=0.02 four of five good videos fail
(4.50–5.50 s). The 4.0 s limit is unachievable for these videos (slow
scenes + the intentionally static final payoff/CTA scene). Negative
tests separate clearly: 10 s black clip and 10 s frozen-frame clip both
measure 0 changes / max gap 10.00 s at fps=2, T=0.01/0.02 (checker exit
1). If a future blocking version is wanted, either the limit must rise
above ~4.5 s or the slow stretches must be re-cut.

v4 measured values (fps=2, T=0.01): Facts draft 57 changes / 2.0 s,
final 55 / 2.0 s; Mysteries draft #1 51 / 2.0 s, draft #2 46 / 2.0 s,
final 47 / 2.0 s. The 3-segment zoom halves the max gap vs v3
(Facts 4.50 s → 2.0 s).

## 6. Frame verification (inspected by the coordinator)

- Facts v4 draft #3: 4 full-res frames (hook 0.5 s, S5 14.0 s, second
  shot 25.0 s, payoff 34.5 s) + 1 phone-size frame — 0 defects.
  Final file: 2 full-res frames (hook 0.5 s, payoff 34.5 s) — 0 defects.
- Mysteries v4 draft #1: 8 full-res + 2 phone-size frames — 0 blocking
  defects. Draft #2: 3 full-res + 1 phone-size (rephrased S3/S6,
  payoff) — 0 defects. Final file: 2 full-res frames (hook 0.5 s,
  payoff 35.0 s) — 0 defects.
- Watermark present top-right on every frame, clear of pill/progress
  bar. Mascot + amber "FOLLOW NOOBNOMORE" CTA in both last scenes,
  legible at 540×960. Source notes on the correct scenes and faded out
  on time. Second-shot crossfade (Facts scene 4) confirmed on frame.

## 7. Bugs encountered and limits

1. **Render killed by SIGTERM (Facts draft #3, first attempt):** the
   render died 31 s in; `~`/`~/.cache` had reverted to group-writable
   (2770) and HyperFrames refused its cache. Fixed with
   `chmod go-w ~/.cache ~` + `npx hyperframes browser ensure`, then
   re-rendered. The permission revert recurs between sessions.
2. **HyperFrames check-cache trap (latent, NOT fixed in code):**
   `build_video.py` judges `npx hyperframes check` only by the "report
   saved to" line; a cached ok:true report reads as FAILED. Workaround:
   delete `videos/<slug>/.hyperframes/cache/check.json` before the run.
3. **TTS determinism:** re-generating the voice does not produce a new
   take (Facts v4 builds #2/#3 had byte-identical narration timings
   for the same text). Pronunciation defects are fixed by rephrasing
   the script, never by rebuilding the voice.
4. **Stretched-tween residuals (same mechanism as v3, not rebuild
   triggers):** the builder stretches base tweens by the scene factor,
   so on long scenes heads/CTA/mascot pop late — Mysteries scene-3 head
   ~2.5 s into a 14.4 s scene; hook title ~0.6–1.9 s; payoff CTA/mascot
   ~2.2 s into the payoff scene (fully in before the end, confirmed on
   frame). The hook question is in the caption from 0.0 s. Facts
   scene-4 head "OVER HALF OF AMERICAN KIDS" stays during the DevEx
   sentence (image + caption carry it).
5. **"Forsaken" intelligibility:** small hears "Forsaken" on the clean
   narration but "Sagan" on the mix (weak /k/); the on-screen caption
   shows "Forsaken". On the listen list for a human ear check (35.48 s).
6. **Facts "robots"** low-confidence (0.29) at 7.28 s — listen list only.

## 8. Files changed (Phase 4B + pending pre-4B push)

Templates: `templates/formats/facts.html`, `templates/formats/mysteries.html`,
`templates/formats/game-discoveries.html` (pre-4B). Pipeline:
`pipeline/run.py`, `pipeline/second-shot.py` (new),
`rendering/build_video.py`, `quality-control/gate.py`,
`quality-control/check-visual-change.py` (new),
`quality-control/narration-lexicon.json`. Video pipelines:
`pipeline/roblox-facts-older-than-you-think-v4/`,
`pipeline/roblox-mystery-1x1x1x1-v4/` (claims/script/storyboard/
source-notes/image-map/heads/format/source-url/publish/gate/loudness/
attribution + run evidence), `pipeline/throw-food-for-animals/`
(pre-4B). Docs: `AGENTS.md` (§10), `audit-package/PHASE4B-REPORT.md`,
`assets/README.md`, `.gitignore` (added `assets/brand/`).

NOT pushed and NOT to be pushed: MP4s, images, the mascot PNG
(local-only), `videos/` compositions, `.cache-tmp/`, frame evidence
under `.cache-tmp/frames-v4-*/`.
