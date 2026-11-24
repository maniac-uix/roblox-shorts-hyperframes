# Storyboard — roblox-facts-older-than-you-think-v5 (Phase 4C rebuild)

- **Format:** facts — **Template:** `templates/formats/facts.html` — **Accent:** teal `#2DD4BF`
- **Scenes:** 6 — **Sentences:** 11 — **Beats:** 11 (one per sentence; scenes 1, 3, 4, 5 hold two sentences, scene 5 holds three — each scene's single rendered title shares a content word with every sentence it covers; second shots give each sentence its own image)
- **Breaks:** [1, 2, 1, 2, 2, 3]
- **Hook:** "Did you know Roblox is 22 years old?" (8 words, digit + number-word) — **Loop:** first/last share "22"/"years"
- **Second shots (applied with `pipeline/second-shot.py` after the build, before the draft render):** scene 1 → robots-blocks at the end of sentence 2 (4.88 s); scene 3 → quote-2020 at the end of sentence 5 (17.12 s); scene 4 → creator at the start of sentence 8 (24.22 s); scene 5 → more-than-a-game at the start of sentence 10 (31.60 s) and payoff-22 at the end of sentence 10 (33.26 s). Scene 5 holds THREE images: its window is 9.21 s (28.02–37.69, scenes start at the previous sentence's end), so two images cannot both stay under the 5.0 s gate limit — the third shot is why `second-shot.py` supports suffix "c". Each image span stays ≤ 5.0 s; no image is used in two scenes.

| # | Time | Visual (distinct, one per scene) | Motion | On-screen text | Caption |
|---|---|---|---|---|---|
| 1 | 0.0– | Blocky voxel city at sunrise | title pop, 3-segment zoom cut | 22 YEARS OLD. | Did you know Roblox is 22 years old? |
| 2 |  | Blocky robot stacking toy blocks; second shot: voxel robot building a tower of colorful blocks on a workbench | number pop, head slide-in, image crossfade, 3-segment zoom cut | STARTED IN 2004 — ROBOTS + BLOCKS | It started in 2004, under the name DynaBlocks. Roblox itself means robots plus blocks. |
| 3 |  | Voxel rocket blasting off at night, orange flame, starry sky | head slide-in, flame glow, 3-segment zoom cut | LAUNCHED SEPTEMBER 1, 2006 | It launched to the public on September 1, 2006. |
| 4 |  | Huge crowd of blocky characters; second shot: voxel classroom, teacher pointing at a 2020 timeline chart | number pop, source note fade-in/out, image crossfade, 3-segment zoom cut | 85 MILLION PLAYERS — ROBLOX SAID IT | In February 2025, over *85 million* players log in daily. Back in 2020, this is what Roblox said. |
| 5 |  | Four diverse voxel kids on a couch with tablets/phones; second shot at sentence 8: blocky creator at a glowing computer | number pop, source note fade-in/out, image crossfade, 3-segment zoom cut | KIDS PLAY — CREATORS EARN REAL MONEY | *Over half* of American kids under sixteen played it. And since 2013, creators can turn their Robux into *real money*. |
| 6 |  | Three diverse voxel builders on a glowing platform; second shot at sentence 11: three builders raising a giant golden 22 monument at dusk; mascot pop-in, CTA pulse | title pop, mascot pop, CTA pulse, image crossfade, 3-segment zoom cut | PLAYERS BUILD THE GAME. | So the players build the games, and they get paid for it. So Roblox is not just a game. 22 years later, it is still built by its own players. |

## Transitions

- Scene 1 → 2: slide-in from the right (template default)
- Scene 2 → 3: slide-in from the right
- Scene 3 → 4: slide-in from the right; inside scene 4, image crossfade scale → quote-2020 at sentence 6
- Scene 4 → 5: slide-in from the right; inside scene 5, image crossfade kids → creator at sentence 8
- Scene 5 → 6: slide-in from the right; inside scene 6, image crossfade platform → payoff-22 at sentence 11; payoff stays on screen to the end

## Notes

- Source note on scene 3 cites claims.json #4 (85.3M DAU, Feb 2025) — fades in at the figure's sentence, out at its end.
- Source note on scene 4 cites claims.json #5 (kids claim, Apr 2020) — fades in at the figure's sentence, out at its end.
- No hardcoded notes anywhere; the builder fails on a hardcoded source note.
- New images (v5, generated in this environment, original voxel illustrations): robots-blocks (scene 1, second shot), launch-2006 (scene 2 — rocket, replaces the origin reuse), quote-2020 (scene 3, second shot), payoff-22 (scene 5, second shot). The crowd version of launch-2006 is kept aside as launch-2006-crowd-unused.webp (too close by histogram to scale.webp, 0.188).
- Facts v4 defects fixed: origin.webp no longer reused across scenes; every sentence has its own image (second shots inside multi-sentence scenes); every scene title shares a content word with each of its sentences; first frame has title + image at t=0 (template 4C rule); watermark 36 px (template).
