#!/usr/bin/env python3
"""check-top5-sum.py — Top 5 sum consistency (Phase 3 blocking gate).

A Top 5 video announces a total ("over 311 billion visits") and shows +
speaks five values. A viewer adding the numbers must land on the total.
Lesson from Phase 2 v1/v2 (22 Nov 2026): the voice said "45/65/74 billion"
for badges reading 45.5/65.6/74.5 — a viewer adding the spoken numbers got
310, not 311. Fixed by speaking "about 45 and a half billion" etc.

Input JSON (--values): {
  "displayed": [89.7, 74.5, 65.6, 45.5, 36.0],   # the badge values, exact
  "spoken":    [89.7, 74.5, 65.6, 45.5, 36.0],   # the values as spoken
  "announced_total": 311,                        # the number in "over N ..."
  "announced_wording": "over 311 billion visits"
}
Checks (all must pass):
  1. displayed sum >= announced total ("over N" means the sum exceeds N)
  2. spoken sum >= announced total
  3. |displayed sum - spoken sum| <= 1.0 (rounding must not mislead)
  4. exactly 5 values on each side
Exit 0 = PASS, 1 = FAIL. The verdict is authoritative: a FAIL blocks
delivery, no manual override.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--values", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()
    data = json.loads(Path(args.values).read_text())
    displayed = [float(x) for x in data["displayed"]]
    spoken = [float(x) for x in data["spoken"]]
    total = float(data["announced_total"])
    s_d, s_s = sum(displayed), sum(spoken)
    checks = {
        "count": {"verdict": "PASS" if len(displayed) == 5 and len(spoken) == 5 else "FAIL",
                  "value": f"{len(displayed)} displayed, {len(spoken)} spoken (need 5 each)"},
        "displayed_sum_vs_total": {
            "verdict": "PASS" if s_d >= total else "FAIL",
            "value": f"displayed sum {s_d:.1f} >= announced {total:.0f}"},
        "spoken_sum_vs_total": {
            "verdict": "PASS" if s_s >= total else "FAIL",
            "value": f"spoken sum {s_s:.1f} >= announced {total:.0f}"},
        "displayed_vs_spoken": {
            "verdict": "PASS" if abs(s_d - s_s) <= 1.0 else "FAIL",
            "value": f"|{s_d:.1f} - {s_s:.1f}| = {abs(s_d - s_s):.1f} (gate <= 1.0)"},
    }
    overall = "PASS" if all(c["verdict"] == "PASS" for c in checks.values()) else "FAIL"
    for name, c in checks.items():
        print(f"  {name}: {c['verdict']} — {c['value']}")
    print(f"TOP5 SUM CHECK: {overall} ({data.get('announced_wording', '')})")
    report = {"overall": overall, "checks": checks,
              "displayed_sum": round(s_d, 1), "spoken_sum": round(s_s, 1),
              "announced_total": total}
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=1) + "\n")
        print(f"  report saved to {args.output}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
