# templates/

Reusable HyperFrames compositions. All vertical 1080 × 1920, 30 fps.

## Layout

- `base-vertical/index.html` — the factory default. Copy it per video and
  replace the `data-var-text` copy, the `--accent` and the media. The motion
  system (progress bar, glow drift, scale-pop titles, pulsing CTA) stays.
- `formats/facts.html` — Roblox Facts, teal accent. Hook → 3 verified facts.
- `formats/top5.html` — Roblox Top 5, amber accent. Hook → countdown 5→2 → #1.
- `formats/mysteries.html` — Roblox Mysteries, violet accent. Question →
  clues → UNSOLVED stamp.

More formats (hidden-secrets, game-discoveries, updates, stories) reuse
`base-vertical` with their accent from `config/factory.json`
(`style.accentsByFormat`) until a dedicated file exists.

## Rules (HyperFrames contract, see AGENTS.md §3)

- Every timed element: `class="clip"`, `data-start`, `data-duration`.
- One paused root timeline per composition on `window.__timelines`.
- No `Date.now()`, no unseeded `Math.random()`, no network fetches, no
  `repeat: -1`. Key text inside the safe zone (x 120–888, y 288–1248).
- Fonts: Montserrat via `@font-face` from
  `assets/fonts/Montserrat-Variable.woff2` (relative path from the template
  file: `../../assets/fonts/...`).
- Audio: `<audio id="narration" src="../../voiceover/narration.mp3">` —
  replaced per video with that video's padded narration.
- After any edit: `npx hyperframes check`, then `npx hyperframes snapshot`
  and look at the frames before rendering.
