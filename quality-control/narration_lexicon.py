"""narration_lexicon.py — shared fuzzy-matching helpers for the narration checks.

Canonicalizes words so Whisper's predictable mis-hearings count as the
script's term: proper-noun variants and two-word phrases (see
narration-lexicon.json), number words ("sixteen" = "16"), and a
character-tolerance fallback (difflib ratio >= FUZZY_RATIO).

Matching order for a script token vs a transcript token:
  1. exact equality (after lower-casing / punctuation strip)
  2. lexicon canonical forms equal
  3. difflib ratio >= FUZZY_RATIO
Exact first matters: "robots" is both a real script word ("means robots
plus blocks") and Whisper's rendering of "Robux" — the lexicon maps it to
"robux", but the exact check still lets the real "robots" match.
"""
import difflib
import json
import re
from pathlib import Path

FUZZY_RATIO = 0.80

_LEX = json.loads((Path(__file__).parent / "narration-lexicon.json").read_text())
VARIANTS = _LEX["variants"]
PHRASES = _LEX["phrases"]
NUMBERS = _LEX["numbers"]


def words(text: str) -> list:
    """Lower-cased word tokens; asterisks (emphasis marks) stripped."""
    return re.findall(r"[a-z0-9']+", text.lower().replace("*", " "))


def _merge_phrases(tokens: list) -> list:
    """Merge known two-word phrases; returns (token, raw_start, raw_end)
    triples so a merged token still maps back to its raw words."""
    out, i = [], 0
    while i < len(tokens):
        if i + 1 < len(tokens):
            pair = tokens[i] + " " + tokens[i + 1]
            if pair in PHRASES:
                out.append((PHRASES[pair], i, i + 2))
                i += 2
                continue
        out.append((tokens[i], i, i + 1))
        i += 1
    return out


def canonical(token: str) -> str:
    t = token.lower().strip("'")
    if t in NUMBERS:
        return NUMBERS[t]
    return VARIANTS.get(t, t)


def canonical_spans_from_words(word_list: list) -> list:
    """Canonical tokens with spans over an explicit word list (e.g. a
    Whisper word list). Returns [(token, start, end)] where start/end
    index into word_list. Each word is tokenized with words(); a word
    that tokenizes to several tokens (e.g. "well-known") spans them."""
    tokens, owners = [], []
    for i, w in enumerate(word_list):
        for t in words(w):
            tokens.append(t)
            owners.append(i)
    merged = _merge_phrases(tokens)
    return [(canonical(t), owners[s], owners[e - 1] + 1)
            for (t, s, e) in merged]


def canonical_spans(text: str) -> list:
    """Canonical tokens with their raw-word spans: [(token, start, end)].
    `start`/`end` index into words(text), so a merged phrase token maps
    back to the two raw words it came from."""
    return canonical_spans_from_words(words(text))


def canonical_tokens(text: str) -> list:
    """Token list with phrases merged and each token canonicalized."""
    return [tok for (tok, _, _) in canonical_spans(text)]


def tokens_match(script_tok: str, transcript_tok: str) -> tuple:
    """Return (matched, method) for one script token vs one transcript token.
    method is 'exact' | 'lexicon' | 'fuzzy' | None."""
    if script_tok == transcript_tok:
        return True, "exact"
    if canonical(script_tok) == canonical(transcript_tok):
        return True, "lexicon"
    if difflib.SequenceMatcher(None, script_tok, transcript_tok).ratio() >= FUZZY_RATIO:
        return True, "fuzzy"
    return False, None


def align(script_tokens: list, transcript_tokens: list) -> list:
    """Word-level alignment via difflib; returns (results, extras).
    Each result is one script token: {script, transcript, status, method,
    s_idx, t_idx} where status is 'match' or 'missing' and t_idx is the
    index of the matched transcript token (None when missing). Transcript
    tokens with no script counterpart are returned separately as extras
    (each as {transcript, t_idx})."""
    sm = difflib.SequenceMatcher(a=script_tokens, b=transcript_tokens, autojunk=False)
    results, extras = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                results.append({"script": script_tokens[i1 + k],
                                "transcript": transcript_tokens[j1 + k],
                                "status": "match", "method": "exact",
                                "s_idx": i1 + k, "t_idx": j1 + k})
        elif tag == "replace":
            s_part, t_part = script_tokens[i1:i2], transcript_tokens[j1:j2]
            for k, s in enumerate(s_part):
                t = t_part[k] if k < len(t_part) else None
                if t is not None:
                    ok, method = tokens_match(s, t)
                    results.append({"script": s, "transcript": t,
                                    "status": "match" if ok else "missing",
                                    "method": method,
                                    "s_idx": i1 + k, "t_idx": j1 + k})
                else:
                    results.append({"script": s, "transcript": None,
                                    "status": "missing", "method": None,
                                    "s_idx": i1 + k, "t_idx": None})
            for k, t in enumerate(t_part[len(s_part):]):
                extras.append({"transcript": t, "t_idx": j1 + len(s_part) + k})
        elif tag == "delete":
            for k, s in enumerate(script_tokens[i1:i2]):
                results.append({"script": s, "transcript": None,
                                "status": "missing", "method": None,
                                "s_idx": i1 + k, "t_idx": None})
        elif tag == "insert":
            for k, t in enumerate(transcript_tokens[j1:j2]):
                extras.append({"transcript": t, "t_idx": j1 + k})
    return results, extras
