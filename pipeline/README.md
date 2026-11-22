# pipeline/ — URL → video (Phase 3)

One public Roblox URL + one format in, one publishable MP4 out.

## The driver

```bash
python3 pipeline/run.py --url <public Roblox URL> --format facts \
    --slug my-video --stage storyboard   # STOP POINT (Step 4)
# ... owner reviews claims.json + script.txt + storyboard.md ...
python3 pipeline/run.py --slug my-video --stage gate      # after green light
python3 pipeline/run.py --slug my-video --stage deliver
```

Stages: `research → script → storyboard → build → draft → final →
normalize → gate → deliver`. The driver **stops after `storyboard`** and
waits for the owner's green light before voice and render — the voice is
generated inside `rendering/build_video.py` (built-in TTS, measured, never
cut) and the duration is derived from it.

## Work dir

`pipeline/<slug>/` holds the editorial artefacts for one video:

| File | What it is |
|---|---|
| `source-url.txt` | the public Roblox URL the video is built from |
| `format.txt` | the format (`facts`, `top5`, `mysteries`, …) |
| `claims.json` | every narration claim: claim, source URL, date, status (`verified` / `unverified` / `rephrased`) — see `claims-schema.json` |
| `script.txt` | the English script, 30–45 s estimated (words / 2.43 w/s) |
| `storyboard.md` | one row per scene: visual, motion, on-screen text, caption — the captions, concatenated, are exactly the script sentences in order |
| `top5-values.json` | Top 5 only: displayed + spoken values + announced total |
| `loudness.json` | loudness before/after normalisation |
| `gate.json` | the blocking gate report (all checks, measured values) |
| `attribution.txt` | the music attribution text for the video description |

## Rules the driver enforces

- **Research:** an `unverified` claim must not appear in the narration as
  fact — delete it or rephrase it (status `rephrased`, with the exact
  `narration_text`). No invented facts, ever.
- **Script:** English only, 30–45 s estimated. Over 45 s → the driver
  refuses; rewrite the script, never cut audio.
- **Storyboard:** ≥ 4 scenes, every scene has a visual, a motion and a
  caption; ≥ 2 distinct motions overall; captions match the script
  sentences in order (the scene breaks passed to the builder are exact).
- **Gate:** `quality-control/gate.py` runs every blocking check of Phase 3
  (format, qc.sh, 48 kHz / A/V gap / loudness, mix, fuzzy narration,
  sync ≤ 0.3 s, Top 5 sum). A FAIL blocks delivery — fix the lexicon and
  re-run, never override.
- **Listening:** the owner must listen to the voice before any manual
  publication. The gate report lists the low-confidence Whisper words
  (< 0.6) with timestamps — listen to those passages first.

## Music attribution

```bash
python3 pipeline/music-attribution.py   # prints the text for the description
```

The text comes from `config/factory.json` (`music` entry) — if the track,
author, licence or source is missing there, the script fails instead of
inventing a credit.
