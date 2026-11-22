"""caption_timing.py — fuzzy-aligned caption timings (shared by the builder
and the v3.1 caption-timing fix).

Maps each script sentence to the Whisper words that actually speak it
(fuzzy alignment: lexicon + number forms + character tolerance) and
returns per-sentence (start, end) from the aligned words' timestamps.

Replaces the old count-based slicing, which drifted whenever Whisper's
word count differed from the script's — "Brainrot" heard as "brain rod"
(2 words) shifted every later caption 1-2 s early (top5 and mysteries
v3: captions appeared up to 2.08 s before the words they show). See
quality-control/check-sync.py (gate: max |start gap| <= 0.3 s).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from narration_lexicon import align, canonical_spans, canonical_spans_from_words


def script_sentences(clean_script: str) -> list:
    return [s.strip() for s in
            re.split(r"(?<=[.!?])\s+", clean_script) if s.strip()]


def corrected_captions(clean_script: str, wlist: list) -> list:
    """Return [(start, end)] per script sentence, aligned to the Whisper
    word list `wlist` (dicts with start/end). A sentence with no aligned
    word gets (None, None)."""
    sentences = script_sentences(clean_script)
    script_spans = canonical_spans(clean_script)
    transcript_spans = canonical_spans_from_words([w["word"] for w in wlist])
    results, _extras = align([t for t, _, _ in script_spans],
                             [t for t, _, _ in transcript_spans])
    aligned = {}
    for res in results:
        if res["status"] == "match" and res["t_idx"] is not None:
            ts, te = transcript_spans[res["t_idx"]][1:]
            aligned[res["s_idx"]] = (ts, te)
    out, off = [], 0
    for s in sentences:
        # word count with the same tokenizer the spans use (words()),
        # not split() — a hyphenated word is one split() token but two
        # words() tokens.
        n = len(re.findall(r"[a-z0-9']+", s.lower().replace("*", " ")))
        sent_idx = [i for i, (_, rs, re_) in enumerate(script_spans)
                    if rs >= off and re_ <= off + n]
        spans = [aligned[i] for i in sent_idx if i in aligned]
        if spans:
            first_raw = min(sp[0] for sp in spans)
            last_raw = max(sp[1] for sp in spans) - 1
            out.append((wlist[first_raw]["start"], wlist[last_raw]["end"]))
        else:
            out.append((None, None))
        off += n
    return out
