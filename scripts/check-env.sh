#!/usr/bin/env bash
# check-env.sh — verify the ROBLOX VIDEO FACTORY environment.
# Usage: bash scripts/check-env.sh
# Exits 0 only when every required check passes. Warnings do not fail.
set -u
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL=0

check() { # check <name> <command...>
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "  PASS  $name"; else echo "  FAIL  $name"; FAIL=1; fi
}

echo "ROBLOX VIDEO FACTORY — environment check"
echo "Project: $PROJECT_DIR"
echo

echo "[1] Runtimes"
node --version 2>/dev/null | sed 's/^/  Node: /'
check "Node.js >= 22" bash -c 'node -e "process.exit(process.versions.node.split(\".\")[0] >= 22 ? 0 : 1)"'
check "npm available" command -v npm
check "npx available" command -v npx
check "FFmpeg available" command -v ffmpeg
check "FFprobe available" command -v ffprobe
ffmpeg -version 2>/dev/null | head -1 | sed 's/^/  FFmpeg: /'

echo "[2] HyperFrames"
check "hyperframes CLI installed" bash -c "cd \"$PROJECT_DIR\" && npx --no-install hyperframes --version"
check "hyperframes.json present" test -f "$PROJECT_DIR/hyperframes.json"
check "config/factory.json present" test -f "$PROJECT_DIR/config/factory.json"
if command -v npx >/dev/null 2>&1; then
  (cd "$PROJECT_DIR" && npx hyperframes doctor 2>&1 | grep -E "Chrome|FFmpeg|Memory" | sed 's/^/  doctor: /')
fi

echo "[3] Cloud limits (audit, 21 Nov 2026)"
MEM_AVAIL_MB=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
echo "  Memory available: ${MEM_AVAIL_MB} MB (need >= 500 MB before a render)"
if [ "$MEM_AVAIL_MB" -lt 500 ]; then echo "  FAIL  Free memory < 500 MB — do not render now"; FAIL=1; else echo "  PASS  Free memory OK"; fi
TMP_FREE_MB=$(df -m /tmp 2>/dev/null | awk 'NR==2 {print $4}')
echo "  /tmp free: ${TMP_FREE_MB} MB (tmpfs 512 MB — NEVER use /tmp for renders)"
echo "  Workspace free: $(df -h "$PROJECT_DIR" | awk 'NR==2 {print $4}')"
check "Safe TMPDIR exists" test -d "$PROJECT_DIR/.cache-tmp/tmp"
check "Safe frames cache exists" test -d "$PROJECT_DIR/.cache-tmp/frames"
check "No render lock held" bash -c "test ! -d \"$PROJECT_DIR/.cache-tmp/render.lock\""

echo "[4] Permissions quirk (HyperFrames refuses group-writable ~/.cache and ~)"
# Group-writable means the group digit of the mode has the write bit (2).
# NOTE (21 Nov 2026): ~ reverted to 2770 between the audit and this build,
# probably on VM replacement — so this check must run every session.
if python3 -c "import os,sys; sys.exit(0 if (os.stat(os.path.expanduser('~')).st_mode & 0o020 or os.stat(os.path.expanduser('~/.cache')).st_mode & 0o020) else 1)"; then
  echo "  FAIL  ~ or ~/.cache is group-writable — HyperFrames will refuse its Chrome cache."
  echo "        Fix (reversible): chmod go-w ~/.cache ~   then re-run this check."
  FAIL=1
else
  echo "  PASS  ~ and ~/.cache permissions OK (not group-writable)"
fi

echo
if [ "$FAIL" -eq 0 ]; then echo "RESULT: environment OK — safe to render"; else echo "RESULT: environment NOT OK — fix the FAIL lines above"; fi
exit "$FAIL"
