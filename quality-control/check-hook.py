#!/usr/bin/env python3
"""check-hook.py — hook rule check (Phase 4B, standalone; same rule as
pipeline/run.py stage_script).

The first sentence must be <= 12 words AND contain a digit, a "?", or a
spelled-out number word (one..twenty, thirty..ninety, hundred, thousand,
million, billion). A "surprising statement" cannot be checked
automatically, so the enforceable rule is digit-or-question; a hook
that is only a surprising statement must be rephrased to include a
number or a question.

Usage:
  check-hook.py --metadata videos/<slug>/metadata.json [--output hook.json]
  check-hook.py --script pipeline/<slug>/script.txt [--output hook.json]

The script is read from metadata.json["script"] when --metadata is
given (preferred), else from the --script file.

Exit 0 iff PASS, else 1. The JSON report is the last stdout line.
"""
import argparse
import json
import re
import sys
from pathlib import Path

NUMBER_WORDS = {
    "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
    "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety", "hundred", "thousand", "million", "billion",
}

MAX_WORDS = 12


def split_sentences(text: str) -> list:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip())
            if s.strip()]


def words_of(text: str) -> list:
    return re.findall(r"[A-Za-z0-9']+", text)


def check_hook_sentence(sentence: str) -> dict:
    """Hook verdict for one sentence (the first sentence of a script)."""
    ws = words_of(sentence)
    lower = [w.lower() for w in ws]
    has_digit = any(any(c.isdigit() for c in w) for w in ws)
    has_question = "?" in sentence
    has_number_word = any(w in NUMBER_WORDS for w in lower)
    ok = (len(ws) <= MAX_WORDS
          and (has_digit or has_question or has_number_word))
    return {"first_sentence": sentence, "n_words": len(ws),
            "has_digit": has_digit, "has_question": has_question,
            "has_number_word": has_number_word,
            "verdict": "PASS" if ok else "FAIL"}


def check_hook(script: str) -> dict:
    sents = split_sentences(script)
    if not sents:
        return {"first_sentence": "", "n_words": 0, "has_digit": False,
                "has_question": False, "has_number_word": False,
                "verdict": "FAIL", "reason": "empty script"}
    return check_hook_sentence(sents[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata")
    ap.add_argument("--script")
    ap.add_argument("--output")
    args = ap.parse_args()
    if args.metadata:
        meta = json.loads(Path(args.metadata).read_text())
        script = meta.get("script", "")
        source = args.metadata
    elif args.script:
        script = Path(args.script).read_text().strip()
        source = args.script
    else:
        ap.error("need --metadata or --script")
    report = check_hook(script)
    report["source"] = source
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=1) + "\n")
    parts = []
    if report["has_digit"]:
        parts.append("digit")
    if report["has_question"]:
        parts.append("question-mark")
    if report["has_number_word"]:
        parts.append("number-word")
    print(f"hook: {report['first_sentence']!r} — {report['n_words']} words"
          + (f" ({', '.join(parts)})" if parts else " (no digit/?/number-word)")
          + f" — {report['verdict']}")
    print(json.dumps(report))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
