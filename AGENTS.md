# AGENTS.md — ROBLOX VIDEO FACTORY (permanent rules)

These rules outlive any single video. Read them before changing anything in
this project. The owner (Amine) outranks them; a new instruction from him
replaces the rule it contradicts, and the replacement must be written here.

## 1. Language

- **Every video is in English** — voice-over, on-screen text, metadata. Never
  French in a video.
- Conversation with the owner: French or English, both fine.

## 2. Editorial — Roblox only, facts only

- Content is exclusively about Roblox: Mysteries, Facts, Top 5, Hidden
  Secrets, Game Discoveries, Updates, Stories.
- **Never invent information** about games, creators, dates, numbers or
  features. Every claim comes from a verified public source; the source URL
  and what it actually says go in `research/` and in the video's
  `metadata.json`.
- Two numbers that measure different things (e.g. estimated retail sales vs
  a bookings forecast) are never compared without labelling both measures.
- No generic, repetitive content. Every video needs an original hook, a
  structured narration and a relevant conclusion.
- Respect usage rights for images, music, brands and gameplay footage. Never
  assume a resource is freely reusable just because it is publicly
  accessible. Prefer official art (e.g. Roblox Newsroom) with credit, or
  images generated in this environment. Record the licence/credit of every
  asset in `assets/README.md` and in `metadata.json`.

## 3. HyperFrames contract

- Read the installed HyperFrames skills before writing or editing a
  composition: `/hyperframes` first, then `/hyperframes-cli`. The skill holds
  the render contract and the work loop; the scaffold `AGENTS.md` in a
  HyperFrames project says the same.
- Every timed element: `class="clip"`, `data-start`, `data-duration`.
- One paused root timeline per composition, registered on
  `window.__timelines["<data-composition-id>"]`.
- No `Date.now()`, no unseeded `Math.random()`, no network fetches, no
  timers, no `repeat: -1`. Everything visible is a function of timeline time.
- Never tween `display`, `visibility` or `autoAlpha` on a `.clip`; animate a
  child. No CSS `transform` on an element GSAP transforms.
- Only the bundled fonts resolve by name; Montserrat is loaded via
  `@font-face` from `assets/fonts/Montserrat-Variable.woff2` (SIL OFL).
- Asset paths are `assets/...` (no leading `/`).
- After every edit: `npx hyperframes check` (fix all errors), then
  `npx hyperframes snapshot` and **look at the frames yourself** before
  rendering. A passing check does not show how it looks.
- Templates live in `templates/`. Never hand-build a named effect,
  transition or caption style without checking the HyperFrames registry
  first (`/hyperframes-registry`).

## 4. Visual standards (factory)

- 1080 × 1920, 30 fps, H.264 MP4. Production target 30–45 s (target 35 s)
  — but the duration of each video is **derived from its narration** (see
  §5), never forced to hit the target.
- Base theme: deep navy `#0B1026`, teal `#2DD4BF`, Montserrat. One accent per
  format (see `config/factory.json` — `style.accentsByFormat`).
- Key text inside the safe zone: x 120–888, y 288–1248. Captions at the
  bottom of the band. Only texture/decoration outside it.
- Titles ≥ 110 px, white with dark outline + shadow, max 2 lines. Subtitles
  ≥ 70 px, 2–3 words at a time, current word highlighted.
- Motion in every scene: something draws, pops, travels or parallaxes every
  1–1.5 s. A zoomed still card is a failure, however clean its typography.
- A progress bar replaces any "1/5" counter. No black first frame: frame 0
  is the thumbnail and the hook.
- Phase 2 layout (all three format templates): pill + progress bar at the
  top, title, an image card (840 × 680 px, rounded, Ken Burns
  zoom/pan) that fills the middle band — no empty central area. Captions
  sit at y1520, below the image zone; CTA zone at y1760. (v3, 22 Nov
  2026: image enlarged from 440–460 px and captions lowered from y1300
  after the owner's v2 verdict — images too small with a big dark void
  below on phone.) The last scene never slides out:
  the payoff + CTA stay on screen to the end. Scene transitions are
  slide-in from the right / slide-out to the left on `.scene-inner`.
- Emphasis: `*word*` in a script marks a word for on-screen highlight
  (`<span class="hl">` in captions, yellow). The builder strips the
  asterisks before TTS, so the spoken script is unchanged.
- Images: original illustrations generated in this environment, or
  permitted assets with a recorded licence. Every image is registered in
  `assets/README.md` with source, licence and scene, and in the video's
  `metadata.json`. `build_video.py --image-map` maps scene index ->
  image file and rewrites `<img data-img-scene="N">` src to a local copy
  inside the video folder.

## 5. Audio standards

- Voice-over: built-in Muse TTS only (`/opt/hatch/bin/tts`, voice Helio).
  No paid TTS, no HeyGen without the owner's explicit approval.
- Music: royalty-free only, with attribution (e.g. Kevin MacLeod, CC BY).
  Level −18 dB, ducked under the voice. Phase 2 default bed: "Basic
  Implosion" by Kevin MacLeod, CC BY 3.0 (see `config/factory.json` —
  `music`), mixed at volume 0.04 (lowered from 0.08 on 22 Nov 2026: at
  0.08 the facts draft measured only 3.0 dB voice-above-music, gate
  requires ≥ 6 dB). The bed ends at last_speech + 0.3 s
  (0.3 s fade-out) so the end margin stays true silence and the
  final-silence QC gate still works. With a bed, the mid-silence QC check
  is blind (the bed fills the gaps) — the voice-above-music gate
  (`quality-control/check-mix.py`, voice ≥ 6 dB above the bed in every
  speech window) replaces it. The gate compares, per caption window, the
  mix (voice+bed) against the bed alone at the same time offset — never
  speech windows against inter-sentence gaps: gap edges carry voice
  tails (Whisper timings are ±0.2 s off) and bed transients, so that
  comparison failed twice on artefacts while the voice was 11+ dB above
  the bed (fixed 22 Nov 2026).
- **Duration is derived from the narration, never the reverse** (corrected
  21 Nov 2026 — Test 001 diagnosis, see `docs/DIAGNOSIS-audio-test1.md`).
  Build with `rendering/build_video.py`: estimate from word count before
  generating the voice; if the estimate exceeds the target, **rewrite the
  script** — never cut audio, never pad a short narration with silence to
  reach a pre-set video length. After TTS, measure the real duration and
  the real end of speech, then `video = max(narration + 0.3, last_speech
  + end_margin)` with end margin 1.0 s (config `durationPolicy`).
- **Audio container gates (v3.1b, 22 Nov 2026 — blocking, `quality-control/check-av.py`):**
  audio sample rate **== 48000 Hz exactly** and **|audio duration − video
  duration| ≤ 0.02 s**, plus the loudness gate (−14 ± 0.5 LUFS, TP ≤ −1).
  The v3.1 files failed both: loudnorm re-encoded the audio at **96000 Hz**
  (no explicit sample rate in the chain) and left the audio 0.06–0.10 s
  longer than the video (AAC padding; the old qc.sh gate was only ±0.1 s).
  Fix: `aresample=48000` in the normalize chain (now forced there) and
  trim the audio to the video duration (`atrim`); the video stream is
  copied untouched and proven byte-identical (raw-stream SHA-256).
  **−14 LUFS integrated, true peak ≤ −1 dBTP** (two-pass `loudnorm`,
  `quality-control/normalize-loudness.py`). Normalise with a TP target of
  −1.5 — loudnorm's dynamic limiter overshoots and the first attempt at
  TP −1 measured −0.79/−0.83/−0.91. The gate is verified on the DELIVERED
  file (|integrated +14| ≤ 0.5 LU, TP ≤ −1.0); report LUFS/LRA/TP before
  and after. A second pass is allowed when the first lands outside the
  ±0.5 LU tolerance (top5 v3.1 needed one).
- **Hard gates, learned the hard way:** final audio duration must equal
  video duration (≤ 0.02 s — v3.1b, see above) — as a *container* check only, never satisfied by
  padding; the **final silence must sit within [margin − 0.5 s, margin
  + 0.75 s]** and no mid-narration silence may exceed 1.0 s (`qc.sh`
  checks both); the voice must sit clearly above the music in every
  speech window (a global loudness number alone proves nothing — loudness
  is set by the loudest element, usually the music) — for normalised
  files the mix gate compares like-for-like with
  `check-mix.py --bed-gain-db` = the loudness gain, otherwise the
  normalisation gain inflates the measurement (facts v3.1 read 21.2 dB
  uncorrected, 10.9 dB corrected); verify the *content* of the
  narration — transcribe the **final MP4** (audio extracted from the
  delivered file) with `quality-control/check-narration-fuzzy.py`
  (Whisper small) and compare with the script. A passing
  `qc.sh` alone never proves the narration is complete. A rebuild gets a
  **new filename** — never overwrite the path of a delivered file and
  re-send it.
- **Narration comparison is FUZZY, not word-for-word** (v3.1, 22 Nov
  2026 — strict comparison FAILed on Whisper respellings only:
  DynaBlocks→"Dynoblocks", Robux→"robots", Brainrot→"brain rot",
  Shedletsky→"shed letzge", sixteen→"16"). `narration_lexicon.py` +
  `narration-lexicon.json`: proper-noun lexicon, number forms, difflib
  ratio ≥ 0.80. **The automatic verdict is authoritative: a FAIL blocks
  delivery, no manual override.** If a FAIL is a false positive, add the
  term to the lexicon and re-run. The check also verifies the final
  sentence is complete and ends before the final silence starts, and
  lists low-confidence words (< 0.6) with timestamps as a listening aid
  (transcription ≠ listening — pronunciation still needs human ears).
- **Caption/voice sync gate ≤ 0.3 s** (v3.1): `quality-control/check-sync.py`
  compares each caption's appearance timestamps with the Whisper word
  timestamps of the corresponding words; report max and mean gap. Use
  **small for word identity, tiny for word timing** — on loudness-normalised
  mixes, small's word STARTs run 0.3–0.7 s early for sentence-initial words
  (dynamic gain boosts pre-speech breaths; small stretches the word back
  over them), tiny's starts match the build transcript within 0.04 s.
- **Captions are synchronised with the narration by FUZZY alignment**
  (`quality-control/caption_timing.py`, shared by the builder and
  `rendering/fix-caption-timing.py`) — NEVER by word count. Count-based
  slicing drifted whenever Whisper's word count differed from the
  script's ("Brainrot" heard as "brain rod") and put later captions up to
  2.08 s before their words (top5/mysteries v3). Caption start = first
  aligned word's start, end = last aligned word's end. Scenes still start
  at the previous sentence's end (during the genuine TTS inter-sentence
  pause); only the caption moves to its first word.
- **Technical reports per video** (`audit-package/technical-reports/`):
  ffprobe, sha256, blackframes (pic_th=0.98), silence, volumedetect,
  loudness before/after, mix per window, narration comparison, caption
  sync, low-confidence words, frames vs previous version, and a
  summary.json with PASS/FAIL + measured values per check. **No value may
  be asserted without a proof file.**
- **Reports are technical only (22 Nov 2026, owner's correction):** a
  report states measured facts, results and limits — never the history of
  the conversation (no back-and-forth, no blockage saga, no who-asked-what).
  One phase = one report file; the report is written once, complete, and
  amended only when the measured state actually changes.
- **Source notes come only from claims.json (22 Nov 2026, owner's
  correction — the age-check test video shipped with false attributions):**
  Phase 2 `facts.html` carried two hardcoded notes ("Roblox Corp. via
  Wikipedia — Feb 2025" and "via The Verge — Apr 2020") that the builder
  rendered on the wrong scenes of a video whose only source was the Roblox
  Nov 18, 2025 announcement. `pipeline/run.py` validates
  `pipeline/<slug>/source-notes.json`: every note must cite a verified
  claim (its date rendered "Mon D, YYYY" or its source domain) and passes
  it to the builder as `--source-notes`; `build_video.py` injects the note
  into its scene and **FAILS the build if the template contains any
  hardcoded source note** (checked before the voice is generated).
- **Pronunciation-sensitive words are never legitimised by variants
  (22 Nov 2026, owner's correction):** adding "sucky"/"study" as valid
  variants of "selfie" made the narration gate pass while small heard
  "sucky" (prob 0.86), base "study" (0.20) and tiny "set" (0.07) — the
  TTS voice itself is unclear on that word. The lexicon's
  `pronunciation_sensitive` list marks such words; a sensitive word not
  heard EXACTLY is missing → the narration check FAILs, no override, and
  the word is recorded in the gate report's `listen_words` (heard form +
  timestamp + prob) for the owner to judge by ear.
- **Duration is validated on the MEASURED narration (22 Nov 2026,
  owner's correction):** measured speech rate varies 2.07–3.32 wps across
  videos, so the word-count estimate (44.0 s estimated vs 31.6 s measured
  on the age-check video) is a WARNING only. The builder REFUSEs when the
  measured video duration is outside 30–45 s — rewrite the script, never
  cut audio.
- **Caption re-anchoring is automated (22 Nov 2026):** a Whisper word
  whose span contains a silence ≥ 0.3 s was stretched back across a pause
  ("So" timed 28.76 while the real pause ran 28.82–29.40) — the builder
  moves such a word's start to the end of the silence before deriving the
  captions (`reanchor_smears` in `build_video.py`, corrections recorded
  in `metadata.json` as `captionReanchoring`). No manual caption fix.
  The same rule applies to the SYNC CHECK's own tiny timings on the
  final MP4 (`check-sync.py`, silences from the clean narration — the
  mix's bed fills the pauses): tiny smeared "Chat" to 25.86 inside the
  25.47–26.28 pause, failing the sync gate at 0.46 s on a correct
  caption; after correction the gap is 0.04 s. The rule only moves a
  word's start to a silence end, so it can only fix smear gaps — it
  cannot hide a genuinely late caption. Corrections are recorded in the
  sync report (`timing_corrections`).
- **Normalize trims and self-verifies (22 Nov 2026):** `normalize-loudness.py`
  appends `atrim` to the video duration after loudnorm+aresample and
  verifies |audio − video| ≤ 0.02 s on the output, raising if exceeded.
  No manual trim step exists anywhere in the pipeline.

## 6. Cloud limits (non-negotiable)

- **Never use `/tmp` for large temp files** — it is a 512 MB tmpfs and
  renders fail there. Always render through `rendering/render.sh`, which
  sets `TMPDIR` and `HYPERFRAMES_EXTRACT_CACHE_DIR` inside the workspace.
- Check free memory before every render (≥ 500 MB free required); never run
  two heavy renders at the same time (lock file in `.cache-tmp/`).
- Always render **draft first**, QC it, then render final. Never deliver a
  file that did not pass `quality-control/qc.sh`.
- All project files live in `~/workspace/hyperframes-roblox-shorts/`.
  Nothing in `/tmp`, nothing on the owner's phone.
- Do not modify `roblox-url-filter-toggle` — that repository is out of
  scope for this project.

## 7. Costs

- **Zero paid services.** Nothing that needs payment is connected. Flag any
  feature that would need payment to the owner *before* integrating it.
- Google Drive archiving is planned but not connected (checked 21 Nov 2026:
  `not_connected`). Do not claim a file is archived on Drive until the
  upload is confirmed.

## 8. Delivery

- Deliver the MP4 + a short summary. No pre-selected choice cards/widgets
  after a video — just the file and the text.
- Verify the rendered result yourself (frames at full size and at phone
  size, centering, charts, font hierarchy, text overlap) before delivering.
  The owner does not QC each video.
- No automated production from URLs and no automatic publishing in Phase 1.
  Both need the owner's explicit go-ahead in a later phase.

## 9. Phase 3 — repository + URL → video pipeline (22 Nov 2026)

- The factory lives in the public repo `maniac-uix/roblox-shorts-hyperframes`
  (code, configs, templates, scripts, quality-control — text only; MP4s,
  binaries, caches and audit evidence are git-ignored and fetched or
  generated locally, see `scripts/fetch-assets.sh`).
- Pipeline: `pipeline/run.py` — one public Roblox URL + one format in.
  Research produces `pipeline/<slug>/claims.json` (claim, source URL, date,
  status: verified / unverified / rephrased) — this IS the research record
  for Phase 3 videos (`research/` keeps the brief template and the Phase 2
  briefs). Unverified claims are excluded from the narration. Script:
  English, 30–45 s estimated. Storyboard: ≥ 4 scenes, ≥ 2 distinct
  motions, captions exactly the script sentences in order.
- Templates: `templates/formats/game-discoveries.html` (sky-blue #38BDF8, copy of facts.html, 6 scenes; CTA is a `<p>` so `--heads` can set it) — first used for throw-food-for-animals (23 Nov 2026).
- **Stop point (Step 4): after script + claims.json + storyboard, STOP and
  wait for the owner's green light before voice and final render.**
  No voice, no render, no delivery before that green light.
- The blocking gate is `quality-control/gate.py` (all Phase 3 checks:
  format, qc.sh, 48 kHz / A/V gap ≤ 0.02 s / loudness, mix ≥ 6 dB, fuzzy
  narration, sync ≤ 0.3 s, Top 5 sum). A FAIL blocks delivery, no manual
  override. The music attribution text comes from
  `pipeline/music-attribution.py` (config `music` entry — never invented).
- No automatic publishing, ever. The owner listens to the voice before
  any manual publication.

## 10. Phase 4B — Brand and Retention (v4, 23 Nov 2026)

Phase 4B re-renders Facts and Mysteries with brand and retention rules.
**It overrides the Phase 3 stop point: there is no stop point in Phase 4B
— the gate decides.** Everything else in §9 still applies.

- **Hook (blocking, in the script stage of `pipeline/run.py`):** the first
  sentence must be ≤ 12 words AND contain a digit, a question mark, or a
  spelled-out number word (one..twenty, thirty…ninety, hundred, thousand,
  million, billion). "Surprising statement" cannot be checked
  automatically, so the enforceable rule is digit-or-question; a hook that
  is only a surprising statement must be rephrased with a number or a
  question. The first-scene title echoes the hook. Dates and "counted
  in…" move later in the script.
- **Loop (report-only, `pipeline/run.py`):** the last sentence must connect
  back to the first — checked as a shared content word between first and
  last sentence, excluding stopwords; printed as `LOOP: PASS/WARNING`.
  Never blocks.
- **Rhythm (4 s rule):** no scene stays more than 4 s without a visible
  change. Implemented as a 3-segment zoom cut per scene (jump cuts at 1/3
  and 2/3 of the scene) in the facts/mysteries templates, plus slide
  transitions, caption swaps, source-note fades and title pops — max gap
  without a discrete change ≈ scene length / 3. Long scenes are NOT split
  into extra scenes; existing images only, no new image generation.
- **Brand (templates, not per video):** persistent "NoobNoMore" watermark
  text in the safe zone (top-right, right edge 1080−150 px, top 150 px,
  30 px Montserrat 800, turquoise #1FD1C1, opacity 0.85) in
  `templates/formats/facts.html` and `mysteries.html`. Last scene: the
  NoobNoMore mascot (240×240 px, bottom-left of the image card area) with
  CTA **"FOLLOW NOOBNOMORE"** (replaces "FOLLOW FOR MORE"). Brand palette:
  turquoise #1FD1C1 / amber #FFB020 / purple #7A4DF0; format accents
  (Facts teal, Mysteries purple) stay for scene design. Mascot asset:
  `assets/brand/noobnomore-mascot-transparent.png` (copy of the channel
  mascot, SHA-256 `58bfc921…013b6b`) — **local-only, git-ignored, never
  pushed**; `build_video.py` copies it into each video folder at build
  time and warns if a template references a missing brand asset.
- **Visual-change gate control (`quality-control/check-visual-change.py`,
  gate check 7):** ffmpeg fps=2 frame-difference, threshold 0.01,
  max-gap limit 4.0 s. **Recorded as a non-blocking warning, never
  PASS/FAIL.** Calibration on the 5 existing videos (23 Nov 2026):
  full-fps scdet fails ALL good videos at every threshold (T=0.05–0.15,
  max gaps 10–20 s — factory motion is smooth slides/zooms, not hard
  cuts); frame-diff fps=2 T=0.01 gives facts 4.50 s / top5 4.00 s /
  mystery 3.50 s / age-check 3.50 s / throw-food 4.00 s — even the best
  instrument leaves facts above 4.0 s and two videos exactly on the
  limit, so blocking would fail good videos. The 4.0 s limit itself is
  unachievable for these videos (slow scenes + the intentionally static
  final payoff/CTA scene). A frozen-frame and a black clip both measure
  max gap 10.00 s / 0 changes, so the instrument does separate dead video
  from live video — it stays a recorded warning. v4 drafts measure 2.0 s
  (Facts 55 changes, Mysteries 46–51 changes) thanks to the 3-segment
  zoom.
- **Final silence (target 0.5–0.7 s measured):** `run.py --end-margin`
  default is **0.85** (was 0.6). Loudnorm's gain (+9.5–12.6 dB) lifts the
  music-bed fade tail above the silence threshold and shrinks the
  measured final silence by 0.11–0.26 s vs the raw render — the extra
  0.25 s of margin compensates. **The gate threshold is unchanged
  (0.5–1.75 s)** and the builder never trims narration.
- **Source-note fade-out (convention + `build_video.py`):** a source note
  belongs to the FIRST sentence of its scene (the figure it sources) and
  fades out 0.2 s after that sentence's caption ends, so it never lingers
  into a sentence it does not source. The storyboard must arrange each
  figure sentence to start its scene.
- **Second shot (`pipeline/second-shot.py`):** parameterized crossfade to
  a second image mid-scene (`--slug --scene --at --end --image <path>
  --reason`); records in `metadata.json` as `secondShots`. Used when one
  scene holds two sentences with different visuals (Facts v4 scene 4:
  kids figure, then DevEx sentence).
- **TTS determinism:** `/opt/hatch/bin/tts` is effectively deterministic
  per script text — rebuilding the voice does not produce a new take
  (two consecutive rebuilds of Facts v4 gave byte-identical narration
  timings). A pronunciation defect is fixed by **rephrasing the script**,
  never by re-generating the voice. A rephrase that changes a sentence
  onset is the fix for a misheard word (Facts v4: "As of February 2025"
  heard as "says" by all three models → "In February 2025"; Mysteries
  v4: sentence-initial "The" heard as "his" → "It first appeared…").
- **Slowly-spelled proper nouns:** a token like `1x1x1x1` in
  sentence-initial position is spelled out slowly by the TTS (~2.2 s,
  "one x one x…"); Whisper models latch onto different parts of it, so
  both the build caption timing and the sync check go wrong (Mysteries
  v4 gate run #1: caption 1.8 s late vs true speech onset, sync gap
  −0.78 s). Never start a sentence with a slowly-spelled token — start
  with a normal word instead (Mysteries v4: "1x1x1x1 was a test
  account…" → "It was a test account…").
- **Lexicon rule (reminder):** a variant is added only for a Whisper
  respelling of a correctly-spoken word — small must hear the word
  EXACTLY on the clean narration (Mysteries v4: "sagan"/"for sagan" →
  "forsaken", same class as the existing "saken"/"for saken"; small
  hears "Forsaken" on the clean narration, the /k/→/g/ voicing confusion
  appears only under the music bed). A word the voice itself misrenders
  ("selfie" → "sucky") is never legitimised by a variant — rephrase the
  script instead.
- **Known latent bug (not fixed):** HyperFrames check-cache trap —
  `build_video.py` judges `npx hyperframes check` only by the "report
  saved to" line, so a cached ok:true report reads as FAILED; workaround
  is to delete `videos/<slug>/.hyperframes/cache/check.json` before the
  run.
