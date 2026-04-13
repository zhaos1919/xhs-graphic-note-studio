#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

clear

choose_action() {
  /usr/bin/osascript <<'APPLESCRIPT'
set options to {"选择单个 JSON 出图", "选择整个文件夹批量出图", "打开输出目录", "打开 JSON 目录", "打开 AI 模板"}
tell application "System Events"
  activate
  set picked to choose from list options with prompt "请选择你要做的事：" default items {"选择单个 JSON 出图"}
end tell
if picked is false then
  return ""
end if
return item 1 of picked
APPLESCRIPT
}

pick_json_file() {
  /usr/bin/osascript <<'APPLESCRIPT'
tell application "System Events"
  activate
  set pickedFile to choose file with prompt "请选择一个 JSON 文件："
end tell
return POSIX path of pickedFile
APPLESCRIPT
}

pick_json_folder() {
  /usr/bin/osascript <<'APPLESCRIPT'
tell application "System Events"
  activate
  set pickedFolder to choose folder with prompt "请选择一个包含 JSON 的文件夹："
end tell
return POSIX path of pickedFolder
APPLESCRIPT
}

open_target() {
  /usr/bin/open "$1"
  exit 0
}

if [ "$#" -gt 0 ]; then
  cd "$ROOT_DIR/xhs-render"
  python3 "$ROOT_DIR/xhs-render/easy_render_cli.py" "$@"
  exit $?
fi

ACTION="$(choose_action)"

case "$ACTION" in
  "选择单个 JSON 出图")
    TARGET="$(pick_json_file)"
    ;;
  "选择整个文件夹批量出图")
    TARGET="$(pick_json_folder)"
    ;;
  "打开输出目录")
    mkdir -p "$ROOT_DIR/xhs-render/output"
    open_target "$ROOT_DIR/xhs-render/output"
    ;;
  "打开 JSON 目录")
    if [ -d "$ROOT_DIR/json" ]; then
      open_target "$ROOT_DIR/json"
    else
      osascript -e 'display alert "未找到 JSON 目录" message "当前项目里没有找到 json 文件夹。" as warning'
      exit 1
    fi
    ;;
  "打开 AI 模板")
    open_target "$ROOT_DIR/xhs-render/ai_json_prompt_template.txt"
    ;;
  *)
    exit 0
    ;;
esac

if [ -z "${TARGET:-}" ]; then
  exit 0
fi

cd "$ROOT_DIR/xhs-render"
python3 "$ROOT_DIR/xhs-render/easy_render_cli.py" "$TARGET"
