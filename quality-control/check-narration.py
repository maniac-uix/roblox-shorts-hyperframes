#!/usr/bin/env python3
"""check-narration.py — prove the narration in an MP4 matches the script.

Extracts the audio from the MP4, transcribes it with local Whisper (tiny),
and compares the transcript word-for-word with the script text.

Usage:
  python3 quality-control/check-narration.py --mp4 output/factory-test-2.mp4 \
      --script "Roblox hides secrets in plain sight." [--output <report.json>]

Exit 0 only when every script word is present, in order, with no extra
spoken words. A mismatch prints exactly which words are missing or added.
Limits: Whisper tiny can mis-hear a word (low prob). Words with prob < 0.5
are flagged as uncertain, not as failures, and must be checked by listening.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
VENV_PY = PROJECT_DIR / ".cache-tmp" / "venv-transcribe" / "bin" / "python"
TRANSCRIBE = PROJECT_DIR / "quality-control" / "transcribe.py"
TMP_DIR = PROJECT_DIR / ".cache-tmp" / "tmp"


def norm_words(text: str) -> list:
    text = text.lower()
    text = re.sub(r"[^a-z0-9' ]", " ", text)
    return [w for w in text.split() if w]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    if not VENV_PY.exists():
        print("ERROR: transcription venv missing at", VENV_PY)
        print("Run: python3 -m venv .cache-tmp/venv-transcribe && "
              ".cache-tmp/venv-transcribe/bin/pip install faster-whisper")
        return 2

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    audio = TMP_DIR / "check-narration-audio.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", args.mp4,
         "-vn", "-ac", "1", "-ar", "16000", str(audio)],
        check=True,
    )
    transcript_path = TMP_DIR / "check-narration-transcript.json"
    subprocess.run(
        [str(VENV_PY), str(TRANSCRIBE), "--input", str(audio),
         "--output", str(transcript_path), "--language", "en"],
        check=True,
    )
    transcript = json.load(open(transcript_path))
    spoken = [w["word"] for w in transcript["words"]]
    expected = norm_words(args.script)
    spoken_norm = norm_words(" ".join(spoken))

    # Longest common subsequence match, in order.
    i = j = 0
    matched, missing, extra = [], [], []
    while i < len(expected) and j < len(spoken_norm):
        if expected[i] == spoken_norm[j]:
            matched.append(expected[i])
            i += 1
            j += 1
        else:
            # Look ahead: is the expected word coming later (extra spoken word)?
            if expected[i] in spoken_norm[j + 1:j + 4]:
                extra.append(spoken_norm[j])
                j += 1
            else:
                missing.append(expected[i])
                i += 1
    missing += expected[i:]
    extra += spoken_norm[j:]
    uncertain = [w for w in transcript["words"] if w["prob"] < 0.5]

    last_word_end = transcript["words"][-1]["end"] if transcript["words"] else None
    report = {
        "mp4": args.mp4,
        "scriptWords": len(expected),
        "spokenWords": len(spoken_norm),
        "matchedWords": len(matched),
        "missingWords": missing,
        "extraWords": extra,
        "uncertainWords": [{"word": w["word"], "prob": w["prob"]} for w in uncertain],
        "lastWordEndSeconds": last_word_end,
        "transcript": " ".join(spoken),
    }
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        json.dump(report, open(args.output, "w"), indent=1)

    print(f"script words: {len(expected)} | spoken words: {len(spoken_norm)} | matched: {len(matched)}")
    print("transcript:", report["transcript"])
    print("last word ends at:", last_word_end, "s")
    if missing:
        print("MISSING words:", missing)
    if extra:
        print("EXTRA words:", extra)
    if uncertain:
        print("UNCERTAIN (prob < 0.5, check by listening):", report["uncertainWords"])
    if not missing and not extra:
        print("NARRATION CHECK: PASS — script matches spoken audio word-for-word.")
        return 0
    print("NARRATION CHECK: FAIL — transcript does not match the script.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
