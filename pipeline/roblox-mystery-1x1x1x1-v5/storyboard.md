# Storyboard — roblox-mystery-1x1x1x1-v5 (Phase 4C rebuild)

- **Format:** mysteries — **Template:** `templates/formats/mysteries.html` (v5: 6 scenes, 12 s base — scene 4 "THE VERDICT" added, conclusion renumbered to scene 5) — **Accent:** purple `#8B5CF6`
- **Scenes:** 6 — **Sentences:** 10 — **Beats:** 10 (one per sentence; scenes 0, 3, 4, 5 hold two sentences — each scene's single rendered title shares a content word with every sentence it covers; second shots give each sentence its own image, except scene 4 where both sentences share never-hacker for a combined 3.21 s span)
- **Breaks:** [2, 1, 1, 2, 2, 2]
- **Hook:** "Could one username hack your account, destroy your game, and ban you?" (12 words, question mark + number word "one") — **Loop:** first/last share "username"/"game" via "one"/"legend"? Loop is report-only; first and last sentences share "game" (first: "destroy your game", last: "in the game Forsaken").
- **Second shots (applied with `pipeline/second-shot.py` after the build, before the draft render — times from the v5 metadata captions):** scene 0 → name-reveal at the start of sentence 2 (4.38 s); scene 1 → hat-necro mid-sentence 3 (10.22 s, scene midpoint); scene 2 → chaos-sign mid-sentence 4 (16.48 s, scene midpoint); scene 3 → test-account at the scene midpoint (23.89 s — the scene window is 8.58 s, so the split is balanced 4.29/4.29 s, not at the sentence boundary); scene 5 → legend at the start of sentence 10 (33.68 s). Each image span stays ≤ 5.0 s; no image is used in two scenes. (Scene windows start at the previous sentence's end, so spans are measured from there — the Facts v5 gate lesson.)

| # | Time | Visual (distinct, one per scene) | Motion | On-screen text | Caption |
|---|---|---|---|---|---|
| 1 | 0.0– | Dark silhouette in fog; second shot: glowing green name tag 1x1x1x1 on a dark voxel wall | question-mark pop, title pop, image crossfade, 3-segment zoom cut | THE USERNAME WAS 1X1X1X1. | Could one username hack your account, destroy your game, and ban you? His name was *1x1x1x1*. |
| 2 |  | Spooky spellbook with a green skull; second shot mid-sentence: dusty wizard hat glowing green on a library shelf | head slide-in, image crossfade, 3-segment zoom cut | FIRST SEEN IN 2007 — THE NECROBLOXICON | It first appeared in 2007, in the description of a spooky Roblox hat called the Necrobloxicon. |
| 3 |  | Voxel world glitching apart; second shot mid-sentence: cracked voxel wall with a glowing green graffiti tag | head slide-in, image crossfade, 3-segment zoom cut | EVERY CRASH LOOKED LIKE PROOF | Then exploiters wrecked games and signed their chaos with his name, so every crash looked like proof. |
| 4 |  | Admin avatar at a glowing console; second shot: plain grey blank avatar in a bright white test room | head slide-in, image crossfade, 3-segment zoom cut | 2011: THE TRUTH — A TEST ACCOUNT | But in 2011, a Roblox admin revealed the truth. It was a test account, created by an admin named Shedletsky, for a story. |
| 5 |  | Grey voxel avatar dissolving into purple pixels | head slide-in, 3-segment zoom cut | NEVER A HACKER. | He was *never* a hacker. The hacker never existed. |
| 6 |  | Giant glowing red X over a shadowy silhouette; second shot at sentence 10: glowing tombstone legend in purple fog; mascot pop-in, CTA pulse | title pop, mascot pop, CTA pulse, image crossfade, 3-segment zoom cut | ANSWER: NO. LEGEND LIVES. | So the answer is no. But the legend lives on, as a killer in the game Forsaken. |

## Transitions

- Scene 1 → 2: slide-in from the right (template default)
- Scene 2 → 3: slide-in from the right; inside scene 2, image crossfade book → hat-necro mid-sentence 3
- Scene 3 → 4: slide-in from the right; inside scene 3, image crossfade glitch → chaos-sign mid-sentence 4
- Scene 4 → 5: slide-in from the right; inside scene 4, image crossfade admin → test-account at sentence 6
- Scene 5 → 6: slide-in from the right; inside scene 6, image crossfade answer-no → legend at sentence 10; legend stays on screen to the end

## Notes

- No source notes (Mysteries has none — the story is a myth debunk, sourced in claims.json).
- Sentences 3 and 4 each exceed 5.0 s alone (5.58 s / 5.34 s in v4) — they are split mid-sentence with a second shot; the script is unchanged (no rephrase justified — the sentences are fine, only the image needs to change).
- New images (v5, generated in this environment, original voxel illustrations): name-reveal (scene 0, second shot), hat-necro (scene 1, second shot), chaos-sign (scene 2, second shot), test-account (scene 3, second shot), never-hacker (scene 4), answer-no (scene 5, base). The first test-account render had a garbled "TE$T" label — regenerated without any text (test-account v2).
- Mysteries v4 defects fixed: no image held > 5.0 s; every sentence has its own image (second shots inside multi-sentence and long sentences); scene 4's verdict ("NEVER A HACKER.") is now its own scene instead of sharing "THE LEGEND LIVES ON." with the conclusion; first frame has title + image at t=0 (template 4C rule); watermark 36 px (template).
