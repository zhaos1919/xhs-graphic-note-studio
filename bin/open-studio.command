#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$ROOT_DIR/web/studio/index.html" ]; then
  open "$ROOT_DIR/web/studio/index.html"
elif [ -f "$ROOT_DIR/web/studio/simple.html" ]; then
  open "$ROOT_DIR/web/studio/simple.html"
elif [ -f "$ROOT_DIR/web/studio/advanced.html" ]; then
  open "$ROOT_DIR/web/studio/advanced.html"
elif [ -f "$ROOT_DIR/傻瓜一键出图.html" ]; then
  open "$ROOT_DIR/傻瓜一键出图.html"
else
  open "$ROOT_DIR/一键出图操作台.html"
fi
