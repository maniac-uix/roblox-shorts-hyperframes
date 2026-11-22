"""add-second-shot.py — one-off patch for roblox-age-check-explained.

Scene 4 (index 4, 15.02-25.92 s, 10.90 s) shows a single image for more
than 8 s. Adds a second shot at 21.34 s (start of sentence 6, the
twelve-year-old sentence): the bands image crossfades to bands-closeup.

Patch:
  1. copy assets/images/roblox-age-check-explained/bands-closeup.webp
     into the video assets dir
  2. in scene 4's .img-wrap, add <img id="img-4b" ...> after #img-4
     (inline position:relative on that wrap so the absolute img anchors
     to it)
  3. CSS rule for #img-4b (absolute, full-size, opacity 0)
  4. GSAP: at 21.34 s fade #img-4 out (0.4 s) and #img-4b in (0.4 s),
     then Ken Burns on #img-4b for 21.34-25.92 s (4.58 s)
  5. record the second shot in metadata.json
  6. tame the #img-4 Ken Burns: the bands image's age labels sit ~6 px
     from the card's left edge at rest, so the template's 1.00->1.16
     zoom cuts them mid-scene (verified on the draft at 20.9 s:
     "13-15" renders as "3-15"). New tween: scale 1.00->1.02, x +10->+18
     (a slight rightward drift that keeps the labels in frame).

Refuses if the composition does not contain exactly the expected
#img-4 line or if the patch was already applied.
"""
import json
import re
import shutil
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent  # pipeline/ -> project root (moved from .cache-tmp/ 22 Nov 2026: one-off patch for this video, kept so the video is reproducible from the repo)
VIDEO = PROJECT / "videos" / "roblox-age-check-explained"
SRC_IMG = PROJECT / "assets" / "images" / "roblox-age-check-explained" / "bands-closeup.webp"
DST_IMG = VIDEO / "assets" / "images" / "bands-closeup.webp"
SWITCH_AT = 21.34   # start of sentence 6 ("A twelve-year-old...")
SCENE_END = 25.92

html_path = VIDEO / "index.html"
html = html_path.read_text()
assert 'id="img-4b"' not in html, "second shot already applied"

# 1. image
shutil.copyfile(SRC_IMG, DST_IMG)
print(f"copied {SRC_IMG.name} -> {DST_IMG}")

# 2. second img element (wrap gets position:relative so the absolute
#    img anchors to the card, not to the composition root)
old_wrap = ('<div class="img-wrap"><img id="img-4" data-img-scene="4" '
            'src="assets/images/bands.webp" alt="" /></div>')
new_wrap = ('<div class="img-wrap" style="position:relative;"><img id="img-4" '
            'data-img-scene="4" src="assets/images/bands.webp" alt="" />'
            '<img id="img-4b" src="assets/images/bands-closeup.webp" '
            'alt="" /></div>')
assert html.count(old_wrap) == 1, "scene-4 img-wrap not found exactly once"
html = html.replace(old_wrap, new_wrap)

# 3. CSS rule (appended at the end of the style block, before </style>)
css = ('\n      #img-4b { position: absolute; inset: 0; width: 100%; '
       'height: 100%; object-fit: cover; opacity: 0; }\n')
assert "</style>" in html
html = html.replace("</style>", css + "    </style>", 1)

# 4. GSAP tweens: tame the #img-4 Ken Burns first (the bands image's
#    age labels sit ~6 px from the card's left edge at rest, so the
#    template's 1.00->1.16 zoom cuts them mid-scene), then add the
#    crossfade tweens at 21.34 s.
old_tween = ('      tl.fromTo("#img-4", { scale: 1, x: -18 }, '
             '{ scale: 1.16, x: 18, duration: 10.90, ease: "none" }, 15.02);')
tamed_tween = ('      tl.fromTo("#img-4", { scale: 1, x: 10 }, '
               '{ scale: 1.02, x: 18, duration: 10.90, ease: "none" }, 15.02);')
new_tweens = tamed_tween + (
    '\n      tl.fromTo("#img-4", { opacity: 1 }, { opacity: 0, duration: 0.4, ease: "none" }, 21.34);'
    '\n      tl.fromTo("#img-4b", { opacity: 0 }, { opacity: 1, duration: 0.4, ease: "none" }, 21.34);'
    '\n      tl.fromTo("#img-4b", { scale: 1, x: -18 }, { scale: 1.16, x: 18, duration: 4.58, ease: "none" }, 21.34);')
assert html.count(old_tween) == 1, "#img-4 tween not found exactly once"
html = html.replace(old_tween, new_tweens)
html_path.write_text(html)
print("index.html patched: img-4b + CSS + 3 GSAP tweens at 21.34 s; img-4 Ken Burns tamed")

# 5. metadata
meta_path = VIDEO / "metadata.json"
meta = json.loads(meta_path.read_text())
meta["images"]["4b"] = "assets/images/bands-closeup.webp"
meta["secondShots"] = [{
    "scene": 4,
    "atSeconds": SWITCH_AT,
    "image": "assets/images/bands-closeup.webp",
    "reason": "scene 4 lasts 10.90 s (> 8 s) with a single image; "
              "second shot at sentence 6 start",
}]
meta_path.write_text(json.dumps(meta, indent=2))
print("metadata.json: secondShots recorded")
