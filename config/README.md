# config/

One central file: `factory.json`. Everything a video depends on lives here —
change it here, never hard-code it in a template.

- `video`: 1080 × 1920, 30 fps, H.264 MP4, 30–45 s (target 35 s)
- `language`: English for all videos (voice, text, metadata)
- `voiceover`: built-in Muse TTS, voice Helio, speed 100
- `style`: gaming-dark theme, Montserrat, safe zone, per-format accents
- `audio`: royalty-free music only, −18 dB, voice above music
- `cloud`: safe temp paths, memory gate, single-render rule
- `costs`: zero paid services — flag anything paid before integrating it
