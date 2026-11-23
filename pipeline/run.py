#!/usr/bin/env python3
"""run.py — the ROBLOX VIDEO FACTORY pipeline driver (Phase 3).

One URL + one format in, one publishable MP4 out — with a STOP POINT
after the script, claims.json and storyboard (Step 4): the driver STOPS
there and waits for the owner's green light before voice and render.

Stages (run --stage <name> to stop after that stage):
  research    validate claims.json against pipeline/claims-schema.json
              (manual validation, no extra dependency): every claim has
              claim/source_url/date/status; status is verified/unverified/
              rephrased; unverified claims are NOT in the script.
  script      validate the script: English, >= 4 sentences. The word-count
              duration estimate (words / 2.43 w/s) is a WARNING only —
              measured speech rate varies 2.07-3.32 wps, so it can never
              validate the duration; the hard validation is on the MEASURED
              narration in the builder.
  storyboard  validate the storyboard: >= 4 scenes, every scene has a
              visual, a motion and a caption; >= 2 distinct motions
              overall (no frozen-card video); the captions, concatenated,
              are exactly the script sentences in order (so the scene
              breaks passed to the builder are exact). Also validates
              source-notes.json when present: every note must cite a
              verified claim in claims.json (date or source domain).
  build       build the composition (rendering/build_video.py) — the voice
              is generated inside the builder (built-in TTS, measured,
              never cut) and the duration is derived from it.
  draft       draft render (rendering/render.sh) + qc.sh on the draft.
  final       final render (rendering/render.sh --quality standard).
  normalize   loudness normalisation (-14 LUFS / TP -1 dBTP, 48 kHz).
  gate        the blocking gate (quality-control/gate.py) on the final MP4.
  deliver     print the delivery summary + music attribution text.

Work dir: pipeline/<slug>/ — claims.json, script.txt, storyboard.md,
top5-values.json (top5 only), attribution.txt, stage logs.
Video build outputs stay in videos/<slug>/ and output/<slug>.mp4.

Usage:
  python3 pipeline/run.py --url <public Roblox URL> --format facts \
      --slug my-video --stage storyboard   # stop point (Step 4)
  python3 pipeline/run.py --slug my-video --stage gate      # after green light
  python3 pipeline/run.py --slug my-video --stage deliver
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
STAGES = ["research", "script", "storyboard", "build",
          "draft", "final", "normalize", "gate", "deliver"]
WPS = 2.43  # words per second (config/factory.json durationPolicy)
DUR_MIN, DUR_MAX = 30, 45


def run(cmd, **kw):
    r = subprocess.run(cmd, text=True, capture_output=True, **kw)
    if r.returncode != 0:
        print(r.stdout[-2000:] if r.stdout else "", file=sys.stderr)
        print(r.stderr[-2000:] if r.stderr else "", file=sys.stderr)
        raise SystemExit(f"FAILED: {' '.join(map(str, cmd))} (exit {r.returncode})")
    return r


def words(text: str) -> list:
    return re.findall(r"[A-Za-z0-9']+", text.replace("*", " "))


def stage_research(d: Path):
    claims = json.loads((d / "claims.json").read_text())
    schema = json.loads((PROJECT / "pipeline" / "claims-schema.json").read_text())
    for key in schema["required"]:
        assert key in claims, f"claims.json: missing '{key}'"
    assert claims["format"] in schema["properties"]["format"]["enum"], \
        f"claims.json: unknown format {claims['format']}"
    verified = unverified = rephrased = 0
    for c in claims["claims"]:
        for key in ("claim", "source_url", "date", "status"):
            assert key in c and c[key], f"claims.json: claim missing '{key}': {c}"
        assert c["status"] in ("verified", "unverified", "rephrased"), \
            f"claims.json: bad status {c['status']}"
        if c["status"] == "rephrased":
            assert c.get("narration_text"), \
                f"claims.json: rephrased claim needs narration_text: {c['claim'][:40]}"
        if c["status"] == "verified":
            verified += 1
        elif c["status"] == "unverified":
            unverified += 1
        else:
            rephrased += 1
    print(f"  research: {len(claims['claims'])} claims — {verified} verified, "
          f"{rephrased} rephrased, {unverified} unverified (excluded from narration)")
    return claims


def stage_script(d: Path, claims):
    script = (d / "script.txt").read_text().strip()
    n = len(words(script))
    est = n / WPS
    print(f"  script: {n} words, estimated {est:.1f} s (target {DUR_MIN}-{DUR_MAX} s)")
    # The estimate is a WARNING only (22 Nov 2026, owner's correction):
    # measured speech rate varies 2.07-3.32 wps across videos, so a word
    # count can never validate the duration. The hard validation is on the
    # MEASURED narration, in the builder (step 2b) — a script that speaks
    # too short or too long is rewritten and rebuilt, never cut.
    if not (DUR_MIN <= est <= DUR_MAX):
        print(f"  WARNING: script estimate {est:.1f} s outside "
              f"{DUR_MIN}-{DUR_MAX} s — estimate only, the measured "
              f"duration decides")
    assert not re.search(r"[àâéèêëîïôöùûüç]", script), \
        "script contains French accented characters — videos are English only"
    script_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script) if s.strip()]
    assert len(script_sents) >= 4, "script needs at least 4 sentences"
    # HOOK check (Phase 4B, blocking): the first sentence must be short
    # (<= 12 words) AND contain an Arabic digit, a "?", or a spelled-out
    # number word. A "surprising statement" cannot be checked
    # automatically, so the enforceable rule is digit-or-question; a hook
    # that is only a surprising statement must be rephrased to include a
    # number or a question.
    NUMBER_WORDS = {
        "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
        "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
        "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
        "eighty", "ninety", "hundred", "thousand", "million", "billion",
    }
    hook = script_sents[0]
    hook_words = words(hook)
    hook_lower = [w.lower() for w in hook_words]
    hook_has_digit = any(any(ch.isdigit() for ch in w) for w in hook_words)
    hook_has_question = "?" in hook
    hook_has_number_word = any(w in NUMBER_WORDS for w in hook_lower)
    assert len(hook_words) <= 12, (
        f"hook too long ({len(hook_words)} words, max 12): {hook!r}")
    assert hook_has_digit or hook_has_question or hook_has_number_word, (
        f"hook has no digit, no '?', and no spelled-out number word: {hook!r} "
        f"— rephrase the hook to include a number or a question")
    hook_parts = []
    if hook_has_digit:
        hook_parts.append("digit")
    if hook_has_question:
        hook_parts.append("question-mark")
    if hook_has_number_word:
        hook_parts.append("number-word")
    print(f"  hook: PASS ({len(hook_words)} words, "
          f"{', '.join(hook_parts)})")
    # LOOP check (Phase 4B, REPORT-ONLY, never blocking): compare the
    # first and last sentences on shared content words (stopwords
    # stripped). A loop can be a logical continuation with no shared
    # word, so a WARNING only asks for a manual check of the link.
    STOPWORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been",
        "it", "its", "this", "that", "these", "those", "and", "or",
        "but", "so", "to", "of", "in", "on", "for", "with", "by", "at",
        "as", "from", "you", "your", "he", "she", "they", "we", "i",
        "did", "do", "does", "can", "could", "will", "would", "not",
        "no", "still", "just", "very", "more", "than", "then", "when",
        "what", "how", "why", "who", "whom",
    }
    first_content = {w.lower() for w in words(script_sents[0])} - STOPWORDS
    last_content = {w.lower() for w in words(script_sents[-1])} - STOPWORDS
    shared = sorted(first_content & last_content)
    if shared:
        print(f"  LOOP: PASS (shared content words: {', '.join(shared)})")
    else:
        print("  LOOP: WARNING (no shared content word between first and "
              "last sentence — verify the logical link manually)")
    # Traceability (researcher's job, checked by the owner at the stop
    # point): every verified claim must be spoken in the script, in its
    # own terms — the driver cannot judge that, so it only reports the
    # counts here.
    print(f"  script: {len(script_sents)} sentences, hook: {script_sents[0][:60]!r}")
    return script


def stage_storyboard(d: Path, script: str):
    # Phase 4C: beats.json is REQUIRED — one sentence = one title + one
    # distinct image. The strict validator blocks the stage on any
    # violation; --legacy dry-run shows the current storyboard's
    # violations without blocking anything.
    beats_path = d / "beats.json"
    if not beats_path.exists():
        raise SystemExit(
            "beats.json is required (Phase 4C: one sentence = one title + "
            "one distinct image). Write it per the schema in "
            "pipeline/validate-storyboard.py, or run: python3 "
            f"pipeline/validate-storyboard.py --slug {d.name} --legacy to "
            "see the violations of the current storyboard.")
    run([sys.executable, str(PROJECT / "pipeline" / "validate-storyboard.py"),
         "--slug", d.name], cwd=PROJECT)
    text = (d / "storyboard.md").read_text()
    rows = [ln for ln in text.splitlines() if ln.strip().startswith("|")
            and not ln.strip().startswith("| #") and "---" not in ln]
    assert len(rows) >= 4, f"storyboard needs >= 4 scenes, found {len(rows)}"
    motions = set()
    captions, breaks = [], []
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        assert len(cells) >= 5, f"storyboard row incomplete: {row}"
        assert cells[2] and cells[3] and cells[5], \
            f"storyboard scene needs visual + motion + caption: {row}"
        motions.add(cells[3].lower())
        cap = re.sub(r"<[^>]+>", " ", cells[5]).replace("*", "").strip()
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cap) if s.strip()]
        assert sents, f"storyboard scene has an empty caption: {row}"
        captions.extend(sents)
        breaks.append(len(sents))
    assert len(motions) >= 2, "storyboard needs >= 2 distinct motions/animations"
    script_sents = [s.strip() for s in
                    re.split(r"(?<=[.!?])\s+", script.replace("*", "")) if s.strip()]
    # NOTE: "*" is removed (not replaced with a space) on both sides:
    # replacing it with " " left a stray space before the period
    # ("...into  real money ." vs "...into real money."), so a script
    # sentence with *emphasis* never matched its plain caption.
    norm = lambda s: re.sub(r"\s+", " ", s.strip().lower())
    assert [norm(c) for c in captions] == [norm(s) for s in script_sents], \
        ("storyboard captions do not match the script sentences in order — "
         "each scene's caption must be exactly the sentence(s) it speaks")
    print(f"  storyboard: {len(rows)} scenes, {len(motions)} distinct motions, "
          f"scene breaks {breaks}")
    return breaks


def _date_citations(date_str):
    """Date renderings a note may cite for one claim date — without ever
    fabricating a day or month that was not claimed (Phase 4B).
    Claim dates in claims.json come in four forms:
      "undated"    -> None: the claim can never be cited by date
                      (it may still be cited by its source domain).
      "YYYY"       -> ["2004"]: the year alone.
      "YYYY-MM"    -> ["Feb 2025"]: month-year only — never a day.
      "YYYY-MM-DD" -> ["Nov 18, 2025", "Nov 2025"]: full date, and the
                      month-year subset (a month that was claimed).
    Anything else unparseable -> None (skipped, never crashes)."""
    from datetime import date
    if not date_str or str(date_str).strip().lower() == "undated":
        return None
    parts = str(date_str).strip().split("-")
    try:
        if len(parts) == 1:
            return [f"{int(parts[0])}"]
        if len(parts) == 2:
            y, m = map(int, parts)
            return [date(y, m, 1).strftime("%b %Y")]  # "Feb 2025"
        if len(parts) == 3:
            y, m, dd = map(int, parts)
            d = date(y, m, dd)
            return [d.strftime("%b %-d, %Y"),  # "Nov 18, 2025"
                    d.strftime("%b %Y")]       # "Nov 2025"
    except ValueError:
        return None
    return None


def stage_source_notes(d: Path, claims):
    """source-notes.json (optional): every on-screen source note must cite
    a VERIFIED claim in claims.json — the claim's date (in whatever
    precision it was claimed: year, month-year, or full date — see
    _date_citations) or the claim source's domain must appear in the
    note text. A note that cites nothing in claims.json is a false
    attribution waiting to happen (22 Nov 2026: Phase 2 facts notes
    "Feb 2025" / "Apr 2020" leaked into the age-check video on the
    wrong scenes)."""
    from urllib.parse import urlparse
    p = d / "source-notes.json"
    if not p.exists():
        return {}
    notes = json.loads(p.read_text())
    verified = [c for c in claims["claims"] if c["status"] == "verified"]
    for scene, text in notes.items():
        ok = False
        for c in verified:
            domain = urlparse(c["source_url"]).netloc.replace("www.", "")
            if domain and domain in text:
                ok = True
                break
            for cit in (_date_citations(c.get("date")) or []):
                # Word-boundary match so a year ("2004") cannot match
                # inside a longer number.
                if re.search(rf"\b{re.escape(cit)}\b", text):
                    ok = True
                    break
            if ok:
                break
        assert ok, (f"source-notes.json scene {scene}: {text!r} cites no "
                    f"verified claim in claims.json — a source note must "
                    f"come from claims.json")
    print(f"  source notes: {len(notes)} note(s), each citing a verified claim")
    return notes


def top5_pill_heads(values: dict) -> dict:
    """Pill heads from a parsed top5-values.json (Phase 4D).

    Single source of truth for the five visit counts: the same file
    the gate's Top 5 sum check reads, so the numbers the gate checks
    are the numbers rendered. `displayed` is in RANK order [#1..#5];
    pills are in SCENE order (scene 1 = rank #5 ... scene 5 = rank
    #1), so pill-k = displayed[5-k], formatted "36.0B VISITS".
    The displayed sum (311.3 on the v3.1b video) is derived from these
    five values — no element displays it; the announced total ("over
    311 billion") is displayed in the conclusion title via heads.json
    (title-6). Raises ValueError on a malformed file or a sum below
    the announced total (the gate would fail it later; failing here
    saves the voice).
    """
    displayed = values.get("displayed")
    total = values.get("announced_total")
    if (not isinstance(displayed, list) or len(displayed) != 5
            or not all(isinstance(v, (int, float)) for v in displayed)):
        raise ValueError("top5-values.json: 'displayed' must be a list "
                         "of exactly 5 numbers")
    if not isinstance(total, (int, float)):
        raise ValueError("top5-values.json: 'announced_total' must be a number")
    if sum(displayed) < total:
        raise ValueError(
            f"top5-values.json: displayed sum {sum(displayed):.1f} is below "
            f"the announced total {total:.0f} — the gate would fail this")
    return {f"pill-{k}": f"{displayed[5 - k]:.1f}B VISITS"
            for k in range(1, 6)}


def merge_top5_heads(d: Path, heads_dict: dict) -> dict:
    """Derive the pill heads for a top5 build from d/top5-values.json.

    Refuses (SystemExit) if the file is missing — without it the pills
    have no source and the builder would refuse on the surviving
    placeholder after generating the voice — or if heads.json already
    defines a pill-* key (top5-values.json is the single source).
    """
    values_path = d / "top5-values.json"
    if not values_path.exists():
        raise SystemExit(
            f"REFUSED: top5 build needs {values_path} (displayed + "
            f"spoken values + announced total) — the visits pills come "
            f"from that file, never from the template.")
    try:
        pill_heads = top5_pill_heads(json.loads(values_path.read_text()))
    except ValueError as e:
        raise SystemExit(f"REFUSED: {values_path}: {e}")
    clash = sorted(set(pill_heads) & set(heads_dict))
    if clash:
        raise SystemExit(
            f"REFUSED: heads.json defines pill key(s) {clash} — the "
            f"visits pills come only from top5-values.json.")
    return pill_heads


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--format", choices=["mysteries", "facts", "top5",
                                         "hidden-secrets", "game-discoveries",
                                         "updates", "stories"])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--stage", choices=STAGES, default="deliver")
    ap.add_argument("--end-margin", type=float, default=0.85)
    args = ap.parse_args()
    d = PROJECT / "pipeline" / args.slug
    d.mkdir(parents=True, exist_ok=True)
    if args.url:
        (d / "source-url.txt").write_text(args.url.strip() + "\n")
    if args.format:
        (d / "format.txt").write_text(args.format + "\n")
    fmt = args.format or (d / "format.txt").read_text().strip()
    stop = STAGES.index(args.stage)
    print(f"== PIPELINE {args.slug} ({fmt}) — up to stage: {args.stage} ==")

    claims = stage_research(d) if stop >= 0 else None
    script = stage_script(d, claims) if stop >= 1 else None
    breaks = stage_storyboard(d, script) if stop >= 2 else None
    notes = stage_source_notes(d, claims) if stop >= 2 else None
    if stop == 2:
        print("\nSTOP POINT (Step 4): script + claims.json + storyboard are ready.")
        print("Waiting for the owner's green light before voice and render.")
        print(f"  Review: pipeline/{args.slug}/claims.json, script.txt, storyboard.md")
        return 0

    if stop >= 3:
        print("  build: composing (voice generated inside the builder, "
              "duration derived from narration)...")
        # build_video.py --scene-breaks takes CUMULATIVE cut indices
        # (n_scenes-1 values; the last scene takes the remainder), while
        # the storyboard validator returns per-scene sentence COUNTS.
        # Convert: [1,1,1,1,2,2] -> cuts [1,2,3,4,6].
        # Phase 4B: --end-margin defaults to 0.85 s, aiming for the low end
        # of the final-silence range (0.5-0.7 s) as MEASURED on the
        # normalised delivered file. The gate threshold is UNCHANGED
        # (qc.sh default margin 1.0 allows 0.5-1.75 s). 0.6 was tried
        # first (Facts v4 gate run #1): the raw render measured 0.56 s
        # but the normalised file measured 0.45 s — FAIL. Loudnorm's
        # +9.54 dB gain lifts the music-bed fade tail above the silence
        # threshold, so the measured silence shrinks 0.11-0.26 s on
        # normalise (throw-food, margin 1.0, measured 0.74 s). 0.85
        # targets ~0.6-0.7 s measured; the builder must never trim
        # narration to hit it.
        cuts = []
        total = 0
        for c in breaks[:-1]:
            total += c
            cuts.append(total)
        build_cmd = ["python3", "rendering/build_video.py", "--slug", args.slug,
             "--script", script, "--template",
             f"templates/formats/{fmt}.html" if fmt in ("facts", "top5", "mysteries",
                                                      "game-discoveries")
             else "templates/base-vertical/index.html",
             "--scene-breaks", ",".join(map(str, cuts)),
             "--end-margin", str(args.end_margin),
             "--target-min", str(DUR_MIN), "--target-max", str(DUR_MAX)]
        image_map = d / "image-map.json"
        if image_map.exists():
            build_cmd += ["--image-map", image_map.read_text()]
            print(f"  build: image map {image_map} (6 scenes)")
        heads = d / "heads.json"
        heads_dict = {}
        if heads.exists():
            heads_dict = json.loads(heads.read_text())
            print(f"  build: heads {heads} (on-screen titles)")
        if fmt == "top5":
            # Phase 4D: the visits pills come from top5-values.json
            # (single source of truth — the same file the gate's Top 5
            # sum check reads), never from the template. Derived here
            # and merged into --heads; a top5 build without the file
            # fails now, before any voice is generated.
            pill_heads = merge_top5_heads(d, heads_dict)
            heads_dict.update(pill_heads)
            print(f"  build: pills from {d / 'top5-values.json'} "
                  f"({', '.join(pill_heads.values())})")
        if heads_dict:
            build_cmd += ["--heads", json.dumps(heads_dict)]
        src_notes = d / "source-notes.json"
        if src_notes.exists():
            build_cmd += ["--source-notes", src_notes.read_text()]
            print(f"  build: source notes {src_notes} (from claims.json only)")
        run(build_cmd, cwd=PROJECT)
        print("  build: done")
    if stop >= 4:
        print("  draft: rendering...")
        run(["bash", "rendering/render.sh", "--quality", "draft",
             "--composition", f"videos/{args.slug}/index.html",
             "--output", f"output/{args.slug}-draft.mp4"], cwd=PROJECT)
        run(["bash", "quality-control/qc.sh", f"output/{args.slug}-draft.mp4"],
            cwd=PROJECT)
        print("  draft: QC PASS")
    if stop >= 5:
        print("  final: rendering...")
        run(["bash", "rendering/render.sh", "--quality", "standard",
             "--composition", f"videos/{args.slug}/index.html",
             "--output", f"output/{args.slug}.mp4"], cwd=PROJECT)
        print("  final: rendered")
    if stop >= 6:
        print("  normalize: loudness -14 LUFS / 48 kHz...")
        r = run(["python3", "quality-control/normalize-loudness.py", "normalize",
                 f"output/{args.slug}.mp4", f"output/{args.slug}-norm.mp4",
                 "--output", str(d / "loudness.json")], cwd=PROJECT)
        Path(f"output/{args.slug}.mp4").unlink()
        Path(f"output/{args.slug}-norm.mp4").rename(f"output/{args.slug}.mp4")
        print("  normalize: done (see loudness.json for before/after)")
    if stop >= 7:
        print("  gate: running all blocking checks...")
        gate_cmd = ["python3", "quality-control/gate.py",
                    "--mp4", f"output/{args.slug}.mp4",
                    "--metadata", f"videos/{args.slug}/metadata.json",
                    "--format", fmt,
                    "--output", str(d / "gate.json")]
        loud = json.loads((d / "loudness.json").read_text())
        gain = round(loud["after"]["input_i"] - loud["before"]["input_i"], 2)
        gate_cmd += ["--bed-gain-db", str(gain)]
        if fmt == "top5":
            gate_cmd += ["--top5-values", str(d / "top5-values.json")]
        run(gate_cmd, cwd=PROJECT)
        print("  gate: PASS")
    if stop >= 8:
        r = run(["python3", "pipeline/music-attribution.py",
                 "--output", str(d / "attribution.txt")], cwd=PROJECT)
        print("  deliver:")
        print(f"    MP4: output/{args.slug}.mp4")
        print(f"    claims: pipeline/{args.slug}/claims.json")
        print(f"    gate: pipeline/{args.slug}/gate.json")
        print(f"    attribution: {r.stdout.strip()}")
        print("    The owner must listen to the voice before any manual publication.")
        # Phase 4C: generate publish.md from the editorial title, if one
        # was provided. Never invent a title — without
        # publish-title.txt the file is simply not generated.
        title_file = d / "publish-title.txt"
        if title_file.exists():
            title = title_file.read_text().strip().splitlines()[0].strip()
            run(["python3", "pipeline/write-publish-md.py",
                 "--slug", args.slug, "--title", title,
                 "--output", str(d / "publish.md")], cwd=PROJECT)
            print(f"    publish: pipeline/{args.slug}/publish.md")
        else:
            print("    publish.md not generated: no publish-title.txt "
                  "(editorial title required — see "
                  "pipeline/write-publish-md.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
