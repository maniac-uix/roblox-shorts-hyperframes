#!/usr/bin/env python3
"""build_video.py — build a narration-driven HyperFrames composition.

THE FIX for Test 001 (21 Nov 2026): the video duration is DERIVED from the
narration, never the reverse. Steps:

1. Estimate the narration duration from the word count (words / 2.43 w/s).
   If the estimate exceeds --target-max, REFUSE and exit 3: rewrite the
   script before generating the voice. Never cut audio to fit a template.
2. Generate the voice (voiceover/generate-voice.sh) and measure the real
   duration + real end of speech (silencedetect, in <output>.meta.json).
3. video_duration = max(narration + 0.3, last_speech_end + end_margin).
4. Transcribe the narration (local Whisper tiny) for real sentence timings;
   fall back to proportional word-count timing, labelled as estimated.
5. Scale a 10 s template composition to video_duration (all data-start /
   data-duration clips and all GSAP times scale by the same factor), align
   each scene's window AND its GSAP tweens to the sentences it actually
   speaks (scene boundaries from caption timings — uniform scaling alone
   puts the payoff visual ~2 s before its sentence), and replace the
   caption clips with the real sentence timings.
6. Mix the narration padded to exactly video_duration (the padding is only
   the end margin, <= ~1 s) and write videos/<slug>/ + metadata.json.
7. Run `npx hyperframes check` on the built composition.

Scene breaks: --scene-breaks "2,5" means scene 1 speaks sentences 1-2,
scene 2 speaks 3-5, scene 3 speaks 6 (for a 3-scene template). Default:
split the sentences into as many groups as the template has scenes,
cutting nearest to the template's scene proportions.

Emphasis: `*word*` in the script marks a word for on-screen highlight
(<span class="hl">) in the captions. The asterisks are stripped before
TTS, so the spoken script is unchanged.

Images: --image-map '{"0": "assets/images/facts/hero.webp", ...}' maps
scene index -> project-relative image file. Images are copied into
videos/<slug>/assets/images/ and every <img data-img-scene="N"> src is
rewritten to the local copy.

Music: --music (default: config music.track when enabled) mixes a
royalty-free bed under the narration at low volume. The bed ends shortly
after the last spoken word (last_speech + 0.3 s, 0.3 s fade-out) so the
end margin stays true silence and the final-silence QC gate still works.

Usage:
  python3 rendering/build_video.py --slug roblox-facts-older-than-you-think \
      --script "Roblox is older than you think. ..." \
      --template templates/formats/facts.html \
      --target-min 30 --target-max 45 --scene-breaks 1,2,4,5 \
      --image-map '{"0": "assets/images/facts/hero.webp"}'
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
VENV_PY = PROJECT_DIR / ".cache-tmp" / "venv-transcribe" / "bin" / "python"


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw)


def fmt(x: float) -> str:
    return f"{x:.2f}"


def scale_number(m, factor):
    return fmt(float(m.group(1)) * factor)


def caption_html(marked_text: str) -> str:
    """*word* -> <span class="hl">word</span>; bold the first word unless
    the caption starts with a highlighted span."""
    html_text = re.sub(r"\*([^*]+)\*", r'<span class="hl">\1</span>', marked_text)
    if html_text.startswith("<span"):
        return html_text
    first, _, rest = html_text.partition(" ")
    return f"<b>{first}</b> {rest}" if rest else f"<b>{first}</b>"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--template", default="templates/base-vertical/index.html")
    ap.add_argument("--target-min", type=float, default=30.0)
    ap.add_argument("--target-max", type=float, default=45.0)
    ap.add_argument("--end-margin", type=float, default=None)
    ap.add_argument("--scene-breaks", default=None,
                    help='Cumulative sentence counts per scene, e.g. "2,5" '
                         'for 3 scenes speaking sentences 1-2, 3-5, 6. '
                         'Default: proportional split by template scene sizes.')
    ap.add_argument("--image-map", default=None,
                    help='JSON mapping scene index to project-relative image '
                         'path, e.g. \'{"0": "assets/images/facts/hero.webp"}\'')
    ap.add_argument("--music", default=None,
                    help='Royalty-free music bed (project-relative path). '
                         'Default: config music.track when enabled. '
                         'Pass "none" for voice-only.')
    ap.add_argument("--music-volume", type=float, default=None,
                    help='Music bed volume (linear, default from config).')
    args = ap.parse_args()

    config = json.load(open(PROJECT_DIR / "config" / "factory.json"))
    end_margin = args.end_margin if args.end_margin is not None else config["durationPolicy"]["endMarginSeconds"]
    wps_est = config["durationPolicy"]["estimateWordsPerSecond"]
    floor_extra = config["durationPolicy"]["endMarginFloorSeconds"]
    music_cfg = config.get("music", {})
    if args.music == "none":
        music_path = None
    elif args.music:
        music_path = (Path(args.music) if Path(args.music).is_absolute()
                      else PROJECT_DIR / args.music)
    elif music_cfg.get("enabled"):
        music_path = PROJECT_DIR / music_cfg["track"]
    else:
        music_path = None
    music_volume = (args.music_volume if args.music_volume is not None
                    else music_cfg.get("volume", 0.04))
    if music_path is not None and not music_path.exists():
        print(f"WARNING: music bed not found: {music_path} — building voice-only")
        music_path = None

    # Emphasis markers (*word*) are for captions only — strip before TTS.
    clean_script = args.script.replace("*", "")
    marked_sentences = [s.strip() for s in
                        re.split(r"(?<=[.!?])\s+", args.script) if s.strip()]

    words = clean_script.split()
    n_words = len(words)
    estimate = n_words / wps_est
    print(f"script: {n_words} words | estimated narration: {estimate:.1f} s "
          f"(target {args.target_min:.0f}-{args.target_max:.0f} s)")
    if estimate > args.target_max:
        print(f"REFUSED: estimated narration {estimate:.1f} s exceeds target max "
              f"{args.target_max:.0f} s. Rewrite the script shorter BEFORE "
              f"generating the voice — audio is never cut to fit a template.")
        return 3
    if estimate < args.target_min:
        print(f"NOTE: estimated narration {estimate:.1f} s is below target min "
              f"{args.target_min:.0f} s — the video will be shorter than the "
              f"target. Duration is derived from the narration, not forced.")

    out_dir = PROJECT_DIR / "videos" / args.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    narration = out_dir / "narration.mp3"

    # 2. Generate + measure the voice.
    run(["bash", str(PROJECT_DIR / "voiceover" / "generate-voice.sh"),
         clean_script, "--output", str(narration)])
    meta = json.load(open(out_dir / "narration.meta.json"))
    dur = meta["durationSeconds"]
    last_speech = meta["lastSpeechEndSeconds"]
    real_wps = meta["wordsPerSecond"]
    print(f"narration measured: {dur:.2f} s | words: {meta['words']} | "
          f"wps: {real_wps} | last speech ends: {last_speech:.2f} s | "
          f"trailing silence: {meta['trailingSilenceSeconds']:.2f} s")

    # 3. Derive the video duration from the narration.
    video_duration = max(dur + floor_extra, last_speech + end_margin)
    video_duration = round(video_duration, 2)
    print(f"video duration = max({dur:.2f}+{floor_extra}, {last_speech:.2f}+{end_margin}) "
          f"= {video_duration:.2f} s (end margin {end_margin} s)")

    # 4. Real sentence timings from Whisper; fallback = proportional.
    transcript_path = out_dir / "transcript.json"
    captions, captions_source = [], "estimated"
    if VENV_PY.exists():
        r = subprocess.run(
            [str(VENV_PY), str(PROJECT_DIR / "quality-control" / "transcribe.py"),
             "--input", str(narration), "--output", str(transcript_path),
             "--language", "en"],
            text=True, capture_output=True)
        if r.returncode == 0:
            t = json.load(open(transcript_path))
            captions_source = "whisper"
            # Group by SCRIPT sentences (exact text), timed by Whisper words:
            # sentence k gets the start of its first word and the end of its
            # last word. This keeps caption text identical to the script
            # (Whisper word timestamps often drop sentence punctuation).
            # "text" is the clean sentence (for transcript comparison);
            # "html" is the marked sentence with *emphasis* -> <span class="hl">.
            #
            # ALIGNMENT (fixed 22 Nov 2026, v3.1 sync gate): the sentences
            # are mapped to Whisper words by FUZZY alignment (lexicon +
            # number forms + character tolerance), not by word count.
            # Count-based slicing drifted whenever Whisper's word count
            # differed from the script's — "Brainrot" heard as "brain rod"
            # (2 words) shifted every later caption 1-2 s early (top5 and
            # mysteries v3: captions appeared up to 2.08 s before the words
            # they show). See quality-control/check-sync.py.
            sys.path.insert(0, str(PROJECT_DIR / "quality-control"))
            from caption_timing import corrected_captions, script_sentences as split_sentences
            sentences = split_sentences(clean_script)
            wlist = t["words"]
            timings = corrected_captions(clean_script, wlist)
            for k, s in enumerate(sentences):
                marked = marked_sentences[k] if k < len(marked_sentences) else s
                start, end = timings[k]
                if start is None:
                    # No aligned word for this sentence (Whisper dropped
                    # it entirely) — fall back to the neighbours' midpoint.
                    prev_end = captions[-1]["end"] if captions else 0.0
                    start = end = prev_end
                    print(f"WARNING: no Whisper words aligned for sentence {k+1} "
                          f"({s[:40]!r}) — caption timed at previous end")
                captions.append({"text": s,
                                 "html": caption_html(marked),
                                 "start": start, "end": end})
            print(f"captions: {len(captions)} sentences from Whisper timings (fuzzy aligned)")
            for c in captions:
                print(f"  [{c['start']:.2f}-{c['end']:.2f}] {c['text']}")
        else:
            print("WARNING: Whisper transcription failed, falling back to "
                  "proportional caption timing:", r.stderr[-300:])
    if not captions:
        # Proportional fallback: split script into sentences, share duration
        # by word count. Explicitly labelled as estimated.
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_script) if s.strip()]
        total_w = sum(len(s.split()) for s in sentences)
        t = 0.0
        for k, s in enumerate(sentences):
            share = len(s.split()) / total_w * dur
            marked = marked_sentences[k] if k < len(marked_sentences) else s
            captions.append({"text": s, "html": caption_html(marked),
                             "start": round(t, 2), "end": round(t + share, 2)})
            t += share
        print("captions: proportional timing (ESTIMATED, no Whisper)")

    # 5. Scale the template composition.
    template_path = PROJECT_DIR / args.template
    html = template_path.read_text()
    m_root = re.search(r'data-duration="([0-9.]+)"', html)
    template_duration = float(m_root.group(1)) if m_root else 10.0
    factor = video_duration / template_duration
    print(f"template duration: {template_duration:.2f} s | scale factor: {factor:.3f} "
          f"(narration {dur:.2f} s vs template {template_duration:.2f} s — "
          f"this is the longer-than-template test case)" if dur > template_duration
          else f"template duration: {template_duration:.2f} s | scale factor: {factor:.3f}")

    # 5a. Scale every data-start / data-duration clip window.
    html = re.sub(r'data-start="([0-9.]+)"',
                  lambda m: f'data-start="{fmt(float(m.group(1)) * factor)}"', html)
    html = re.sub(r'data-duration="([0-9.]+)"',
                  lambda m: f'data-duration="{fmt(float(m.group(1)) * factor)}"', html)
    # 5b. Scale GSAP times inside the <script> block only.
    def scale_script(match):
        block = match.group(0)
        block = re.sub(r'duration:\s*([0-9.]+)',
                       lambda m: f"duration: {fmt(float(m.group(1)) * factor)}", block)
        block = re.sub(r'stagger:\s*([0-9.]+)',
                       lambda m: f"stagger: {fmt(float(m.group(1)) * factor)}", block)
        block = re.sub(r'},\s*([0-9.]+)\)',
                       lambda m: f"}}, {fmt(float(m.group(1)) * factor)})", block)
        return block
    html = re.sub(r"<script>.*?</script>", scale_script, html, flags=re.DOTALL)
    # 5c. Composition id + timeline key: the template registers its timeline
    # under its own id AND marks the root with data-composition-id — both
    # must change together (a mismatch is a hard lint error).
    m_id = re.search(r'data-composition-id="([^"]+)"', html)
    if m_id:
        old_id = m_id.group(1)
        html = html.replace(f'data-composition-id="{old_id}"',
                            f'data-composition-id="{args.slug}"')
        html = html.replace(f'window.__timelines["{old_id}"]',
                            f'window.__timelines["{args.slug}"]')
    # 5c2. Assets: the template references ../../assets/, which traverses
    # above the composition folder (hard lint error). Copy the font into the
    # video dir so every path stays inside the composition folder.
    font_src = PROJECT_DIR / "assets" / "fonts" / "Montserrat-Variable.woff2"
    font_dst = out_dir / "assets" / "fonts" / "Montserrat-Variable.woff2"
    if font_src.exists():
        font_dst.parent.mkdir(parents=True, exist_ok=True)
        font_dst.write_bytes(font_src.read_bytes())
        html = html.replace("../../assets/", "assets/")
    # 5c3. Images: --image-map maps scene index -> project-relative image.
    # Copy each image into the video dir and rewrite the <img
    # data-img-scene="N"> src to the local copy.
    copied_images = {}
    if args.image_map:
        image_map = json.loads(args.image_map)
        for scene_idx, src_rel in image_map.items():
            src = PROJECT_DIR / src_rel
            if not src.exists():
                print(f"WARNING: image not found, scene {scene_idx}: {src_rel}")
                continue
            dst = out_dir / "assets" / "images" / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            copied_images[str(scene_idx)] = f"assets/images/{src.name}"
            print(f"image scene {scene_idx}: {src_rel} -> {dst.relative_to(PROJECT_DIR)}")

        def repl_img(m):
            new_src = copied_images.get(m.group(2))
            return m.group(1) + new_src + m.group(3) if new_src else m.group(0)
        html = re.sub(r'(<img[^>]*data-img-scene="(\d+)"[^>]*src=")[^"]*(")',
                      repl_img, html)
        unmapped = [m.group(1) for m in
                    re.finditer(r'data-img-scene="(\d+)"', html)
                    if m.group(1) not in copied_images]
        if unmapped:
            print(f"WARNING: scenes without an image (placeholder kept): {unmapped}")
    # 5d. Audio source (relative to the composition folder).
    html = re.sub(r'(<audio[^>]*src=")[^"]*(")',
                  r'\1narration-mix.mp3\2', html)
    html = html.replace("FACTORY TEST 001", args.slug.upper().replace("-", " "))
    # 5d. Replace caption clips (track-index 3) with real sentence timings.
    # Caption text is the marked sentence rendered as HTML (*word* -> hl
    # span, first word bold). Captions sit at y1520, below the image zone.
    caption_divs = []
    for c in captions:
        cap_dur = max(0.5, c["end"] - c["start"])
        caption_divs.append(
            f'<div class="clip" data-start="{fmt(c["start"])}" '
            f'data-duration="{fmt(cap_dur)}" data-track-index="3" '
            f'style="left:120px; top:1520px;">'
            f'<p class="caption">{c["html"]}</p></div>')
    new_captions = "\n      ".join(caption_divs)
    html2, n_sub = re.subn(
        r'<div class="clip" data-start="[^"]*" data-duration="[^"]*" '
        r'data-track-index="3"[^>]*>.*?</div>',
        new_captions, html, count=1, flags=re.DOTALL)
    if n_sub:
        html = html2
        print(f"captions replaced: {len(captions)} clips ({captions_source} timings)")
    else:
        print("WARNING: no track-index 3 caption div found in template — "
              "captions NOT replaced; check the template.")

    # 5e. Scene alignment: uniform scaling puts the payoff visual ~2 s
    # before its sentence (scenes are even thirds, sentences are not).
    # Re-time each scene window AND its GSAP tweens to the sentences the
    # scene actually speaks. Full-duration tweens (progress, glows) keep
    # the global scaling — they belong to no scene.
    scene_pat = re.compile(
        r'<div class="scene clip" data-start="([0-9.]+)" '
        r'data-duration="([0-9.]+)" data-track-index="2">(.*?)</div>\s*</div>',
        re.DOTALL)
    scene_divs = list(scene_pat.finditer(html))
    if scene_divs and captions:
        n_scenes = len(scene_divs)
        # Group sentences into scenes.
        if args.scene_breaks:
            breaks = [int(x) for x in args.scene_breaks.split(",")]
            assert len(breaks) == n_scenes - 1, \
                f"--scene-breaks needs {n_scenes - 1} values for {n_scenes} scenes"
            assert breaks[-1] < len(captions), "--scene-breaks exceeds sentence count"
            groups = []
            prev = 0
            for b in breaks:
                groups.append(captions[prev:b])
                prev = b
            groups.append(captions[prev:])
        else:
            # Proportional split nearest to the template's scene sizes.
            old_bounds = [(float(m.group(1)), float(m.group(1)) + float(m.group(2)))
                          for m in scene_divs]
            groups, prev = [], 0
            for k in range(n_scenes - 1):
                cut = old_bounds[k][1] / video_duration * dur
                best, best_d = prev, None
                for j in range(prev, len(captions)):
                    d = abs(captions[j]["end"] - cut)
                    if best_d is None or d < best_d:
                        best, best_d = j, d
                groups.append(captions[prev:best + 1])
                prev = best + 1
            groups.append(captions[prev:])
        # New scene boundaries: scene k starts at 0 or at the end of the
        # previous group's last caption; it ends at its last caption's end,
        # except the last scene, which runs to the video end.
        new_bounds = []
        for k, g in enumerate(groups):
            start = 0.0 if k == 0 else groups[k - 1][-1]["end"]
            end = video_duration if k == n_scenes - 1 else g[-1]["end"]
            new_bounds.append((start, end))
        # id -> scene index, from the element ids inside each scene div.
        id_to_scene = {}
        for k, m in enumerate(scene_divs):
            for eid in re.findall(r'id="([^"]+)"', m.group(3)):
                id_to_scene[eid] = k

        def scene_map(k, t):
            (a, b), (a2, b2) = ((float(scene_divs[k].group(1)),
                                float(scene_divs[k].group(1)) + float(scene_divs[k].group(2))),
                               new_bounds[k])
            f = (b2 - a2) / (b - a) if b > a else 1.0
            return a2 + (t - a) * f, f

        # Rewrite the scene clip windows (in order).
        def repl_scene(m, it=iter(new_bounds)):
            s, e = next(it)
            return (f'<div class="scene clip" data-start="{fmt(s)}" '
                    f'data-duration="{fmt(e - s)}" data-track-index="2">'
                    f'{m.group(3)}</div>\n      </div>')
        html = scene_pat.sub(lambda m: repl_scene(m), html, count=n_scenes)

        # Re-time GSAP tweens whose target id belongs to a scene.
        def scale_durations(vars_text, f):
            return re.sub(r'duration:\s*([0-9.]+)',
                          lambda mm: f"duration: {fmt(float(mm.group(1)) * f)}",
                          vars_text)

        def repl_tween(m):
            kind, target = m.group(1), m.group(2)
            k = id_to_scene.get(target.lstrip("#"))
            if k is None:
                return m.group(0)
            pos = float(m.group(5))
            new_pos, f = scene_map(k, pos)
            if kind == "fromTo":
                v1 = scale_durations(m.group(3), f)
                v2 = scale_durations(m.group(4), f)
                return (f'tl.fromTo("{target}", {v1}, {v2}, {fmt(new_pos)})')
            v1 = scale_durations(m.group(3), f)
            return f'tl.to("{target}", {v1}, {fmt(new_pos)})'

        def scale_script2(match):
            block = match.group(0)
            # One pattern for both shapes: tl.fromTo("#id", {...}, {...}, POS)
            # and tl.to("#id", {...}, POS). Group 4 is None for tl.to.
            return re.sub(
                r'tl\.(fromTo|to)\("([^"]+)",\s*(\{[^}]*\})'
                r'(?:,\s*(\{[^}]*\}))?,\s*([0-9.]+)\)',
                repl_tween, block)
        html = re.sub(r"<script>.*?</script>", scale_script2, html, flags=re.DOTALL)
        print("scene alignment:")
        for k, (s, e) in enumerate(new_bounds):
            print(f"  scene {k + 1}: {s:.2f}-{e:.2f} s "
                  f"(sentences: {' | '.join(c['text'][:28] for c in groups[k])})")

    comp_path = out_dir / "index.html"
    comp_path.write_text(html)

    # 6. Mix narration padded to exactly video_duration (margin only).
    # With a music bed: the bed plays at low volume and ends shortly after
    # the last spoken word (last_speech + 0.3 s, 0.3 s fade-out), so the end
    # margin stays true silence and the final-silence QC gate still works.
    mix = out_dir / "narration-mix.mp3"
    if music_path is not None:
        music_end = round(last_speech + 0.3, 2)
        fc = (f"[0:a]apad,atrim=0:{video_duration}[a0];"
              f"[1:a]atrim=0:{music_end},"
              f"afade=t=out:st={music_end - 0.3:.2f}:d=0.3,"
              f"volume={music_volume}[a1];"
              f"[a0][a1]amix=inputs=2:normalize=0[aout]")
        run(["ffmpeg", "-y", "-v", "error", "-i", str(narration),
             "-i", str(music_path), "-filter_complex", fc,
             "-map", "[aout]", str(mix)])
        print(f"music bed: {music_path.relative_to(PROJECT_DIR)} "
              f"volume {music_volume} (ends {music_end:.2f} s, "
              f"0.3 s fade-out)")
    else:
        run(["ffmpeg", "-y", "-v", "error", "-i", str(narration),
             "-af", f"apad,atrim=0:{video_duration}", str(mix)])
    mix_dur = float(run(["ffprobe", "-v", "error", "-show_entries",
                         "format=duration", "-of", "csv=p=0", str(mix)]).stdout.strip())
    added_silence = round(video_duration - dur, 2)
    print(f"audio mix: {mix_dur:.2f} s (narration {dur:.2f} s + "
          f"{added_silence:.2f} s end margin — no other silence added)")
    assert abs(mix_dur - video_duration) < 0.1, "mix duration mismatch"

    # Metadata.
    metadata = {
        "slug": args.slug,
        "script": clean_script,
        "template": args.template,
        "templateDurationSeconds": template_duration,
        "scaleFactor": round(factor, 3),
        "targetSeconds": [args.target_min, args.target_max],
        "estimatedNarrationSeconds": round(estimate, 2),
        "narration": meta,
        "videoDurationSeconds": video_duration,
        "endMarginSeconds": end_margin,
        "addedSilenceSeconds": added_silence,
        "captions": captions,
        "captionsSource": captions_source,
        "images": copied_images,
        "music": ({
            "track": str(music_path.relative_to(PROJECT_DIR)),
            "volume": music_volume,
            "endsAtSeconds": round(last_speech + 0.3, 2),
            "license": music_cfg.get("license", ""),
        } if music_path is not None else None),
        "composition": str(comp_path.relative_to(PROJECT_DIR)),
        "audioMix": str(mix.relative_to(PROJECT_DIR)),
        "qc": "pending",
    }
    json.dump(metadata, open(out_dir / "metadata.json", "w"), indent=1)

    # 7. HyperFrames check on the built composition (check takes the
    # composition's directory as a positional argument).
    # NOTE: `hyperframes check` exits 1 even on a clean report when the
    # directory is not a registered project root — so judge by the JSON
    # report (ok + errorCount), not by the exit code.
    print("--- hyperframes check ---")
    r = subprocess.run(["npx", "hyperframes", "check", "--json",
                        str(out_dir.relative_to(PROJECT_DIR))],
                       cwd=PROJECT_DIR, text=True, capture_output=True)
    print(r.stdout[-1500:])
    # Judge by the SAVED report file (authoritative): the check prints
    # "report saved to <path>.json" (on stderr). The stdout also embeds
    # summary JSON fragments whose "ok" fields are sub-objects, not the verdict.
    combined = r.stdout + "\n" + r.stderr
    m_rep = re.search(r"report saved to (\S+\.json)", combined)
    ok_flag, err_count = None, None
    if m_rep:
        try:
            rep = json.load(open(m_rep.group(1)))
            ok_flag = rep.get("ok")
            err_count = rep.get("lint", {}).get("errorCount")
        except Exception as e:
            print("could not read check report:", e)
    if ok_flag is True and err_count == 0:
        print("hyperframes check: ok (0 errors)")
    else:
        print(r.stderr[-1000:])
        print(f"hyperframes check FAILED: ok={ok_flag}, errors={err_count}")
        return 1
    print(f"BUILT: {comp_path} ({video_duration:.2f} s) — ready to render:")
    print(f"  bash rendering/render.sh --quality draft --composition "
          f"videos/{args.slug}/index.html --output output/{args.slug}-draft.mp4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
