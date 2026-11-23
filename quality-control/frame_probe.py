#!/usr/bin/env python3
"""frame_probe.py — shared pixel-probe helpers for the ROBLOX VIDEO FACTORY
Phase 4C gate checkers.

Calibrated constants (23 Nov 2026, coordinator calibration — do not re-tune
without reporting why):

- All videos are 1080x1920, 30 fps. Frames are extracted at half scale
  (540x960); every probe coordinate below is given at full scale and at
  half scale.
- PROBE CROP (the image card, "img-wrap", is x 120-960 full scale; its top
  varies by scene, 596-824): full scale x 140-940, y 850-1130;
  half scale (70, 425, 470, 565). The crop sits inside the image for every
  scene of the facts/mysteries templates and avoids the mascot zone
  (x 690-930, y 1134-1374), the source-note zone (below the card), the
  captions (y1520) and the CTA (y1760).
- WATERMARK: text "NoobNoMore", colour #1FD1C1 = (31, 209, 193), top-right
  zone full scale x 630-930, y 145-195 (half scale 315-465, 72-98).
  Pixel presence: RGB distance < 60 from (31, 209, 193). On the v4 videos
  the median count is ~269 px and the glyph bbox height is 9 px at
  half scale (~18 px full scale for a 30 px font, i.e. ~0.6em). The
  blocking size comparison is the DECLARED font-size from the composition
  CSS, threshold >= 36 px — never the pixel-measured height.
- MASCOT: PNG at assets/brand/noobnomore-mascot-transparent.png
  (1600x1600, transparent), rendered 240x240 at (left 690, top 1134) in
  the last scene of the facts/mysteries templates. Masked normalised
  cross-correlation (mask = alpha > 0.5) between the downscaled PNG and
  the frame crop at the composition-declared position: present = 0.953,
  absent = -0.16 / 0.20 on the v4 videos. Threshold 0.5. The blocking
  size comparison is the DECLARED width from the composition CSS,
  threshold >= 220 px.
- EMPTY definition: grey_std of the card crop < 12.0 (calibrated: empty
  frames 5.9-10.1, image frames >= ~17).

Frames are piped from ffmpeg (``-f image2pipe -vcodec mjpeg -``) and
decoded with PIL — no frame files are written. No new dependency:
PIL 10.2.0 + numpy 1.26.4 (system python3), no cv2.
"""
import io
import json
import subprocess

import numpy as np
from PIL import Image

# --- calibrated constants -------------------------------------------------
FULL_W, FULL_H = 1080, 1920
HALF_W, HALF_H = 540, 960

# Probe crop, full scale (x0, y0, x1, y1); half scale (70, 425, 470, 565).
PROBE_CROP_FULL = (140, 850, 940, 1130)
# Watermark zone, full scale; half scale (315, 72, 465, 98).
WATERMARK_ZONE_FULL = (630, 145, 930, 195)
WATERMARK_RGB = (31, 209, 193)
WATERMARK_DIST = 60
# Title band, full scale; half scale (60, 170, 480, 280).
TITLE_BAND_FULL = (120, 340, 960, 560)
TITLE_BRIGHT_LUM = 180
# Empty-image definition (grey stddev of the card crop).
EMPTY_STD_THRESHOLD = 12.0
# Mascot defaults (full scale) when the composition gives no position.
MASCOT_DEFAULT_BOX_FULL = (690, 1134, 240, 240)


def _scale_box(box_full, img_w):
    """Scale a full-scale (x0, y0, x1, y1) box to the image's width."""
    s = img_w / FULL_W
    return (int(round(box_full[0] * s)), int(round(box_full[1] * s)),
            int(round(box_full[2] * s)), int(round(box_full[3] * s)))


def _crop(img, box_full):
    x0, y0, x1, y1 = _scale_box(box_full, img.width)
    return img.crop((x0, y0, x1, y1))


def card_crop(img):
    """Return the probe crop of *img* (a 540x960 or 1080x1920 frame)."""
    return _crop(img, PROBE_CROP_FULL)


def video_duration(mp4: str) -> float:
    """Video duration in seconds (ffprobe, format duration)."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", str(mp4)],
        text=True, capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"ffprobe failed on {mp4}: {r.stderr.strip()}")
    return float(json.loads(r.stdout)["format"]["duration"])


def _split_jpegs(data: bytes):
    """Split concatenated JPEG bytes into individual frames."""
    frames = []
    start = 0
    while True:
        soi = data.find(b"\xff\xd8", start)
        if soi < 0:
            break
        eoi = data.find(b"\xff\xd9", soi + 2)
        if eoi < 0:
            break
        frames.append(data[soi:eoi + 2])
        start = eoi + 2
    return frames


def extract_frames(mp4, fps, scale=(540, 960)):
    """Yield (t_seconds, PIL.Image) sampled at *fps* from *mp4*.

    Frames come from ffmpeg piped as MJPEG (no files written). The fps
    filter emits frames at exact multiples of 1/fps starting at t=0.
    """
    w, h = scale
    cmd = ["ffmpeg", "-v", "error", "-i", str(mp4),
           "-vf", f"scale={w}:{h},fps={fps}",
           "-f", "image2pipe", "-vcodec", "mjpeg", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg failed on {mp4}: {r.stderr.decode(errors='replace').strip()}")
    for i, blob in enumerate(_split_jpegs(r.stdout)):
        img = Image.open(io.BytesIO(blob))
        img.load()
        yield (i / fps, img.convert("RGB"))


def extract_at_times(mp4, times, scale=(540, 960)):
    """Return [(t, PIL.Image)] for exact timestamps *times* (seconds).

    One fast-seek ffmpeg call per timestamp; each call decodes forward
    to the requested time, so the frame is the true frame at that time
    (not the nearest keyframe).
    """
    w, h = scale
    out = []
    for t in times:
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(mp4),
               "-vf", f"scale={w}:{h}", "-frames:v", "1",
               "-f", "image2pipe", "-vcodec", "mjpeg", "-"]
        r = subprocess.run(cmd, capture_output=True)
        blobs = _split_jpegs(r.stdout)
        if r.returncode != 0 or not blobs:
            out.append((t, None))
            continue
        img = Image.open(io.BytesIO(blobs[0]))
        img.load()
        out.append((t, img.convert("RGB")))
    return out


def rgb_hist64(img):
    """4x4x4 RGB histogram (64 bins, normalised) of the card crop."""
    arr = np.asarray(card_crop(img), dtype=np.uint8)
    q = (arr // 64).astype(np.int32)
    idx = q[:, :, 0] * 16 + q[:, :, 1] * 4 + q[:, :, 2]
    hist = np.bincount(idx.ravel(), minlength=64).astype(np.float64)
    total = hist.sum()
    return hist / total if total else hist


def hist_dist(a, b):
    """Histogram distance: 1 - sum(min(a, b)). 0 = same, 1 = different.

    Calibrated: same image ~0.03-0.04, different images >= 0.24.
    """
    return float(1.0 - np.minimum(a, b).sum())


def gray_std(img):
    """Stddev of the grayscale card crop. < 12.0 means "empty"."""
    arr = np.asarray(card_crop(img).convert("L"), dtype=np.float64)
    return float(arr.std())


def watermark_pixels(img):
    """Count of watermark-coloured pixels in the top-right zone.

    A pixel counts when its RGB distance from (31, 209, 193) is < 60.
    Calibrated median on the v4 videos: ~269 px.
    """
    zone = np.asarray(_crop(img, WATERMARK_ZONE_FULL), dtype=np.int32)
    diff = zone - np.array(WATERMARK_RGB, dtype=np.int32)
    dist = np.sqrt((diff * diff).sum(axis=2))
    return int((dist < WATERMARK_DIST).sum())


def watermark_glyph_height(img):
    """BBox height (px, at the frame's scale) of watermark-coloured
    pixels in the top-right zone; 0 when none are present. Evidence
    only — never the blocking size check (see module docstring)."""
    zone = np.asarray(_crop(img, WATERMARK_ZONE_FULL), dtype=np.int32)
    diff = zone - np.array(WATERMARK_RGB, dtype=np.int32)
    dist = np.sqrt((diff * diff).sum(axis=2))
    ys = np.where((dist < WATERMARK_DIST).any(axis=1))[0]
    if len(ys) == 0:
        return 0
    return int(ys.max() - ys.min() + 1)


def mascot_ncc(img, mascot_png, box_full):
    """Masked normalised cross-correlation of the mascot PNG against the
    frame crop at *box_full* (full-scale left, top, width, height).

    The PNG is downscaled to the box size at the frame's scale; the
    mask is alpha > 0.5. Calibrated: present = 0.953, absent = -0.16 /
    0.20; threshold 0.5. Returns 0.0 when the mask is empty or either
    side has zero variance under the mask.
    """
    left, top, width, height = box_full
    s = img.width / FULL_W
    bw, bh = int(round(width * s)), int(round(height * s))
    if bw <= 0 or bh <= 0:
        return 0.0
    x0, y0 = int(round(left * s)), int(round(top * s))
    crop = img.crop((x0, y0, x0 + bw, y0 + bh)).convert("L")
    mascot = Image.open(mascot_png).convert("RGBA").resize(
        (bw, bh), Image.LANCZOS)
    alpha = np.asarray(mascot.split()[3], dtype=np.float64)
    mask = alpha > 127.5
    if mask.sum() < 10:
        return 0.0
    a = np.asarray(mascot.convert("L"), dtype=np.float64)[mask]
    b = np.asarray(crop, dtype=np.float64)[mask]
    a = a - a.mean()
    b = b - b.mean()
    denom = np.sqrt((a * a).sum() * (b * b).sum())
    if denom == 0:
        return 0.0
    return float((a * b).sum() / denom)


def title_bright_px(img):
    """Count of pixels with luminance > 180 in the title band
    (full scale x 120-960, y 340-560). A 108 px title has thousands
    of bright pixels; the calibrated threshold is >= 200 px."""
    band = np.asarray(_crop(img, TITLE_BAND_FULL).convert("L"),
                      dtype=np.float64)
    return int((band > TITLE_BRIGHT_LUM).sum())
