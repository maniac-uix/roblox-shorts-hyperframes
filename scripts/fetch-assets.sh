#!/usr/bin/env bash
# fetch-assets.sh — download the binary assets that are NOT stored in git.
# The GitHub snapshot push only accepts UTF-8 text, so binaries live outside
# the repo and are fetched/regenerated locally with this script.
# Usage: bash scripts/fetch-assets.sh
set -u
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$PROJECT_DIR/assets/fonts" "$PROJECT_DIR/assets/music"
FONT_URL="https://fonts.gstatic.com/s/montserrat/v31/JTUSjIg1_i6t8kCHKm459Wlhyw.woff2"
FONT_FILE="$PROJECT_DIR/assets/fonts/Montserrat-Variable.woff2"
if [ -f "$FONT_FILE" ]; then
  echo "Font already present: $FONT_FILE"
else
  echo "Downloading Montserrat (SIL OFL) from Google Fonts..."
  curl -s -o "$FONT_FILE" "$FONT_URL" || { echo "ERROR: font download failed." >&2; exit 1; }
  file "$FONT_FILE"
fi
# Music bed (CC BY 3.0, attribution required — see assets/music/CREDITS.md
# and pipeline/music-attribution.py). URL recorded in config/factory.json.
MUSIC_URL="https://incompetech.com/music/royalty-free/mp3-royaltyfree/Basic%20Implosion.mp3"
MUSIC_FILE="$PROJECT_DIR/assets/music/basic-implosion.mp3"
if [ -f "$MUSIC_FILE" ]; then
  echo "Music already present: $MUSIC_FILE"
else
  echo "Downloading 'Basic Implosion' by Kevin MacLeod (CC BY 3.0)..."
  curl -s -L -o "$MUSIC_FILE" "$MUSIC_URL" || { echo "ERROR: music download failed." >&2; exit 1; }
  file "$MUSIC_FILE"
fi
echo "Done. Voiceover MP3s are NOT downloaded — generate them per video:"
echo "  bash voiceover/generate-voice.sh \"Your script text.\""
echo "Images in assets/images/ are NOT downloaded — generate them per video"
