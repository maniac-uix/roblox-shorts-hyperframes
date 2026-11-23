#!/usr/bin/env python3
"""validate-storyboard.py — storyboard validator for the Phase 4C
one-sentence = one-visual-beat model, plus a legacy dry-run mode.

STRICT mode (default, beats.json present):
  beats.json schema:
    {"format": "<format>",
     "beats": [{"phrase": "<script sentence, asterisks stripped>",
                "titre": "<on-screen title for this sentence>",
                "image": "assets/images/<...>.webp",
                "duree": <seconds, float>,
                "scene": <int, 0-based>}]}
  One beat per script sentence, in order. Validates:
    (a) beats' phrases, normalized, equal the script sentences in order
    (b) every beat has a non-empty titre
    (c) every beat's titre shares a content word with its phrase
        (same match rule as quality-control/check-title-sentence.py)
    (d) every beat's image file exists under the project root
    (e) every beat's duree is > 0 and <= 5.0 s (an image is shown at
        most 5.0 s consecutively)
    (f) NO image reused across different scenes — EXCEPT the Top 5
        outro exception: if format == "top5", the beats of the LAST
        scene may reuse the image of the immediately preceding scene
        (the #1 reveal); any other reuse is a violation
    (g) the first beat passes the hook rule (same as
        quality-control/check-hook.py: <= 12 words AND a digit, a "?"
        or a spelled-out number word)

LEGACY mode (--legacy): for existing storyboards WITHOUT beats.json.
  Derives beats from pipeline/<slug>/storyboard.md (table rows: scene
  index, on-screen text column, caption column with one or more
  sentences) + pipeline/<slug>/image-map.json (scene -> image file)
  + pipeline/<slug>/heads.json (scene -> title text, when present)
  + videos/<slug>/metadata.json captions (sentence start/end for
  duree) + metadata.json secondShots (a second shot splits a scene's
  image at the shot time — the later sentences of that scene use the
  second-shot image). Then runs the SAME checks (b)-(g) on the derived
  beats (skips (a) — the storyboard captions already matched the
  script when the video was built — but DOES check that every derived
  beat has a title and a distinct image). Image existence in legacy
  mode accepts the project root (image-map paths) AND the video folder
  (second-shot paths, which metadata.json records in video-folder
  form assets/images/<basename>); strict mode accepts the project
  root only. In legacy mode check (e)
  applies to each image's CONSECUTIVE display span (scene windows
  from videos/<slug>/index.html when present, else derived from the
  caption timings), since one image covers a whole multi-sentence
  scene there.

Usage:
  validate-storyboard.py --slug <slug> [--beats pipeline/<slug>/beats.json]
      [--output report.json]
  validate-storyboard.py --slug <slug> --legacy [--output report.json]

Exit 0 iff no violations, else 1. The JSON report is the last stdout line.
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
PIPELINE = PROJECT / "pipeline"
VIDEOS = PROJECT / "videos"
QC = PROJECT / "quality-control"
MAX_IMAGE_S = 5.0


# --- shared matchers (imported from the gate checkers when possible) ---
def _load_qc_module(filename: str, modname: str):
    spec = importlib.util.spec_from_file_location(
        modname, QC / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    _cts = _load_qc_module("check-title-sentence.py", "check_title_sentence")
    match_title_sentence = _cts.match_title_sentence
except Exception:  # fallback: duplicate of the checker's matcher
    _STOP = {"a", "an", "the", "is", "are", "was", "were", "be", "been",
             "it", "its", "this", "that", "these", "those", "and", "or",
             "but", "so", "to", "of", "in", "on", "for", "with", "by",
             "at", "as", "from", "you", "your", "he", "she", "they",
             "we", "i", "did", "do", "does", "can", "could", "will",
             "would", "not", "no", "still", "just", "very", "more",
             "than", "then", "when", "what", "how", "why", "who", "whom"}
    _NUM = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
            "six": "6", "seven": "7", "eight": "8", "nine": "9",
            "ten": "10", "eleven": "11", "twelve": "12",
            "thirteen": "13", "fourteen": "14", "fifteen": "15",
            "sixteen": "16", "seventeen": "17", "eighteen": "18",
            "nineteen": "19", "twenty": "20", "thirty": "30",
            "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
            "eighty": "80", "ninety": "90"}

    def _tok(text):
        return [_NUM.get(t, t) for t in
                re.findall(r"[a-z0-9]+", text.lower().replace("*", " "))
                if t not in _STOP]

    def match_title_sentence(title, sentence):  # noqa: F811
        tt, st = _tok(title), _tok(sentence)
        shared = []
        for t in tt:
            for s in st:
                if t == s or (len(max(t, s, key=len)) >= 4
                              and max(t, s, key=len).startswith(
                                  min(t, s, key=len))):
                    w = t if len(t) <= len(s) else s
                    if w not in shared:
                        shared.append(w)
                    break
        return bool(shared), shared


try:
    _chk = _load_qc_module("check-hook.py", "check_hook")
    check_hook_sentence = _chk.check_hook_sentence
except Exception:  # fallback: duplicate of the checker's hook rule
    _NUMWORDS = {"one", "two", "three", "four", "five", "six", "seven",
                 "eight", "nine", "ten", "eleven", "twelve", "thirteen",
                 "fourteen", "fifteen", "sixteen", "seventeen",
                 "eighteen", "nineteen", "twenty", "thirty", "forty",
                 "fifty", "sixty", "seventy", "eighty", "ninety",
                 "hundred", "thousand", "million", "billion"}

    def check_hook_sentence(sentence):  # noqa: F811
        ws = re.findall(r"[A-Za-z0-9']+", sentence)
        low = [w.lower() for w in ws]
        has_digit = any(any(c.isdigit() for c in w) for w in ws)
        has_q = "?" in sentence
        has_nw = any(w in _NUMWORDS for w in low)
        ok = len(ws) <= 12 and (has_digit or has_q or has_nw)
        return {"first_sentence": sentence, "n_words": len(ws),
                "has_digit": has_digit, "has_question": has_q,
                "has_number_word": has_nw,
                "verdict": "PASS" if ok else "FAIL"}


def split_sentences(text: str) -> list:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip())
            if s.strip()]


def normalize_phrase(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("*", "").strip().lower())


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def check_beats(beats: list, fmt: str, script_sents=None,
                check_duree=True, image_bases=None) -> list:
    """Checks (b)-(g) on a list of beat dicts (phrase/titre/image/duree/
    scene). Returns a violations list of {beat, check, detail}.
    check_duree=False skips the per-beat duree check (legacy mode: a
    derived beat's duree is its sentence's spoken duration, not an
    image display time — the image-span check covers (e) there).
    image_bases: directories an image path may resolve against
    (default: the project root only). Legacy mode also accepts the
    video folder, because metadata.json records second-shot images in
    video-folder form (assets/images/<basename>, copied there by
    second-shot.py) while image-map images are project-root form
    (assets/images/<format>/<basename>) — a single-base check would
    false-flag the second shots. Strict mode keeps the default:
    beats.json is validated before any video folder exists, so its
    paths must resolve at the project root."""
    violations = []
    bases = image_bases if image_bases is not None else (PROJECT,)
    for i, b in enumerate(beats):
        phrase, titre = b.get("phrase", ""), b.get("titre", "")
        if not titre or not str(titre).strip():
            violations.append({"beat": i, "check": "titre",
                               "detail": "missing or empty titre"})
        elif phrase:
            ok, _ = match_title_sentence(str(titre), phrase)
            if not ok:
                violations.append(
                    {"beat": i, "check": "titre-match",
                     "detail": f"titre {str(titre)!r} shares no content "
                               f"word with phrase {phrase[:60]!r}"})
        image = b.get("image", "")
        if not image:
            violations.append({"beat": i, "check": "image",
                               "detail": "missing image"})
        elif not any((base / image).exists() for base in bases):
            violations.append({"beat": i, "check": "image",
                               "detail": f"image file not found: {image}"})
        duree = b.get("duree")
        if check_duree and (duree is None
                            or not isinstance(duree, (int, float))):
            violations.append({"beat": i, "check": "duree",
                               "detail": f"duree missing or not a number: "
                                         f"{duree!r}"})
        elif check_duree and not (0 < duree <= MAX_IMAGE_S):
            violations.append(
                {"beat": i, "check": "duree",
                 "detail": f"duree {duree} s outside (0, {MAX_IMAGE_S}] s"})
    # (f) image reuse across different scenes
    by_image = {}
    for i, b in enumerate(beats):
        if b.get("image"):
            by_image.setdefault(b["image"], []).append(i)
    max_scene = max((b.get("scene", 0) for b in beats), default=0)
    for image, idxs in by_image.items():
        scenes = sorted({beats[i].get("scene", 0) for i in idxs})
        if len(scenes) > 1:
            allowed = (fmt == "top5" and scenes == [max_scene - 1, max_scene])
            if not allowed:
                violations.append(
                    {"beat": idxs, "check": "image-reuse",
                     "detail": f"image {image} reused across scenes "
                               f"{scenes} (beats {idxs})"})
    # (g) hook on the first beat
    if beats and beats[0].get("phrase"):
        hook = check_hook_sentence(beats[0]["phrase"])
        if hook["verdict"] != "PASS":
            violations.append(
                {"beat": 0, "check": "hook",
                 "detail": f"first sentence fails the hook rule "
                           f"({hook['n_words']} words, digit="
                           f"{hook['has_digit']}, ?={hook['has_question']}, "
                           f"number-word={hook['has_number_word']}): "
                           f"{beats[0]['phrase'][:80]!r}"})
    return violations


def validate_strict(slug: str, beats_path: Path) -> dict:
    d = PIPELINE / slug
    script = (d / "script.txt").read_text().strip()
    script_sents = split_sentences(script.replace("*", ""))
    data = json.loads(beats_path.read_text())
    fmt = data.get("format", "")
    beats = data.get("beats", [])
    violations = []
    # (a) phrases equal the script sentences in order
    norm_beats = [normalize_phrase(b.get("phrase", "")) for b in beats]
    norm_script = [normalize_phrase(s) for s in script_sents]
    if len(norm_beats) != len(norm_script):
        violations.append({"beat": None, "check": "phrases",
                           "detail": f"{len(norm_beats)} beats but "
                                     f"{len(norm_script)} script sentences"})
    else:
        for i, (pb, ps) in enumerate(zip(norm_beats, norm_script)):
            if pb != ps:
                violations.append(
                    {"beat": i, "check": "phrases",
                     "detail": f"beat phrase {beats[i].get('phrase', '')[:60]!r} "
                               f"!= script sentence {script_sents[i][:60]!r}"})
    violations += check_beats(beats, fmt, script_sents)
    return {"slug": slug, "mode": "strict", "format": fmt,
            "n_beats": len(beats), "beats": beats,
            "violations": violations,
            "verdict": "PASS" if not violations else "FAIL"}


def _scene_windows_from_composition(slug: str, n_scenes: int):
    """Scene windows [(start, end)] from videos/<slug>/index.html, or
    None if the composition is missing."""
    comp = VIDEOS / slug / "index.html"
    if not comp.exists():
        return None
    html = comp.read_text()
    windows = []
    for m in re.finditer(r'<div[^>]*class="scene clip"[^>]*>', html):
        tag = m.group(0)
        s = re.search(r'data-start="([0-9.]+)"', tag)
        du = re.search(r'data-duration="([0-9.]+)"', tag)
        if s and du:
            windows.append((float(s.group(1)),
                            float(s.group(1)) + float(du.group(1))))
    return windows if len(windows) == n_scenes else None


def validate_legacy(slug: str) -> dict:
    d = PIPELINE / slug
    meta = json.loads((VIDEOS / slug / "metadata.json").read_text())
    captions = meta.get("captions", [])
    # storyboard.md rows
    rows = [ln for ln in (d / "storyboard.md").read_text().splitlines()
            if ln.strip().startswith("|") and "---" not in ln
            and not ln.strip().startswith("| #")]
    scenes = []  # {scene, titre_md, sentences}
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        scene = int(cells[0]) - 1
        cap = strip_html(cells[5]).replace("*", "").strip()
        scenes.append({"scene": scene,
                       "titre_md": strip_html(cells[4]).replace("*", ""),
                       "sentences": split_sentences(cap)})
    scenes.sort(key=lambda s: s["scene"])
    # heads.json: element id -> text; numeric suffix = scene index
    heads = {}
    heads_path = d / "heads.json"
    if heads_path.exists():
        for key, val in json.loads(heads_path.read_text()).items():
            m = re.match(r"(title|head)-(\d+)$", key)
            if m:
                scene = int(m.group(2))
                # title-k wins over head-k for the same scene
                if key.startswith("title-") or scene not in heads:
                    heads[scene] = strip_html(str(val))
    # image-map.json: scene (str) -> image file
    image_map = {}
    image_map_path = d / "image-map.json"
    if image_map_path.exists():
        image_map = {int(k): v for k, v in
                     json.loads(image_map_path.read_text()).items()}
    # captions in order == flattened storyboard sentences in order
    flat = [s for sc in scenes for s in sc["sentences"]]
    cap_by_norm = {normalize_phrase(c["text"]): c for c in captions}
    timed = []
    if len(flat) == len(captions):
        timed = list(captions)
    else:
        for s in flat:
            timed.append(cap_by_norm.get(normalize_phrase(s)))
    # second shots: {scene: [(at, image)]}
    shots = {}
    for sh in meta.get("secondShots", []):
        shots.setdefault(int(sh["scene"]), []).append(
            (float(sh["atSeconds"]), sh["image"]))
    # scene windows (composition if present, else caption-derived)
    windows = _scene_windows_from_composition(slug, len(scenes))
    if windows is None:
        # caption-derived: scene starts at the previous scene's last
        # caption end (0.0 for scene 0), ends at its last caption end
        windows = []
        idx = 0
        prev_end = 0.0
        for sc in scenes:
            n = len(sc["sentences"])
            chunk = timed[idx:idx + n]
            idx += n
            ends = [float(c["end"]) for c in chunk if c is not None]
            end = max(ends) if ends else prev_end
            windows.append((prev_end, end))
            prev_end = end
    # derived beats, one per sentence
    beats = []
    idx = 0
    for si, sc in enumerate(scenes):
        scene = sc["scene"]
        titre = heads.get(scene) or sc["titre_md"]
        for s in sc["sentences"]:
            cap = timed[idx] if idx < len(timed) else None
            idx += 1
            start = float(cap["start"]) if cap else windows[si][0]
            end = float(cap["end"]) if cap else windows[si][1]
            image = image_map.get(scene)
            for at, img in sorted(shots.get(scene, [])):
                if start >= at:
                    image = img
            beats.append({"phrase": s, "titre": titre, "image": image,
                          "duree": round(end - start, 2), "scene": scene,
                          "start_s": round(start, 2),
                          "end_s": round(end, 2)})
    fmt = (d / "format.txt").read_text().strip() if (d / "format.txt").exists() else ""
    # (b)-(d), (f), (g) on the derived beats; (e) is the image-span
    # check below, not the per-sentence duree. Image existence accepts
    # the project root (image-map paths) AND the video folder
    # (second-shot paths, video-folder form) — see check_beats.
    violations = check_beats(beats, fmt, check_duree=False,
                             image_bases=(PROJECT, VIDEOS / slug))
    # legacy (e): consecutive display span per image (scene windows +
    # second-shot splits), not the per-sentence duree
    segments = []  # (image, start, end, scenes)
    for si, sc in enumerate(scenes):
        scene = sc["scene"]
        w_start, w_end = windows[si]
        cuts = sorted([at for at, _ in shots.get(scene, [])])
        bounds = [w_start] + [c for c in cuts if w_start < c < w_end] + [w_end]
        imgs = [image_map.get(scene)]
        for at, img in sorted(shots.get(scene, [])):
            if w_start < at < w_end:
                imgs.append(img)
        for j in range(len(bounds) - 1):
            segments.append((imgs[j], bounds[j], bounds[j + 1], {scene}))
    merged = []
    for seg in segments:
        if merged and merged[-1][0] == seg[0] \
                and abs(merged[-1][2] - seg[1]) < 0.01:
            merged[-1] = (seg[0], merged[-1][1], seg[2],
                          merged[-1][3] | seg[3])
        else:
            merged.append(list(seg))
    for image, s0, s1, scs in merged:
        span = round(s1 - s0, 2)
        if span > MAX_IMAGE_S:
            violations.append(
                {"beat": None, "check": "duree",
                 "detail": f"image {image} shown {span} s consecutively "
                           f"(scenes {sorted(scs)}, {s0:.2f}–{s1:.2f} s) "
                           f"> {MAX_IMAGE_S} s"})
    return {"slug": slug, "mode": "legacy", "format": fmt,
            "n_beats": len(beats), "beats": beats,
            "image_segments": [{"image": i, "start_s": round(a, 2),
                                "end_s": round(b, 2),
                                "span_s": round(b - a, 2),
                                "scenes": sorted(s)}
                               for i, a, b, s in merged],
            "violations": violations,
            "verdict": "PASS" if not violations else "FAIL"}


def _print_report(report: dict):
    beats = report["beats"]
    print(f"storyboard ({report['mode']}): {report['slug']} — "
          f"{len(beats)} beats, {len(report['violations'])} violation(s) "
          f"— {report['verdict']}")
    print(f"  {'#':>3} {'sc':>2}  {'phrase':<46} {'titre':<30} "
          f"{'image':<28} {'dur':>5}")
    for i, b in enumerate(beats):
        print(f"  {i:>3} {b.get('scene', '?'):>2}  "
              f"{b.get('phrase', '')[:46]:<46} "
              f"{str(b.get('titre', ''))[:30]:<30} "
              f"{str(b.get('image', ''))[13:][:28]:<28} "
              f"{b.get('duree', '?'):>5}")
    if report.get("image_segments"):
        print("  image segments (consecutive display):")
        for seg in report["image_segments"]:
            flag = "OVER 5.0 s" if seg["span_s"] > MAX_IMAGE_S else "ok"
            print(f"    {seg['image']:<32} scenes {seg['scenes']} "
                  f"{seg['start_s']:.2f}–{seg['end_s']:.2f} s "
                  f"({seg['span_s']:.2f} s) {flag}")
    if report["violations"]:
        print("  violations:")
        for v in report["violations"]:
            print(f"    beat {v['beat']} [{v['check']}] {v['detail']}")
    else:
        print("  no violations")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--beats")
    ap.add_argument("--legacy", action="store_true")
    ap.add_argument("--output")
    args = ap.parse_args()
    if args.legacy:
        report = validate_legacy(args.slug)
    else:
        beats_path = Path(args.beats) if args.beats else \
            PIPELINE / args.slug / "beats.json"
        if not beats_path.exists():
            print(f"beats.json not found: {beats_path} — write it per the "
                  f"schema in this file, or run with --legacy to see the "
                  f"violations of the current storyboard.", file=sys.stderr)
            return 1
        report = validate_strict(args.slug, beats_path)
    _print_report(report)
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
