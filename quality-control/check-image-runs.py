#!/usr/bin/env python3
"""check-image-runs.py — duplicate-image durations + reuse (Phase 4C).

Samples the image-card probe crop (see frame_probe.py) and segments the
video into runs of one image, then checks:

(a) DURATION: any merged image span longer than 5.0 s is a FAIL (a span of
    exactly 5.0 s PASSES — the rule is "more than 5.0 s"). Sampling
    resolution is 0.5 s, so boundary spans carry a +/-0.5 s uncertainty.
(b) REUSE: the same image file under two different integer scene keys in
    metadata.json["images"] is reuse -> FAIL, except the Top 5 outro
    exception (format == "top5" and the reused file's second occurrence
    is the LAST scene and its first occurrence is the immediately
    preceding scene). Keys like "4b" are second shots inside one scene,
    NOT reuse. Without an "images" map, pixel identity is used instead
    (cluster merged spans >= 1.0 s by hist_dist <= 0.15).

Method: sample the card crop every 0.5 s (histogram per frame); segment
into runs with a RUNNING-MEAN reference (a frame joins the current run
if hist_dist(frame, run_mean) <= 0.20, else close the run and start a
new one); then merge runs that are DIRECTLY ADJACENT (end of A ==
start of B) AND hist_dist(mean_A, mean_B) <= 0.15 (this repairs splits
caused by zoom jump-cuts and overlay pops inside one scene). Runs
shorter than 1.0 s are transition fragments — reported but never
counted as images.

Calibration (23 Nov 2026): same image hist_dist ~0.03-0.04, different
images >= 0.24. Expected spans: Facts v4 approx hero 2.0, robot
5.5 + 2.5, scale 7.0, kids 3.0, creator 3.0, platform 9.0 (plus 0.5 s
transition fragments); Mysteries v4 approx shadow 6.0, book 5.5,
glitch 5.5, admin 8.5, legend 7.5.

Usage:
  python3 quality-control/check-image-runs.py --mp4 output/<slug>.mp4 \
      --metadata videos/<slug>/metadata.json [--output JSON]
      [--sample-fps 2] [--join-threshold 0.20] [--merge-threshold 0.15]
      [--max-image-s 5.0] [--format facts|top5|mysteries]

Output: one JSON object on stdout (last line) plus a human summary line.
Exit 0 iff verdict PASS.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame_probe import (extract_frames, hist_dist, rgb_hist64,
                         video_duration)

FRAGMENT_MIN_S = 1.0


def segment_runs(frames, join_threshold):
    """Segment (t, hist) samples into runs with a running-mean reference.

    Returns a list of dicts: {start_s, end_s, n_frames, mean_hist}
    where end_s is exclusive (last frame t + sample dt).
    """
    if not frames:
        return []
    dt = frames[1][0] - frames[0][0] if len(frames) > 1 else 0.5
    runs = []
    cur = {"start_s": frames[0][0], "end_s": frames[0][0] + dt,
           "n_frames": 1, "mean_hist": frames[0][1].copy()}
    for t, hist in frames[1:]:
        if hist_dist(hist, cur["mean_hist"]) <= join_threshold:
            n = cur["n_frames"]
            cur["mean_hist"] = (cur["mean_hist"] * n + hist) / (n + 1)
            cur["n_frames"] = n + 1
            cur["end_s"] = t + dt
        else:
            runs.append(cur)
            cur = {"start_s": t, "end_s": t + dt, "n_frames": 1,
                   "mean_hist": hist.copy()}
    runs.append(cur)
    return runs


def merge_runs(runs, merge_threshold):
    """Merge directly adjacent runs whose mean histograms are close.

    Only consecutive runs with B.start == A.end (within 1 ms) are
    candidates — a transition fragment between two runs of the same
    image keeps them separate spans.
    """
    if not runs:
        return []
    merged = [dict(runs[0])]
    for nxt in runs[1:]:
        last = merged[-1]
        adjacent = abs(nxt["start_s"] - last["end_s"]) <= 0.001 + 1e-9
        if adjacent and hist_dist(last["mean_hist"],
                                  nxt["mean_hist"]) <= merge_threshold:
            n_last, n_nxt = last["n_frames"], nxt["n_frames"]
            last["mean_hist"] = (last["mean_hist"] * n_last
                                 + nxt["mean_hist"] * n_nxt) / (n_last + n_nxt)
            last["n_frames"] = n_last + n_nxt
            last["end_s"] = nxt["end_s"]
        else:
            merged.append(dict(nxt))
    return merged


def detect_format(metadata, cli_format):
    """Format for the outro exception: explicit --format wins, then
    metadata["format"], then the template filename (top5.html -> top5),
    else "facts"."""
    if cli_format:
        return cli_format
    if metadata and metadata.get("format"):
        return str(metadata["format"]).lower()
    template = (metadata or {}).get("template", "") or ""
    m = re.search(r"([a-z0-9]+)\.html$", os.path.basename(template))
    if m:
        return m.group(1).lower()
    return "facts"


def reuse_from_images_map(images, fmt):
    """Reuse from metadata.json["images"]: {scene key -> image file}.

    Returns (reuse_list, outro_exception_applied). Keys like "4b" are
    second shots inside one scene, not reuse. The Top 5 outro
    exception applies only when format == "top5" and the reused file's
    second occurrence is the LAST scene and its first is the scene
    immediately before it.
    """
    by_file = {}
    for key, path in (images or {}).items():
        if not re.fullmatch(r"\d+", str(key)):
            continue
        by_file.setdefault(path, []).append(int(key))
    max_scene = max((int(k) for k in (images or {})
                     if re.fullmatch(r"\d+", str(k))), default=None)
    reuse = []
    exception = False
    for path, scenes in sorted(by_file.items()):
        scenes = sorted(scenes)
        if len(scenes) < 2:
            continue
        if (fmt == "top5" and len(scenes) == 2 and max_scene is not None
                and scenes[1] == max_scene and scenes[0] == max_scene - 1):
            exception = True
            continue
        reuse.append({"image": path, "scenes": scenes})
    return reuse, exception


def reuse_from_pixels(spans, fmt):
    """Pixel fallback: cluster spans >= 1.0 s by hist_dist <= 0.15.

    A cluster whose spans are not consecutive in time is reuse. The
    Top 5 outro exception applies when the cluster's last span is the
    video's last span and its first span is the immediately preceding
    span. Returns (reuse_list, outro_exception_applied).
    """
    big = [(i, s) for i, s in enumerate(spans)
           if s["end_s"] - s["start_s"] >= FRAGMENT_MIN_S]
    clusters = []  # each cluster: list of (span_index, span)
    for idx, span in big:
        placed = False
        for cluster in clusters:
            if hist_dist(span["mean_hist"],
                         cluster[0][1]["mean_hist"]) <= 0.15:
                cluster.append((idx, span))
                placed = True
                break
        if not placed:
            clusters.append([(idx, span)])
    reuse = []
    exception = False
    n_big = len(big)
    for i, cluster in enumerate(clusters):
        if len(cluster) < 2:
            continue
        idx = [c[0] for c in cluster]
        if (fmt == "top5" and len(cluster) == 2
                and idx[1] == n_big - 1 and idx[0] == n_big - 2):
            exception = True
            continue
        reuse.append({"image": f"pixel-cluster-{i}",
                      "scenes": [round(c[1]["start_s"], 2)
                                 for c in cluster]})
    return reuse, exception


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp4", required=True)
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--output")
    ap.add_argument("--sample-fps", type=float, default=2.0)
    ap.add_argument("--join-threshold", type=float, default=0.20)
    ap.add_argument("--merge-threshold", type=float, default=0.15)
    ap.add_argument("--max-image-s", type=float, default=5.0)
    ap.add_argument("--format", default=None)
    args = ap.parse_args()

    duration = video_duration(args.mp4)
    metadata = {}
    if args.metadata and os.path.exists(args.metadata):
        with open(args.metadata) as f:
            metadata = json.load(f)
    fmt = detect_format(metadata, args.format)

    samples = [(t, rgb_hist64(img))
               for t, img in extract_frames(args.mp4, args.sample_fps)]
    runs = segment_runs(samples, args.join_threshold)
    spans = merge_runs(runs, args.merge_threshold)

    span_list = []
    for s in spans:
        d = round(s["end_s"] - s["start_s"], 2)
        span_list.append({
            "start_s": round(s["start_s"], 2),
            "end_s": round(s["end_s"], 2),
            "duration_s": d,
            "n_frames": s["n_frames"],
            "fragment": d < FRAGMENT_MIN_S,
        })
    real_spans = [s for s in span_list if not s["fragment"]]
    max_span = max((s["duration_s"] for s in span_list), default=0.0)
    duration_verdict = ("PASS" if all(s["duration_s"] <= args.max_image_s
                                       for s in real_spans) else "FAIL")

    images = (metadata or {}).get("images")
    if images:
        reuse, exception = reuse_from_images_map(images, fmt)
        method = "images_map"
    else:
        reuse, exception = reuse_from_pixels(spans, fmt)
        method = "pixel_fallback"
    reuse_verdict = "PASS" if not reuse else "FAIL"

    verdict = "PASS" if (duration_verdict == "PASS"
                         and reuse_verdict == "PASS") else "FAIL"
    result = {
        "mp4": str(args.mp4),
        "duration_s": round(duration, 3),
        "sample_fps": args.sample_fps,
        "spans": span_list,
        "max_span_s": max_span,
        "duration_verdict": duration_verdict,
        "reuse": reuse,
        "reuse_verdict": reuse_verdict,
        "reuse_method": method,
        "outro_exception_applied": exception,
        "verdict": verdict,
    }
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
    over = [s for s in real_spans if s["duration_s"] > args.max_image_s]
    print(f"IMAGE RUNS: {verdict} — max span {max_span:.1f} s "
          f"(limit {args.max_image_s:.1f} s), "
          f"{len(real_spans)} image spans, "
          f"{len(reuse)} reuse ({method})"
          + (f", {len(over)} span(s) over limit" if over else "")
          + (", outro exception applied" if exception else ""))
    print(json.dumps(result))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
