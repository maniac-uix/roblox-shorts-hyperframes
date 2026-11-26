# Storyboard — bloxburg-winter

- **Format:** game-discoveries — **Template:** `templates/formats/game-discoveries.html` — **Accent:** sky blue `#38BDF8`
- **Duration:** ~34 s estimated (83 words) — **Scenes:** 7 — **Sentences:** 8 — **Beats:** 8 (one per sentence; scene 6 holds two beats — the second beat is a second shot, applied at build stage with `pipeline/second-shot.py` after the build)
- **Breaks:** [1, 1, 1, 1, 1, 1, 2]
- **Hook:** "Players jumped 52 percent in one day — winter hit Bloxburg." (10 words, digit) — **Loop:** first/last share "bloxburg"

| # | Time | Visual (distinct, one per scene) | Motion | On-screen text | Caption |
|---|---|---|---|---|---|
| 1 | 0.0– | Snowy voxel town square at dusk, big decorated Christmas tree glowing, blocky characters in winter clothes, falling snow | tree lights twinkle, snow falls, characters walk in | +52% IN 24 HOURS. | Players jumped 52 percent in one day — winter hit Bloxburg. |
| 2 |  | Cozy voxel suburban street in winter, snow-covered roofs, chimneys smoking, a snowman on a lawn | smoke drifts, snow falls, hero waves | WELCOME TO BLOXBURG | Meet Welcome to Bloxburg, the town builder with 10 billion visits. |
| 3 |  | Snowy voxel town hall with a clock tower, winter garlands on the doors, frozen fountain in the plaza | garlands sway, snow falls, lamps flicker | WINTER IS HERE. | The Winter event started November 26, and runs to January 11. |
| 4 |  | Glowing outdoor ice rink at night, blocky skaters under bright spotlights, figure-skating show in the center | skaters glide, spotlights sweep, snow sparkles | SKATING SPOTLIGHT. | A new Skating Spotlight minigame leads the winter fun. |
| 5 |  | Chunky orange snowplow clearing a snowy street in a heavy snowstorm, cozy houses with lit windows | plow pushes snow, storm swirls, windows glow | SNOWSTORMS PAY EXTRA. | Snowstorms roll in, and plowing snow pays extra while they last. |
| 6 |  | Festive winter market at night, wooden stalls with striped awnings, glowing light-blue carriage, string lights | lights twinkle, carriage glows, shoppers stroll | THE WINTER MARKET. | The winter market is back, with new items and a glowing carriage. |
| 7 |  | Cozy voxel living room at night, fireplace, stockings, Christmas tree, snow outside the window; second shot: cheerful blocky friends playing in the snow together | fire flickers, snow falls outside; friends throw snowballs, snowman grows | SEND WINTER TO A FRIEND. | Winter is here, and Bloxburg is still the coziest town. Send this to a friend who plays Bloxburg today. |

## Transitions

- Scene 1 → 2: whip-pan on the voice beat ("Meet Welcome to Bloxburg")
- Scene 2 → 3: zoom-blur into the town square
- Scene 3 → 4: fade into the ice rink at night
- Scene 4 → 5: wipe to the snowstorm street
- Scene 5 → 6: crowd wipe to the winter market
- Scene 6 → 7: fade through the fireplace glow

## Heads (rendered titles — one per scene)

- Scene 6 holds two sentences with the single title-6 "SEND WINTER TO A FRIEND." ("winter" shared with sentence 7, "send"/"friend" shared with sentence 8). `beats.json` keeps per-sentence titres for the validator.

## Assets needed

- [ ] 8 generated images (voxel style, 1920×1280 WebP, game-discoveries sky-blue theme): hook-snow-town, bloxburg-street, winter-townhall, skating-spotlight, snowstorm-plow, winter-market, payoff-cozy, share-friends — all ORIGINAL voxel scenes; no Roblox logo, no Bloxburg character design reproduced (winter-tree-square was generated then replaced: too close to the hook tree image for the duplicate-image gate)
- [ ] Second shot at build stage: scene 6 beat 8 (share-friends) via `pipeline/second-shot.py` (switch at sentence 8 start, derived from the CURRENT build's transcript — §16, TTS is not deterministic across rebuilds)
- [ ] Music: "Basic Implosion" by Kevin MacLeod, CC BY 3.0 — attribution via `pipeline/music-attribution.py`
- [ ] Source note on scene 0 cites claims.json #2 (visits, Nov 26, 2026) — no hardcoded notes anywhere

## Notes

- Hook number is the LIVECOUNTS reading at 21:03 UTC Nov 26, 2026 (+52.0% in 24h, 35,086 playing, 24h peak 37,940, rank #36). The trend-pick brief's +92.4% was an earlier reading the same day and is NOT used — re-checked live before writing the script.
- "10 billion visits" = 10,175,151,407 (Roblox public API, Nov 26, 2026).
- Created Nov 4, 2014 → 12 years old in Nov 2026 (sentence 7, "Twelve years old" — verified via claim #1).
- Brand: `game-discoveries.html` carries the watermark (36 px) + mascot (240 px) + FOLLOW NOOBNOMORE — gate check 12 must PASS.
