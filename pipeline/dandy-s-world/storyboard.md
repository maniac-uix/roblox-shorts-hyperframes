# Storyboard — dandy-s-world

- **Format:** game-discoveries — **Template:** `templates/formats/game-discoveries.html` — **Accent:** sky blue `#38BDF8`
- **Duration:** ~34 s measured (83 words) — **Scenes:** 7 — **Sentences:** 8 — **Beats:** 8 (one per sentence; scene 6 holds two beats — the second beat is a second shot, applied at build stage with `pipeline/second-shot.py` after the build)
- **Breaks:** [1, 1, 1, 1, 1, 1, 2]
- **Hook:** "8 billion visits, and this horror game just left alpha." (10 words, digit) — **Loop:** first/last share "game"

| # | Time | Visual (distinct, one per scene) | Motion | On-screen text | Caption |
|---|---|---|---|---|---|
| 1 | 0.0– | Voxel flower-shop entrance at dusk, big rainbow flower sign glowing over warm windows, a small voxel hero walking in | sign glow pulse, hero walk-in | 8 BILLION VISITS. | 8 billion visits, and this horror game just left alpha. |
| 2 |  | Giant blank voxel calendar page over a flower-shop street, confetti falling | calendar flip-in, confetti fall | DANDY'S WORLD | Meet Dandy's World: version 1.0 arrived November 20, 2026. |
| 3 |  | Voxel heroes working together on a glowing machine in a retro hallway, elevator doors behind them | machine lights chase, teammates pop-in | FINISH THE MACHINES. | Team up with friends, finish machines, and go deeper together. |
| 4 |  | Dark voxel hallway, shadowy distorted mascot silhouettes with glowing eyes in the distance, a small hero hiding behind a pillar | eyes blink, flashlight sweep | THE TWISTED HUNT YOU. | But Twisted mascots hunt you, and one wrong step ends the run. |
| 5 |  | Voxel science laboratory corridor with glowing experiment doors and a tall elevator shaft | doors light up in sequence, elevator rise | THE LABS ARE HERE. | Version 1.0 adds The Labs, a harder mode with 11 floors. |
| 6 |  | Crowded voxel lobby, heroes cheering, confetti, big glowing star | crowd bounce, star pulse | 800,000 AT ONCE. | Launch day drew almost 800,000 players at once. |
| 7 |  | Voxel trophy on a podium with a rising block chart arrow and flower petals; second shot: proud voxel hero with a rainbow flower flag, friends around, moonlit dusk | trophy spin, chart rise; flag wave, confetti | NUMBER ONE TRENDING. | Two years in alpha, 8 billion visits, now the top trending game. From noob to pro, try the number one game this week. |

## Transitions

- Scene 1 → 2: whip-pan on the voice beat ("Meet Dandy's World")
- Scene 2 → 3: zoom-blur into the machine room
- Scene 3 → 4: fade into the dark hallway
- Scene 4 → 5: wipe to the laboratory corridor
- Scene 5 → 6: crowd wipe to the launch-day lobby
- Scene 6 → 7: fade through the trophy pop

## Heads (rendered titles — one per scene)

- v5: scene 4 split into scenes 4 and 5, so each sentence has its own title (head-4 "THE LABS ARE HERE.", head-5 "800,000 AT ONCE."). Scene 6 still holds two sentences with the single title-6 "NUMBER ONE TRENDING." (trending / number, one — shared by both sentences). `beats.json` keeps per-sentence titres for the validator.

## Assets needed

- [ ] 8 generated images (voxel style, 1920×1280 WebP, game-discoveries sky-blue theme): gardenview-entrance-dark (v5 re-tone), title-calendar-v2 (v5 replacement, no white board), machine-team, twisted-hallway, labs-entrance, launch-crowd, trending-trophy, hero-payoff-dark (v5 re-tone) — all ORIGINAL voxel scenes; no Roblox logo, no Dandy or Toon character design reproduced
- [ ] Second shot at build stage: scene 6 beat 8 (hero-payoff-dark) via `pipeline/second-shot.py` (the old scene-4 second shot is gone — launch-crowd is its own scene 5 now)
- [ ] Music: "Basic Implosion" by Kevin MacLeod, CC BY 3.0 — attribution via `pipeline/music-attribution.py`
- [ ] Source note on scene 0 cites claims.json #2 (visits, Nov 23, 2026) — no hardcoded notes anywhere

## Notes

- The 130+ Lab Cards and the new Ambrosia currency (claims.json #7, verified) are NOT in the narration — word budget — but belong in the publish.md description.
- "Almost 800,000" = livecounts' recorded peak 797,183 on Nov 20, 2026 (claims.json #4; livecounts tracks the game since Sep 23, 2026 — "recorded peak", not proven all-time).
- Brand: `game-discoveries.html` carries the watermark (36 px) + mascot (240 px) + FOLLOW NOOBNOMORE since the v4 build — gate check 12 must PASS.
