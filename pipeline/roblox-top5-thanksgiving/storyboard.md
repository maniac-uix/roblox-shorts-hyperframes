# Storyboard — roblox-top5-thanksgiving

- **Format:** top5 — **Template:** `templates/formats/top5.html` — **Accent:** amber `#F59E0B`
- **Duration:** ~33.5 s estimated (87 words) — **Scenes:** 7 — **Sentences:** 8 — **Beats:** 8 (one per sentence; scene 6 holds 2 beats, second shot at the share sentence)
- **Breaks:** [1, 1, 1, 1, 1, 1, 2]
- **Hook:** "Five Thanksgiving games, over 75 billion visits between them." (9 words, digit 75 + number-word Five — concrete-hook test #1 of 3) — **Loop:** WARNING expected (first/last share no content word; the link is the countdown itself)
- **Ranking criterion:** total visits, Roblox public games API, read Nov 25, 2026, 21:52 UTC (Grow a Garden 36.0B, 99 Nights 30.7B, Fisch 5.2B, Pet Simulator 99 2.7B, NFL Universe Football 1.0B; sum 75.6B, announced "over 75 billion")

| # | Time | Visual (distinct, one per scene) | Motion | On-screen text | Caption |
|---|---|---|---|---|---|
| 1 | 0.0–3.5 | Voxel Thanksgiving feast table at dusk, roast turkey centerpiece, five glowing game portals behind it, autumn leaves falling | leaves fall, portal glow pulse | 75 BILLION VISITS. | Five Thanksgiving games, over 75 billion visits between them. |
| 2 | 3.5–8.1 | Voxel American football stadium in an autumn park, blocky players chasing a turkey across the field, orange leaves | players run, turkey dodges | NFL UNIVERSE FOOTBALL | Number five, NFL Universe Football, one billion visits, turkey rush for Thanksgiving. |
| 3 | 8.1–12.7 | Voxel island with a giant turkey landing in the center, blocky pets with nets running toward it, maple trees | turkey lands, pets rush in | PET SIMULATOR 99 | Number four, Pet Simulator 99, almost three billion visits, giant turkey hunt. |
| 4 | 12.7–17.3 | Voxel fishing boat on a calm autumn sea, blocky angler reeling in a turkey-shaped catch, leaves on the water | rod bends, ripples spread | FISCH | Number three, Fisch, over five billion visits, Fischgiving starts with fourteen turkeys. |
| 5 | 17.3–21.9 | Voxel forest camp at night, campfire glow, long dinner table with a crock pot, blocky guests arriving | fire flickers, guests walk in | 99 NIGHTS IN THE FOREST | Number two, 99 Nights, almost 31 billion visits, Thanksgiving challenge now live. |
| 6 | 21.9–26.5 | Voxel garden in autumn harvest, giant turkey pet among pumpkin and corn rows, blocky gardener with a basket | turkey struts, leaves drift | GROW A GARDEN | And number one, Grow a Garden, 36 billion visits, turkey hunt live. |
| 7 | 26.5–33.5 | Voxel hero with turquoise cape at a Thanksgiving feast table, confetti falling, then two voxel friends sharing a game on a phone (second shot) | confetti fall, hero pop-in, friends lean in | SEND THESE GAMES. | Five Thanksgiving games, over 75 billion visits in total. Send this to a friend who plays Roblox today. |

## Transitions

- Scene 1 → 2: slide to the football stadium on the voice beat ("Number five")
- Scene 2 → 3: zoom-blur into the turkey landing
- Scene 3 → 4: wipe to the fishing boat
- Scene 4 → 5: slide to the forest camp
- Scene 5 → 6: wipe to the garden
- Scene 6 → 7: fade through the hero pop
- Scene 7: second shot at the share sentence ("Send this to a friend…") — payoff feast crossfades to the two friends sharing a game

## Heads (rendered titles — one per scene)

- title-0 "75 BILLION VISITS.", sub-0 "Five games, one Thanksgiving." — game-1 "NFL UNIVERSE FOOTBALL", game-2 "PET SIMULATOR 99", game-3 "FISCH", game-4 "99 NIGHTS IN THE FOREST", game-5 "GROW A GARDEN" — title-6 "SEND THESE GAMES." + sub-6 "Over 75 billion visits in total." (see `heads.json`). Title-6 shares "games" with the total sentence and "send" with the share sentence (2 lines: "SEND THESE" / "GAMES.").
- Visits pills from `top5-values.json` (scene order #5..#1): 1.0B / 2.7B / 5.2B / 30.7B / 36.0B VISITS.

## Assets needed

- [ ] 8 generated images (voxel style, 1920×1280 WebP, top5 amber `#F59E0B` theme): hook-feast, nfl-turkey-rush, ps99-turkey-hunt, fisch-fischgiving, nights-thanksgiving, garden-turkey-hunt, payoff-feast, share-friends — all ORIGINAL voxel scenes; no Roblox logo, no Roblox characters, no game footage
- [ ] Music: "Basic Implosion" by Kevin MacLeod, CC BY 3.0 — attribution via `pipeline/music-attribution.py`
- [ ] Source note on scene 0 cites claims.json visits (Roblox public API, Nov 25, 2026) — no hardcoded notes anywhere
- [ ] Brand: `top5.html` carries the watermark (36 px) + mascot (240 px) + FOLLOW NOOBNOMORE — added to the template in this build (the template predated brand; gate check 12 must PASS, not N/A)

## Notes

- Ranking is by TOTAL VISITS (Roblox API, Nov 25, 2026) — stated in the hook ("over 75 billion visits") and restated in the conclusion. Displayed pills are the same numbers, one decimal.
- 99 Nights: the Thanksgiving Challenge starts November 25, 2026 (day before Thanksgiving, official Roblox event listing) — NOT November 29 (that is last year's schedule, still shown by several guides). The video says "now live", no date, so no tense risk.
- The "45 free diamonds" (three working 99 Nights codes, 15 each) is verified but NOT in the narration — it is a general codes fact, not a Thanksgiving Challenge reward; it belongs in the publish.md description.
- The trend pick's "+123% players in 24h" for Pet Simulator 99 could not be verified from any source and is DROPPED — the video makes no player-growth claim.
- Share test #1 of 2: the share CTA is spoken in the last sentence ("Send this to a friend who plays Roblox today.") with the matching on-screen title — the publish.md share line alone does not count.
- Hook test #1 of 3: concrete hook, big number as the big title ("75 BILLION VISITS."), no question hook.

## Second shots (applied after build, before draft render)

Measured narration runs at 2.0 wps (43.44 s in build 1, 42.60 s in build 2 — the TTS take is NOT byte-identical across rebuilds, contrary to the Facts v4 note; second-shot times must always be derived from the CURRENT build's transcript.json), so every rank scene exceeds the 5.0 s image limit. Mid-sentence second shots (v5 precedent) split each scene; split times from the build-2 `videos/roblox-top5-thanksgiving/transcript.json` word timings:

- Scene 1 (#5 NFL): second shot at 8.50 s (after "visits") → nfl-detail.webp, ends 10.02 s
- Scene 2 (#4 PS99): second shot at 13.10 s (after the game name) → ps99-detail.webp, ends 16.48 s
- Scene 3 (#3 Fisch): second shot at 20.28 s (after "visits") → fisch-detail.webp, ends 22.68 s
- Scene 4 (#2 99 Nights): second shot at 25.44 s (after the game name) → nights-detail.webp, ends 29.64 s
- Scene 5 (#1 Grow a Garden): second shot at 33.92 s (after "visits") → garden-detail.webp, ends 35.34 s
- Scene 6 (payoff): second shot at 40.28 s (share sentence start) → share-friends.webp, ends 43.06 s
