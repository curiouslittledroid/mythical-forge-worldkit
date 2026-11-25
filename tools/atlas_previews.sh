#!/bin/bash
# Render a PNG preview of every atlas SVG (macOS + Google Chrome).
# Usage: tools/atlas_previews.sh
set -euo pipefail
cd "$(dirname "$0")/.."
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [ ! -x "$CHROME" ]; then
  echo "Google Chrome not found at $CHROME" >&2
  exit 1
fi
mkdir -p maps/svg/preview
for svg in maps/svg/*.svg; do
  name=$(basename "$svg" .svg)
  # the page size in mm, scaled to about 1,270 px on the long edge
  read -r w h < <(python3 - "$svg" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r'width="(\d+)mm" height="(\d+)mm"', s)
print(m.group(1), m.group(2))
PY
)
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=0.4 \
    --window-size=$((w * 38 / 10)),$((h * 38 / 10)) \
    --screenshot="$PWD/maps/svg/preview/$name.png" \
    "file://$PWD/maps/svg/$name.svg" >/dev/null 2>&1
  echo "wrote maps/svg/preview/$name.png"
done
