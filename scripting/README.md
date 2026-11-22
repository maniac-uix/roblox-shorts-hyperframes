# scripting/

Scripts and storytelling. One script per video, in English, written to be
spoken — never written to be read silently.

## Rules

- English only. Write numbers and abbreviations as they should sound
  ("three point seven nine billion", not "$3.79B").
- Target pace: ~2.3 words/second (see `config/factory.json`).
- Structure: hook (first 2 s, the question or the result) → beats (one idea
  per scene) → payoff + CTA (follow / comment).
- Every sentence traces to the research brief. No sentence without a source.
- Duration rule: video duration = narration duration + music bed; the final
  audio mix must equal the video duration (±0.1 s, QC gate).

## Template

See `script-template.md`. The voiceover is generated with
`bash voiceover/generate-voice.sh "<script text>"`.
