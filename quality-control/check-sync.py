#!/usr/bin/env python3
"""check-sync.py — caption/voice synchronization check (v3.1 gate, 22 Nov 2026).

Compares each caption's appearance timestamp (metadata.json) with the
Whisper word timestamps of the corresponding words in the DELIVERED MP4.

For each caption: start_gap = caption.start - first_word.start,
end_gap = caption.end - last_word.end. Reports the max and mean absolute
start gap (the gate) and the end gaps (informational). Gate: max
|start_gap| <= 0.3 s. Exit 0 = PASS, exit 1 = FAIL.

TIMING MODEL — measured 22 Nov 2026, facts v3.1: Whisper SMALL's word
starts on a loudnorm-normalized mix run 0.3-0.7 s EARLY for
sentence-initial words (the dynamic gain boosts the pre-speech breath
and small stretches the word back over it), while TINY's starts match
the build transcript within 0.04 s. Small is kept for word IDENTITY
(check-narration-fuzzy.py); sync uses TINY for word TIMING (default
--model tiny). Passing --transcript reuses another transcription, but
a small-model transcript biases the gaps — the report records which
model the timestamps came from.

SMEAR CORRECTION (22 Nov 2026): tiny still smears SOME sentence-initial
words back across the preceding pause on the normalized mix — "Chat"
timed 25.86 inside the real 25.47-26.28 pause, "So" timed 28.76 while
the pause ran 28.82-29.40. The mix's music bed fills the pauses, so the
silences are read from the CLEAN narration (--narration, default
<metadata-dir>/narration.mp3) and the same rule as the builder applies
(caption_timing.reanchor_smears): a word whose start lies inside a
silence >= 0.3 s, or whose span contains one, moves to the silence end.
No speech happens inside a silence, so the correction can only fix gaps
caused by the smear — it cannot hide a genuinely late caption (the
corrected start is a lower bound on the true start). Corrections are
recorded in the report ("timing_corrections").

Usage:
  check-sync.py --mp4 <final.mp4> --metadata videos/<slug>/metadata.json
      [--model tiny] [--transcript <narration-fuzzy-report.json>]
      [--narration videos/<slug>/narration.mp3] [--output sync.json]
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from caption_timing import reanchor_smears  # noqa: E402
from narration_lexicon import canonical, words  # noqa: E402
from transcribe import decode_to_pcm  # noqa: E402

THRESHOLD_S = 0.3


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).replace("*", " ")


def transcribe(mp4: Path, model: str):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(decode_to_pcm(mp4), language="en", word_timestamps=True)
    return [{"word": wd.word.strip(), "start": float(round(wd.start, 2)),
             "end": float(round(wd.end, 2)), "prob": float(round(wd.probability, 2))}
            for s in segs for wd in (s.words or [])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True)
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--model", default="tiny",
                    help="Whisper model for word timings (tiny: stable starts)")
    ap.add_argument("--transcript",
                    help="optional: JSON report from check-narration-fuzzy.py "
                         "(its 'words'); overrides --model")
    ap.add_argument("--narration",
                    help="clean narration mp3 for the smear correction "
                         "(default: <metadata-dir>/narration.mp3 when it "
                         "exists; without it, timings are uncorrected)")
    ap.add_argument("--output")
    args = ap.parse_args()

    meta = json.loads(Path(args.metadata).read_text())
    captions = meta["captions"]
    if args.transcript:
        rep = json.loads(Path(args.transcript).read_text())
        wlist, model_used = rep["words"], rep.get("model", "unknown")
    else:
        wlist = transcribe(Path(args.mp4), args.model)
        model_used = args.model
    # Smear correction (see module docstring): a sentence-initial word
    # stretched back across a pause gets its start moved to the silence
    # end, using the CLEAN narration's silences (the mix's bed fills the
    # pauses, so silencedetect on the MP4 cannot see them).
    narration = args.narration
    if narration is None:
        cand = Path(args.metadata).parent / "narration.mp3"
        narration = str(cand) if cand.exists() else None
    timing_corrections = []
    if narration:
        wlist, timing_corrections = reanchor_smears(wlist, Path(narration))
        for c in timing_corrections:
            print(f"  re-anchored {c['word']!r}: {c['old_start']:.2f} -> "
                  f"{c['new_start']:.2f} s (silence "
                  f"{c['silence'][0]:.2f}-{c['silence'][1]:.2f} s)")
    else:
        print("  no clean narration found — sync timings uncorrected")
    # Transcript words carry punctuation ("years,", "value.") — strip it
    # with the same tokenizer as the caption words, or "years" never
    # matches "years," and the alignment collapses (found 22 Nov 2026:
    # that bug alone pushed mysteries cap 0 to 0.69 coverage).
    tw = []
    for w in wlist:
        toks = words(w["word"])
        tw.append((canonical(toks[0]) if toks else "", w))

    pos = 0
    per_caption, unmatched = [], []
    for ci, cap in enumerate(captions):
        cw = [canonical(t) for t in words(strip_html(cap.get("html") or cap["text"]))]
        # Time-windowed alignment: take the transcript words spoken around
        # this caption (+/-1 s) and align the caption's words against them
        # with difflib. (A positional walk proved brittle: one split or
        # mis-heard word desynced every later caption.)
        win = [(k, c0, w0) for k, (c0, w0) in enumerate(tw)
               if cap["start"] - 1.0 <= w0["start"] <= cap["end"] + 1.0]
        win_tokens = [c0 for _, c0, _ in win]
        sm = difflib.SequenceMatcher(a=cw, b=win_tokens, autojunk=False)
        matched_pairs = []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    matched_pairs.append((i1 + k, j1 + k))
        coverage = len(matched_pairs) / max(len(cw), 1)
        if coverage < 0.7 or not matched_pairs:
            unmatched.append(ci)
            per_caption.append({"caption": ci, "text": cap["text"][:60],
                                "start_gap_s": None, "end_gap_s": None,
                                "matched": False,
                                "coverage": round(coverage, 2)})
            continue
        first = win[matched_pairs[0][1]][2]
        last = win[matched_pairs[-1][1]][2]
        per_caption.append({"caption": ci, "text": cap["text"][:60],
                            "caption_start_s": cap["start"], "caption_end_s": cap["end"],
                            "first_word": first["word"], "first_word_start_s": first["start"],
                            "last_word": last["word"], "last_word_end_s": last["end"],
                            "start_gap_s": round(cap["start"] - first["start"], 2),
                            "end_gap_s": round(cap["end"] - last["end"], 2),
                            "matched": True, "coverage": round(coverage, 2)})
    start_gaps = [abs(c["start_gap_s"]) for c in per_caption if c["matched"]]
    end_gaps = [abs(c["end_gap_s"]) for c in per_caption if c["matched"]]
    max_start = max(start_gaps) if start_gaps else None
    mean_start = round(sum(start_gaps) / len(start_gaps), 3) if start_gaps else None
    max_end = max(end_gaps) if end_gaps else None
    mean_end = round(sum(end_gaps) / len(end_gaps), 3) if end_gaps else None
    verdict = "PASS" if (not unmatched and max_start is not None
                         and max_start <= THRESHOLD_S) else "FAIL"
    report = {"mp4": args.mp4, "verdict": verdict, "threshold_s": THRESHOLD_S,
              "timing_model": model_used, "narration": narration,
              "timing_corrections": timing_corrections,
              "captions_checked": len(captions), "unmatched_captions": unmatched,
              "max_abs_start_gap_s": max_start, "mean_abs_start_gap_s": mean_start,
              "max_abs_end_gap_s": max_end, "mean_abs_end_gap_s": mean_end,
              "per_caption": per_caption}
    print(f"SYNC CHECK (Whisper {model_used} timings): {verdict} "
          f"(threshold max |start gap| <= {THRESHOLD_S} s)")
    print(f"  captions: {len(captions)} matched, {len(unmatched)} unmatched")
    print(f"  start gaps: max {max_start} s | mean {mean_start} s")
    print(f"  end gaps:   max {max_end} s | mean {mean_end} s")
    for c in per_caption:
        if c["matched"]:
            print(f"    cap {c['caption']}: start gap {c['start_gap_s']:+.2f} s, "
                  f"end gap {c['end_gap_s']:+.2f} s  ({c['text'][:45]}...)")
        else:
            print(f"    cap {c['caption']}: UNMATCHED ({c['text'][:45]}...)")
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=1) + "\n")
        print(f"  report saved to {args.output}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
