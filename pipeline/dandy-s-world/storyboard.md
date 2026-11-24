# Storyboard — dandy-s-world

- **Format:** game-discoveries — **Template:** `templates/formats/game-discoveries.html` — **Accent:** sky blue `#38BDF8`
- **Duration:** ~36 s estimated (88 words / 2.43 wps) — **Scenes:** 6 — **Sentences:** 8 — **Beats:** 8 (one per sentence; scenes 4 and 5 hold two beats each — the second beat of each is a second shot, applied at build stage with `pipeline/second-shot.py` after the green light)
- **Breaks:** [1, 1, 1, 1, 2, 2]
- **Hook:** "8 billion visits, and this horror game just left alpha." (10 words, digit) — **Loop:** first/last share "game"

| # | Time | Visual (distinct, one per scene) | Motion | On-screen text | Caption |
|---|---|---|---|---|---|
| 1 | 0.0– | Voxel flower-shop entrance at dusk, big rainbow flower sign glowing over warm windows, a small voxel hero walking in | sign glow pulse, hero walk-in | 8 BILLION VISITS. | 8 billion visits, and this horror game just left alpha. |
| 2 |  | Giant blank voxel calendar page over a flower-shop street, confetti falling | calendar flip-in, confetti fall | DANDY'S WORLD | Meet Dandy's World: version 1.0 arrived November 20, 2026. |
| 3 |  | Voxel heroes working together on a glowing machine in a retro hallway, elevator doors behind them | machine lights chase, teammates pop-in | FINISH THE MACHINES. | Team up with friends, finish machines, and go deeper together. |
| 4 |  | Dark voxel hallway, shadowy distorted mascot silhouettes with glowing eyes in the distance, a small hero hiding behind a pillar | eyes blink, flashlight sweep | THE TWISTED HUNT YOU. | But Twisted mascots hunt you, and one wrong step ends the run. |
| 5 |  | Voxel science laboratory corridor with glowing experiment doors and a tall elevator shaft; second shot: crowded voxel lobby, heroes cheering, confetti, big glowing star | doors light up in sequence, elevator rise; crowd bounce, star pulse | THE LABS: 800,000 AT ONCE. | Version 1.0 adds The Labs, a harder mode with 11 floors. Launch day drew almost 800,000 players at once. |
| 6 |  | Voxel trophy on a podium with a rising block chart arrow and flower petals; second shot: proud voxel hero with a rainbow flower flag, friends around, sunrise | trophy spin, chart rise; flag wave, confetti | NUMBER ONE TRENDING. | Two years in alpha, 8 billion visits, now the top trending game. From noob to pro, try the number one game this week. |

## Transitions

- Scene 1 → 2: whip-pan on the voice beat ("Meet Dandy's World")
- Scene 2 → 3: zoom-blur into the machine room
- Scene 3 → 4: fade into the dark hallway
- Scene 4 → 5: wipe to the laboratory corridor
- Scene 5 → 6: fade through the trophy pop

## Heads (rendered titles — one per scene)

- Scenes 4 and 5 hold two sentences each, so the rendered head is a combined title sharing a content word with BOTH sentences (gate check 8 assigns one title per scene): head-4 "THE LABS: 800,000 AT ONCE." (labs / 800,000, once) and title-5 "NUMBER ONE TRENDING." (trending / number, one). `beats.json` keeps per-sentence titres ("THE LABS ARE HERE.", "800,000 AT ONCE.", "NUMBER ONE TRENDING.", "TRY THE NUMBER ONE GAME.") for the validator.

## Assets needed

- [ ] 8 generated images (voxel style, 1920×1280 WebP, game-discoveries sky-blue theme): gardenview-entrance, title-calendar, machine-team, twisted-hallway, labs-entrance, launch-crowd, trending-trophy, hero-payoff — all ORIGINAL voxel scenes; no Roblox logo, no Dandy or Toon character design reproduced
- [ ] Second shots at build stage: scene 4 beat 6 (launch-crowd), scene 5 beat 8 (hero-payoff) via `pipeline/second-shot.py`
- [ ] Music: "Basic Implosion" by Kevin MacLeod, CC BY 3.0 — attribution via `pipeline/music-attribution.py`
- [ ] Source note on scene 0 cites claims.json #2 (visits, Nov 23, 2026) — no hardcoded notes anywhere

## Notes

- The 130+ Lab Cards and the new Ambrosia currency (claims.json #7, verified) are NOT in the narration — word budget — but belong in the publish.md description.
- "Almost 800,000" = livecounts' recorded peak 797,183 on Nov 20, 2026 (claims.json #4; livecounts tracks the game since Sep 23, 2026 — "recorded peak", not proven all-time).
- Brand check: `game-discoveries.html` carries no watermark/mascot elements (brand lives only in facts.html/mysteries.html) — gate check 12 is expected to record N/A at build time; flag if it records FAIL.
