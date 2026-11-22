#!/usr/bin/env python3
"""check-narration-fuzzy.py — narration content check for the ROBLOX VIDEO FACTORY.

Replaces the strict word-by-word comparison (check-narration.py) for the
v3.1 gate (22 Nov 2026). Transcribes the AUDIO OF THE DELIVERED MP4 with
local faster-whisper (model "small" by default, falls back to "base" if
small cannot load — the model actually used is recorded in the report)
and compares it to the script with a FUZZY match:

  - proper-noun lexicon (narration-lexicon.json): Whisper's predictable
    mis-hearings count as the script term (DynaBlocks, Robux, Blox Fruits,
    Brainrot, Necrobloxicon, Shedletsky, Forsaken, 1x1x1x1, ...),
  - number words ("sixteen" = "16", "five" = "5", ...),
  - character tolerance: difflib ratio >= 0.80 counts as a match.

The automatic verdict is authoritative: exit 0 = PASS, exit 1 = FAIL.
A FAIL blocks delivery. If a FAIL is a false positive, add the term to
narration-lexicon.json and re-run — never override a FAIL by hand.

Also verifies the last sentence is complete and ends before the final
silence starts, and lists low-confidence words (prob < 0.6) with
timestamps as a listening aid.

Usage:
  check-narration-fuzzy.py --mp4 <final.mp4> --script "<text>"
      [--model small] [--output report.json] [--low-confidence 0.6]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from narration_lexicon import (NUMBERS, PHRASES, VARIANTS, align,  # noqa: E402
                               canonical_tokens, words)
from transcribe import decode_to_pcm  # noqa: E402

DEFAULT_MODEL = "small"
FALLBACK_MODEL = "base"


def trailing_silence_start(wav: Path, duration: float) -> float:
    """Start of the trailing silence (silencedetect -40 dB, min 0.3 s),
    or the file duration if speech runs to the end."""
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(wav),
                        "-af", "silencedetect=noise=-40dB:d=0.3",
                        "-f", "null", "-"], text=True, capture_output=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    if not starts:
        return duration
    s, e = starts[-1], ends[-1]
    return s if e >= duration - 0.3 else duration


def transcribe(pcm, model: str):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(pcm, language="en", word_timestamps=True)
    text_parts, wlist = [], []
    for s in segs:
        text_parts.append(s.text.strip())
        for wd in (s.words or []):
            # faster-whisper returns numpy scalars; float() them so the
            # report stays plain JSON-serializable.
            wlist.append({"word": wd.word.strip(), "start": float(round(wd.start, 2)),
                          "end": float(round(wd.end, 2)),
                          "prob": float(round(wd.probability, 2))})
    return " ".join(text_parts), wlist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--output")
    ap.add_argument("--low-confidence", type=float, default=0.6)
    args = ap.parse_args()

    mp4 = Path(args.mp4)
    assert mp4.exists(), f"file not found: {mp4}"
    pcm = decode_to_pcm(mp4)

    model_used, fallback = args.model, None
    try:
        text, wlist = transcribe(pcm, args.model)
    except Exception as e:
        print(f"model '{args.model}' failed ({e}); falling back to '{FALLBACK_MODEL}'",
              file=sys.stderr)
        text, wlist = transcribe(pcm, FALLBACK_MODEL)
        model_used, fallback = FALLBACK_MODEL, str(e)

    script_tokens = canonical_tokens(args.script)
    transcript_tokens = canonical_tokens(text)
    raw_transcript = words(text)
    # Which lexicon entries did Whisper actually produce? (The alignment
    # runs on canonical tokens, so a variant that canonicalizes to the
    # script term shows up as an "exact" match there — this lists the
    # variants that were really heard.)
    variant_hits = [(w, VARIANTS[w]) for w in raw_transcript if w in VARIANTS]
    phrase_hits = [(f"{raw_transcript[i]} {raw_transcript[i+1]}",
                    PHRASES[f"{raw_transcript[i]} {raw_transcript[i+1]}"])
                   for i in range(len(raw_transcript) - 1)
                   if f"{raw_transcript[i]} {raw_transcript[i+1]}" in PHRASES]
    results, extras = align(script_tokens, transcript_tokens)
    missing = [r for r in results if r["status"] == "missing"]
    fuzzy = [r for r in results if r["status"] == "match" and r["method"] == "fuzzy"]
    lexicon = [r for r in results if r["status"] == "match" and r["method"] == "lexicon"]

    # final sentence: complete in the transcript tail, and its last word
    # ends before the final silence starts (+0.3 s Whisper timing tolerance).
    sents = [s.strip() for s in args.script.replace("*", "").split(".") if s.strip()]
    final = sents[-1] if sents else ""
    # canonicalize BOTH sides: "one" in the script is "1" in the transcript
    # tokens, and "blocks" is "blox" — comparing raw script words against
    # canonical transcript tokens would false-FAIL the final sentence.
    final_words = canonical_tokens(final)
    tail = transcript_tokens[-30:]
    present = [w for w in final_words if w in tail]
    duration = len(pcm) / 16000.0
    wav = Path(".cache-tmp/tmp/fuzzy-check.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4),
                    "-ac", "1", "-ar", "16000", str(wav)], check=True)
    silence_start = trailing_silence_start(wav, duration)
    last_end = wlist[-1]["end"] if wlist else None
    final_complete = len(present) == len(final_words)
    final_before_silence = last_end is not None and last_end <= silence_start + 0.3

    low_conf = [w for w in wlist if w["prob"] < args.low_confidence]

    verdict = "PASS" if not missing and final_complete and final_before_silence else "FAIL"
    report = {
        "mp4": str(mp4), "model": model_used, "model_fallback": fallback,
        "verdict": verdict,
        "script_words": len(script_tokens), "transcript_words": len(transcript_tokens),
        "matched": sum(1 for r in results if r["status"] == "match"),
        "missing": missing, "fuzzy_matches": fuzzy, "lexicon_matches": lexicon,
        "lexicon_variants_heard": variant_hits + phrase_hits,
        "extra_transcript_words": extras,
        "transcript": text,
        "words": wlist,
        "final_sentence": {"text": final + ".", "complete": final_complete,
                           "missing_words": [w for w in final_words if w not in tail],
                           "last_word_end_s": last_end,
                           "final_silence_start_s": round(silence_start, 2),
                           "ends_before_silence": final_before_silence},
        "low_confidence_words": low_conf,
        "low_confidence_threshold": args.low_confidence,
    }
    print(f"NARRATION CHECK (fuzzy, Whisper {model_used}): {verdict}")
    print(f"  script {len(script_tokens)} words | transcript {len(transcript_tokens)} words | "
          f"matched {report['matched']} | missing {len(missing)} | "
          f"fuzzy {len(fuzzy)} | lexicon {len(lexicon)} | extra {len(extras)}")
    for r in missing:
        print(f"  MISSING: script [{r['script']}] -> transcript [{r['transcript']}]")
    for r in fuzzy:
        print(f"  fuzzy: script [{r['script']}] -> transcript [{r['transcript']}]")
    for r in lexicon:
        print(f"  lexicon: script [{r['script']}] -> transcript [{r['transcript']}]")
    if variant_hits or phrase_hits:
        print(f"  lexicon variants heard: "
              + ", ".join(f"{a}->{b}" for a, b in variant_hits + phrase_hits))
    if extras:
        print(f"  extra transcript words: {extras}")
    print(f"  final sentence: {'COMPLETE' if final_complete else 'INCOMPLETE'}; "
          f"last word ends {last_end} s, final silence starts {silence_start:.2f} s "
          f"-> {'ends before silence' if final_before_silence else 'RUNS INTO SILENCE'}")
    print(f"  low-confidence words (< {args.low_confidence}): {len(low_conf)}")
    for w in low_conf:
        print(f"    {w['start']:6.2f}-{w['end']:6.2f}s  {w['word']!r} (prob {w['prob']})")
    if args.output:
        Path(args.output).write_text(
            json.dumps(report, indent=1, default=lambda o: o.item()
                       if hasattr(o, "item") else str(o)) + "\n")
        print(f"  report saved to {args.output}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
