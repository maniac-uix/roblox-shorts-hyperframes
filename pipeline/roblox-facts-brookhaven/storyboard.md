# Storyboard — roblox-facts-brookhaven (Facts, hook-test #3)

- **Format:** facts — **Template:** `templates/formats/facts.html` — **Accent:** teal `#2DD4BF`
- **Scenes:** 6 — **Sentences:** 9 — **Beats:** 9 (one per sentence; scenes 3, 4, 5 hold two sentences — each scene's single rendered title shares a content word with every sentence it covers; second shots give each sentence its own image)
- **Breaks:** [1, 1, 1, 2, 2, 2]
- **Hook:** "89.9 billion visits." (3 words, digit) — **Loop:** first/last share "89.9"/"billion"/"visits"
- **Second shots (applied with `pipeline/second-shot.py` after the build, before the draft render — times from the CURRENT build transcript, narration 33.53 s):** scene 3 → house-car-role at 14.58 s (S5 start, end 17.52); scene 4 → favorites at 22.30 s (S6 end — S7 start 22.96 would push the first image past 5.0 s, end 25.08); scene 5 → payoff-town at 29.70 s (S9 start, end 33.97). Each image span stays ≤ 5.0 s; no image is used in two scenes.

| # | Time | Visual (distinct, one per scene) | Motion | On-screen text | Caption |
|---|---|---|---|---|---|
| 1 | 0.0– | Voxel town avenue at golden sunset | title pop, 3-segment zoom cut | 89.9 BILLION VISITS. | 89.9 billion visits. |
| 2 |  | Aerial view of the whole voxel town | head slide-in, 3-segment zoom cut | MOST VISITED EVER. | That is Brookhaven RP, the most visited game in Roblox history. |
| 3 |  | Quiet voxel street in soft morning light | head slide-in, 3-segment zoom cut | SINCE APRIL 2020. | It launched in April 2020, and players never left. |
| 4 |  | Crowded voxel town square; second shot: voxel house with a red sports car | number pop, head slide-in, image crossfade, 3-segment zoom cut | A TOWN OF YOUR OWN. | Right now, over *500,000* players are exploring its town. In this town, you pick a house, a car, and a role. |
| 5 |  | Student, police officer and parent avatars; second shot: golden star over the town at dusk | head slide-in, image crossfade, 3-segment zoom cut | PICK YOUR ROLE. | Student, police officer, parent — pick any role you want. *31 million* players picked it as their favorite. |
| 6 |  | Purple voxel nightclub with DJ; second shot: night town from above with fireworks; mascot pop-in, CTA pulse | title pop, mascot pop, CTA pulse, image crossfade, 3-segment zoom cut | THE TOWN KEEPS GROWING. | And the town keeps growing — Club Brooks just opened its doors. 89.9 billion visits — and the town is still filling up. |

## Transitions

- Scene 1 → 2: slide-in from the right (template default)
- Scene 2 → 3: slide-in from the right
- Scene 3 → 4: slide-in from the right; inside scene 4, image crossfade crowd-town → house-car-role at sentence 5
- Scene 4 → 5: slide-in from the right; inside scene 5, image crossfade roles → favorites at sentence 7
- Scene 5 → 6: slide-in from the right; inside scene 6, image crossfade club-brooks → payoff-town at sentence 9; payoff stays on screen to the end

## Notes

- Source note on scene 0 cites claims.json #1 (89.9B visits, Roblox API Nov 27, 2026) — fades in at the figure's sentence, out at its end.
- Source note on scene 3 cites claims.json #4 (505,268 playing, Roblox API Nov 27, 2026) — fades in at the figure's sentence, out at its end.
- No hardcoded notes anywhere; the builder fails on a hardcoded source note.
- New images (generated in this environment, original voxel illustrations): all 9 — hero-brookhaven, town-overview, calendar-2020, crowd-town, house-car-role, roles, favorites, club-brooks, payoff-town.
