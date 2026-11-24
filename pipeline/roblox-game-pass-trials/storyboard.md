# Storyboard — roblox-game-pass-trials

- **Format:** news — **Template:** `templates/formats/news.html` — **Accent:** red `#EF4444`
- **Duration:** ~38.5 s estimated (94 words) — **Scenes:** 9 — **Sentences:** 9 — **Beats:** 9 (one per sentence, one per scene)
- **Breaks:** [1, 1, 1, 1, 1, 1, 1, 1, 1]
- **Hook:** "Starting December 2, try a game pass for free." (9 words, digit) — **Loop:** first/last share "try", "December", "2"

| # | Time | Visual (distinct, one per scene) | Motion | On-screen text | Caption |
|---|---|---|---|---|---|
| 1 | 0.0–3.7 | Voxel Shop storefront at dusk, big glowing red TRY button next to BUY on a game-pass stand, small voxel hero walking in | TRY button pulse, sparkle burst | TRY IT FREE. | Starting December 2, try a game pass for free. |
| 2 | 3.7–8.6 | Close-up voxel game-pass card in the Shop, Try button glowing red beside Buy | card slide-in, button glow pulse | THE TRY BUTTON. | Roblox adds a Try button to the Shop, right next to Buy. |
| 3 | 8.6–13.5 | Voxel avatar tapping a glowing game pass, golden unlock burst, sparkles | unlock flash, sparkles rise | ONE FULL SESSION. | Tap it, and you unlock the whole pass, for one full session. |
| 4 | 13.5–17.2 | Big voxel clock and hourglass glowing red "1 HOUR", voxel avatar playing below | clock hands spin, glow pulse | ONE HOUR FREE. | One session means at least one hour of free play. |
| 5 | 17.2–21.3 | Single golden voxel ticket stamped "1 PER PASS" on a dark pedestal | ticket flip-in, gold shimmer | ONE PER PASS. | One free trial per pass, and only one at a time. |
| 6 | 21.3–25.0 | Voxel creator at a control panel with red switches, one switch ON and glowing, others OFF | switch flick, panel lights chase | THE CREATOR DECIDES. | But the creator has to turn trials on first. |
| 7 | 25.0–29.1 | Voxel game-pass card stamped "OWNED" in red, Try button greyed out | stamp slam, grey fade | NO TRY BUTTON. | A pass you already own shows no Try button at all. |
| 8 | 29.1–34.0 | Voxel avatar pressing a big glowing red Buy button, Robux coins bursting | coin burst, button pulse | BUY TO KEEP IT. | Buy it before the session ends, and you keep it for good. |
| 9 | 34.0–38.5 | Proud voxel hero with cape on a podium, red confetti falling, payoff | confetti fall, hero pop-in | TRY BEFORE YOU BUY. | From noob to pro, try before you buy, starting December 2. |

## Transitions

- Scene 1 → 2: slide to the pass card on the voice beat ("Roblox adds a Try button")
- Scene 2 → 3: zoom-blur into the unlock burst
- Scene 3 → 4: wipe to the clock
- Scene 4 → 5: slide to the ticket pedestal
- Scene 5 → 6: wipe to the creator panel
- Scene 6 → 7: fade to the owned card
- Scene 7 → 8: zoom into the Buy button
- Scene 8 → 9: fade through the hero pop

## Heads (rendered titles — one per scene)

- title-0 "TRY IT FREE.", head-1 "THE TRY BUTTON.", head-2 "ONE FULL SESSION.", head-3 "ONE HOUR FREE.", head-4 "ONE PER PASS.", head-5 "THE CREATOR DECIDES.", head-6 "NO TRY BUTTON.", head-7 "BUY TO KEEP IT.", title-8 "TRY BEFORE YOU BUY." + sub-8 "December 2 — try it first." (see `heads.json`).

## Assets needed

- [ ] 9 generated images (voxel style, 1920×1280 WebP, news red `#EF4444` theme): shop-try-button, pass-card-try, unlock-pass, one-hour-clock, one-ticket, creator-switch, owned-pass, buy-to-keep, payoff-hero — all ORIGINAL voxel scenes; no Roblox logo, no Roblox UI reproduced pixel-for-pixel (the Shop UI is evoked, not copied)
- [ ] Music: "Basic Implosion" by Kevin MacLeod, CC BY 3.0 — attribution via `pipeline/music-attribution.py`
- [ ] Source note on scene 0 cites claims.json #1 (DevForum announcement, Nov 18, 2026) — no hardcoded notes anywhere

## Notes

- Claim 5 (crash / system-error resume if you rejoin within one hour) is verified but NOT in the narration (word budget) — it belongs in the publish.md description.
- Buying a pass is a real purchase in Robux; on a child's account Roblox spending limits apply — also for the publish.md description, not the narration (word budget).
- The "Try" button only appears on passes whose creator turned trials on (claims.json #2 + #7) — the video says so explicitly in sentence 6.
- Brand: `news.html` carries the watermark (36 px) + mascot (240 px) + FOLLOW NOOBNOMORE from the start — gate check 12 must PASS.
