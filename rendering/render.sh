#!/usr/bin/env bash
# render.sh — the ONLY supported way to render in this project.
# Sets the safe temporary paths (never /tmp), checks free memory, refuses a
# second heavy render in parallel, and always renders draft before final.
#
# Usage:
#   bash rendering/render.sh [--quality draft|standard] \
#     [--composition index.html] [--output output/factory-test.mp4]
set -u
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUALITY="standard"
COMPOSITION="index.html"
OUTPUT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --quality) QUALITY="$2"; shift 2 ;;
    --composition) COMPOSITION="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

[ -z "$OUTPUT" ] && OUTPUT="output/factory-test-${QUALITY}.mp4"
case "$OUTPUT" in /*) ;; *) OUTPUT="$PROJECT_DIR/$OUTPUT" ;; esac
case "$COMPOSITION" in /*) ;; *) COMPOSITION="$PROJECT_DIR/$COMPOSITION" ;; esac

# --- Safe temporary paths (audit: /tmp is a 512 MB tmpfs, renders fail there)
export TMPDIR="$PROJECT_DIR/.cache-tmp/tmp"
export HYPERFRAMES_EXTRACT_CACHE_DIR="$PROJECT_DIR/.cache-tmp/frames"
mkdir -p "$TMPDIR" "$HYPERFRAMES_EXTRACT_CACHE_DIR" "$(dirname "$OUTPUT")"

# --- Memory gate
MEM_AVAIL_MB=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
if [ "$MEM_AVAIL_MB" -lt 500 ]; then
  echo "ERROR: only ${MEM_AVAIL_MB} MB free memory (< 500 MB). Do not render now." >&2
  exit 1
fi
echo "Memory available: ${MEM_AVAIL_MB} MB — OK"

# --- Single-render lock (never two heavy renders at once)
LOCK_DIR="$PROJECT_DIR/.cache-tmp/render.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "ERROR: another render is already running (lock: $LOCK_DIR)." >&2
  exit 1
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

# --- Draft-before-final rule
if [ "$QUALITY" = "standard" ] && [ ! -f "$PROJECT_DIR/output/factory-test-draft.mp4" ] \
   && [ "$OUTPUT" = "$PROJECT_DIR/output/factory-test-standard.mp4" ]; then
  echo "NOTE: no draft render found for the factory test — rendering draft first."
  bash "$PROJECT_DIR/rendering/render.sh" --quality draft \
    --composition "$COMPOSITION" --output "$PROJECT_DIR/output/factory-test-draft.mp4" || exit 1
  echo "Draft done. Run QC on it before the final render:"
  echo "  bash quality-control/qc.sh output/factory-test-draft.mp4"
fi

echo "Rendering: $COMPOSITION"
echo "  quality=$QUALITY  output=$OUTPUT"
echo "  TMPDIR=$TMPDIR"
cd "$PROJECT_DIR" && npx hyperframes render \
  --quality "$QUALITY" \
  --composition "$COMPOSITION" \
  --output "$OUTPUT" \
  --frames-cache-dir "$HYPERFRAMES_EXTRACT_CACHE_DIR"
STATUS=$?
if [ "$STATUS" -ne 0 ]; then echo "ERROR: render failed (exit $STATUS)." >&2; exit "$STATUS"; fi
ls -lh "$OUTPUT"
echo "Render complete: $OUTPUT"
