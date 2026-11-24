#!/usr/bin/env python3
"""second-shot.py — parameterized second-shot patch (Phase 4B).

A scene that holds two thematically different sentences gets a second
image mid-scene: the first image crossfades to the second at a given
time (usually the start of the second sentence). Same technique as the
age-check video's one-off patch (pipeline/add-second-shot.py), but
parameterized so any video can use it.

Patch (applied to videos/<slug>/index.html AFTER build_video.py, BEFORE
the draft render — a later rebuild regenerates index.html, so re-apply
after any rebuild):
  1. copy --image into the video assets dir
  2. in scene N's .img-wrap, add <img id="img-Nb" ...> after #img-N
     (inline position:relative on that wrap so the absolute img anchors
     to it). A scene that already has a second shot gets a third shot
     <img id="img-Nc"> (Facts v5 scene 5: three images in one scene —
     the scene window is 9.2 s, two images cannot both stay under the
     5.0 s gate limit once the scene starts at the previous sentence's
     end and the crossfade blend is counted)
  3. CSS rule for #img-Nb (absolute, full-size, opacity 0)
  4. GSAP: at --at fade #img-N out (0.4 s) and #img-Nb in (0.4 s),
     then Ken Burns on #img-Nb for --at to --end
  5. record the second shot in metadata.json

With the Phase 4B 3-segment zoom, #img-N has three segment tweens; the
ones after --at keep running on the (now invisible) first image —
harmless, no change needed.

Usage:
  python3 pipeline/second-shot.py --slug roblox-facts-older-than-you-think-v4 \\
      --scene 4 --at 24.70 --end 28.66 \\
      --image assets/images/facts/creator.webp \\
      --reason "scene 4: kids figure then DevEx sentence; switch at S8 start"
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--scene", type=int, required=True)
    ap.add_argument("--at", type=float, required=True,
                    help="switch time in seconds (final video time)")
    ap.add_argument("--end", type=float, required=True,
                    help="scene end in seconds (final video time)")
    ap.add_argument("--image", required=True,
                    help="project-relative image path, e.g. assets/images/facts/creator.webp")
    ap.add_argument("--reason", default="")
    args = ap.parse_args()

    video = PROJECT / "videos" / args.slug
    html_path = video / "index.html"
    meta_path = video / "metadata.json"
    assert html_path.exists(), f"no built composition: {html_path}"
    assert meta_path.exists(), f"no metadata.json: {meta_path}"
    src_img = PROJECT / args.image
    assert src_img.exists(), f"image not found: {src_img}"
    assert args.end > args.at, "--end must be after --at"

    html = html_path.read_text()
    # First free suffix: "b" for a second shot, "c" for a third shot in
    # the same scene (a scene whose window exceeds ~8.6 s needs three
    # images to keep every span under the 5.0 s gate limit).
    nb = None
    suffix_used = None
    for suffix in ("b", "c"):
        cand = f"img-{args.scene}{suffix}"
        if f'id="{cand}"' not in html:
            nb = cand
            suffix_used = suffix
            break
    assert nb is not None, f"scene {args.scene} already has shots b and c"

    # 1. image
    dst_img = video / "assets" / "images" / src_img.name
    shutil.copyfile(src_img, dst_img)
    print(f"copied {src_img.name} -> {dst_img.relative_to(PROJECT)}")

    # 2. extra img element: insert before the closing </div> of the
    # img-wrap that holds #img-N (the wrap may already contain a
    # second-shot img).
    wrap_pat = re.compile(
        r'(<div class="img-wrap"[^>]*><img id="img-' + str(args.scene) +
        r'"[^>]*/>.*?</div>)', re.DOTALL)
    m = wrap_pat.search(html)
    assert m, f"scene {args.scene} img-wrap not found exactly once"
    # Keep the original wrap verbatim, inject the new img before
    # </div> (the wrap gets position:relative so the absolute img
    # anchors to the card, not to the composition root).
    orig = m.group(1)
    new_wrap = orig[:-len("</div>")] + (f'<img id="{nb}" src="assets/images/{src_img.name}" '
                        f'alt="" /></div>')
    if 'style="position:relative;"' not in new_wrap:
        new_wrap = new_wrap.replace('<div class="img-wrap"',
                                    '<div class="img-wrap" style="position:relative;"', 1)
    html = html.replace(orig, new_wrap, 1)
    print(f"img-wrap scene {args.scene}: added #{nb} ({src_img.name})")

    # 3. CSS rule
    css = (f'\n      #{nb} {{ position: absolute; inset: 0; width: 100%; '
           f'height: 100%; object-fit: cover; opacity: 0; }}\n')
    assert "</style>" in html
    html = html.replace("</style>", css + "    </style>", 1)

    # 4. GSAP tweens (final time — appended after scene alignment).
    at, end = args.at, args.end
    dur = round(end - at, 2)
    tweens = (
        f'      tl.fromTo("#img-{args.scene}", {{ opacity: 1 }}, '
        f'{{ opacity: 0, duration: 0.4, ease: "none" }}, {at:.2f});\n'
        f'      tl.fromTo("#{nb}", {{ opacity: 0 }}, '
        f'{{ opacity: 1, duration: 0.4, ease: "none" }}, {at:.2f});\n'
        f'      tl.fromTo("#{nb}", {{ scale: 1, x: -18 }}, '
        f'{{ scale: 1.16, x: 18, duration: {dur:.2f}, ease: "none" }}, {at:.2f});\n')
    assert "      window.__timelines[" in html
    html = html.replace("      window.__timelines[",
                        tweens + "      window.__timelines[", 1)

    # If a shot added earlier in this scene fades in AFTER this shot's
    # --at, it must also fade this new image out: the new img is last
    # in DOM order (topmost), so without the fade-out it would stay
    # visible over the later shot.
    fade_in_pat = re.compile(
        r'tl\.fromTo\("#img-' + str(args.scene) + r'[bc]", '
        r'\{ opacity: 0 \}, \{ opacity: 1, duration: 0\.4, '
        r'ease: "none" \}, (\d+\.\d+)\);')
    for m2 in fade_in_pat.finditer(html):
        at2 = float(m2.group(1))
        if at2 > at:
            fade_out = (f'      tl.fromTo("#{nb}", {{ opacity: 1 }}, '
                        f'{{ opacity: 0, duration: 0.4, ease: "none" }}, {at2:.2f});\n')
            html = html.replace(m2.group(0), fade_out + m2.group(0), 1)
            print(f"index.html: #{nb} also fades out at {at2:.2f} s "
                  f"(later shot in scene {args.scene})")
    html_path.write_text(html)
    print(f"index.html patched: #{nb} crossfade at {at:.2f} s, "
          f"Ken Burns {dur:.2f} s to {end:.2f} s")

    # 5. metadata
    meta = json.loads(meta_path.read_text())
    meta.setdefault("images", {})[f"{args.scene}{suffix_used}"] = f"assets/images/{src_img.name}"
    meta.setdefault("secondShots", []).append({
        "scene": args.scene,
        "atSeconds": at,
        "endSeconds": end,
        "image": f"assets/images/{src_img.name}",
        "reason": args.reason,
    })
    meta_path.write_text(json.dumps(meta, indent=1))
    print("metadata.json: secondShots recorded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
