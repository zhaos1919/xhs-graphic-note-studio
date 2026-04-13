from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from styles import STYLE_PRESETS, init_styles


SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN_RE = re.compile(r"\n|[A-Za-z0-9_]+|[^\S\n]+|.", re.UNICODE)
TAG_RE = re.compile(r"^(【[^】]+】)(.*)$")
INVALID_PATH_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1F]+')
WHITESPACE_RE = re.compile(r"\s+")
ALLOWED_TYPES = {"auto", "list", "compare", "tag"}
OUTPUT_MANIFEST_NAME = ".xhs-render-output.json"
STYLE_ALIASES = {
    "banxia": "banxia",
    "半夏": "banxia",
    "半夏风格": "banxia",
    "rifu": "rifu",
    "日富": "rifu",
    "日富风格": "rifu",
    "日富一日新": "rifu",
    "richu": "rifu",
}


@dataclass
class FlowLine:
    indent: int
    segments: List[Tuple[str, ImageFont.FreeTypeFont]]


@lru_cache(maxsize=None)
def find_font(bold: bool) -> Path:
    family_queries = [
        "Noto Serif CJK SC",
        "Source Han Serif SC",
    ]
    style_name = "Bold" if bold else "Regular"
    fc_match = shutil.which("fc-match")
    if fc_match:
        for family in family_queries:
            result = subprocess.run(
                [fc_match, "-f", "%{file}\n", f"{family}:style={style_name}"],
                capture_output=True,
                text=True,
                check=False,
            )
            candidate = result.stdout.strip()
            if candidate:
                path = Path(candidate)
                if path.exists():
                    return path

    home = Path.home()
    font_dirs = [
        home / "Library" / "Fonts",
        Path("/Library/Fonts"),
        Path("/Library/Fonts/Supplemental"),
        Path("/System/Library/Fonts"),
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        home / ".fonts",
        home / ".local" / "share" / "fonts",
        Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts",
        Path("C:/Windows/Fonts"),
    ]
    patterns = [
        f"*Noto*Serif*CJK*SC*{style_name}*",
        f"*NotoSerifCJKsc*{style_name}*",
        f"*Source*Han*Serif*SC*{style_name}*",
        f"*SourceHanSerifSC*{style_name}*",
    ]

    for font_dir in font_dirs:
        if not font_dir.exists():
            continue
        # 没有 fc-match 时，直接扫常见字体目录，兼容 macOS / Windows / Linux。
        for pattern in patterns:
            matches = sorted(font_dir.rglob(pattern))
            for match in matches:
                if match.is_file():
                    return match

    install_hint = (
        "未找到 Noto Serif CJK SC / 思源宋体字体。"
        "请先安装后再运行：macOS 可执行 `brew install font-noto-serif-cjk-sc`，"
        "Windows 可从 Google Fonts 下载并安装。"
    )
    raise RuntimeError(install_hint)


@lru_cache(maxsize=None)
def load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(font_path, size=size)


@lru_cache(maxsize=None)
def load_fitted_background(bg_path: str, width: int, height: int) -> Image.Image:
    with Image.open(bg_path) as image:
        image = image.convert("RGB")
        return ImageOps.fit(
            image,
            (width, height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )


def tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text)


def trim_trailing_spaces(
    segments: Sequence[Tuple[str, ImageFont.FreeTypeFont]]
) -> List[Tuple[str, ImageFont.FreeTypeFont]]:
    cleaned = [(text, font) for text, font in segments if text]
    while cleaned:
        text, font = cleaned[-1]
        stripped = text.rstrip()
        if stripped:
            cleaned[-1] = (stripped, font)
            break
        cleaned.pop()
    return cleaned


def layout_segments(
    segments: Sequence[Tuple[str, ImageFont.FreeTypeFont]],
    maxw: int,
    first_indent: int = 0,
    rest_indent: int = 0,
) -> List[FlowLine]:
    # 把多段不同字重的文本统一流式排版，后续 draw_mixed / 悬挂缩进都复用这里。
    lines: List[FlowLine] = []
    line_segments: List[Tuple[str, ImageFont.FreeTypeFont]] = []
    line_width = 0.0
    current_indent = first_indent

    def append_piece(text: str, font: ImageFont.FreeTypeFont) -> None:
        nonlocal line_width
        if not text:
            return
        if line_segments and line_segments[-1][1] == font:
            prev_text, _ = line_segments[-1]
            line_segments[-1] = (prev_text + text, font)
        else:
            line_segments.append((text, font))
        line_width += float(font.getlength(text))

    def flush(force_blank: bool = False) -> None:
        nonlocal line_segments, line_width, current_indent
        cleaned = trim_trailing_spaces(line_segments)
        if cleaned or force_blank:
            lines.append(FlowLine(indent=current_indent, segments=cleaned))
        line_segments = []
        line_width = 0.0
        current_indent = rest_indent

    def push_token(token: str, font: ImageFont.FreeTypeFont) -> None:
        nonlocal current_indent
        if token == "\n":
            flush(force_blank=True)
            return

        if token.isspace() and not line_segments:
            return

        available = max(maxw - current_indent, 1)
        token_width = float(font.getlength(token))
        if line_width + token_width <= available + 0.01:
            append_piece(token, font)
            return

        if line_segments:
            flush()
            if token.isspace():
                return
            available = max(maxw - current_indent, 1)
            token_width = float(font.getlength(token))
            if token_width <= available + 0.01:
                append_piece(token, font)
                return

        if len(token) == 1:
            append_piece(token, font)
            return

        for char in token:
            push_token(char, font)

    for text, font in segments:
        for token in tokenize(text):
            push_token(token, font)

    if line_segments:
        flush()
    return lines


def wrap(text: str, font: ImageFont.FreeTypeFont, maxw: int) -> List[str]:
    lines = layout_segments([(text, font)], maxw)
    return ["".join(part for part, _ in line.segments) for line in lines]


def draw_mixed(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    segments: Sequence[Tuple[str, ImageFont.FreeTypeFont]],
    maxw: int,
    lh: int,
    color: str,
) -> int:
    lines = layout_segments(segments, maxw)
    for line in lines:
        cursor_x = x + line.indent
        for text, font in line.segments:
            draw.text((cursor_x, y), text, fill=color, font=font)
            cursor_x += int(round(font.getlength(text)))
        y += lh
    return y


def draw_hanging_mixed(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    segments: Sequence[Tuple[str, ImageFont.FreeTypeFont]],
    maxw: int,
    lh: int,
    color: str,
    indent: int,
) -> int:
    lines = layout_segments(segments, maxw, first_indent=indent, rest_indent=indent)
    for line in lines:
        cursor_x = x + line.indent
        for text, font in line.segments:
            draw.text((cursor_x, y), text, fill=color, font=font)
            cursor_x += int(round(font.getlength(text)))
        y += lh
    return y


def draw_left_lines(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    lines: Sequence[str],
    font: ImageFont.FreeTypeFont,
    line_height: int,
    color: str,
) -> int:
    for line in lines:
        draw.text((x, y), line, fill=color, font=font)
        y += line_height
    return y


def draw_aligned_text(
    draw: ImageDraw.ImageDraw,
    width: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    color: str,
    align: str,
    x: int | None = None,
) -> None:
    if align == "left":
        draw.text((x or 0, y), text, fill=color, font=font)
        return
    text_width = int(round(font.getlength(text)))
    text_x = (width - text_width) // 2
    draw.text((text_x, y), text, fill=color, font=font)


def detect_type(items: Sequence[object]) -> str:
    if not items:
        return "list"
    if all(isinstance(item, dict) for item in items):
        if all("normal" in item and "better" in item for item in items):
            return "compare"
    if all(isinstance(item, str) for item in items):
        if any("【" in item and "】" in item for item in items):
            return "tag"
        return "list"
    raise ValueError("无法自动识别页型，请检查 items 结构是否符合要求。")


def normalize_style(style_value: object) -> str:
    raw_style = str(style_value).strip()
    normalized = STYLE_ALIASES.get(raw_style.lower(), STYLE_ALIASES.get(raw_style))
    if normalized:
        return normalized
    raise ValueError


def normalize_quotes(text: str) -> str:
    core = str(text).strip().strip("“”\"")
    return f"“{core}”"


def count_han_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def sanitize_output_name(text: object, fallback: str = "result") -> str:
    cleaned = str(text or "").strip()
    cleaned = INVALID_PATH_CHARS_RE.sub("_", cleaned)
    cleaned = WHITESPACE_RE.sub(" ", cleaned)
    cleaned = cleaned.strip(" .")
    return cleaned or fallback


def build_expected_output_names(cfg: dict) -> List[str]:
    return ["封面.jpg"] + [f"第{index + 2}页.jpg" for index, _ in enumerate(cfg["pages"])]


def load_output_manifest(out_dir: Path) -> set[str]:
    manifest_path = out_dir / OUTPUT_MANIFEST_NAME
    if not manifest_path.exists():
        return set()
    try:
        with manifest_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return set()
    if not isinstance(payload, dict) or payload.get("managed_by") != "xhs-render":
        return set()
    generated_files = payload.get("generated_files", [])
    if not isinstance(generated_files, list):
        return set()
    names: set[str] = set()
    for item in generated_files:
        if isinstance(item, str):
            file_name = Path(item).name.strip()
            if file_name:
                names.add(file_name)
    return names


def write_output_manifest(
    out_dir: Path,
    generated_files: Sequence[Path | str],
    *,
    status: str,
) -> None:
    manifest_path = out_dir / OUTPUT_MANIFEST_NAME
    payload = {
        "managed_by": "xhs-render",
        "status": status,
        "generated_files": [Path(item).name for item in generated_files],
    }
    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def prepare_output_dir(out_dir: Path, expected_names: Sequence[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    managed_names = load_output_manifest(out_dir)
    conflicts = [
        name
        for name in expected_names
        if (out_dir / name).exists() and name not in managed_names
    ]
    if conflicts:
        conflict_text = "、".join(conflicts)
        raise FileExistsError(
            f"输出目录里已存在同名图片：{conflict_text}\n"
            f"目录：{out_dir}\n"
            "这些文件不是本工具记录过的旧输出。为避免误删，当前已停止覆盖。\n"
            "请改用空目录，或先手动整理这些图片后再重试。"
        )

    for stale_name in sorted(managed_names | set(expected_names)):
        stale_path = out_dir / stale_name
        if stale_path.exists() and stale_path.is_file():
            stale_path.unlink()

    # 先写入占位清单，确保中途失败时，下次也只会清理本工具管理的文件。
    write_output_manifest(out_dir, expected_names, status="in_progress")


def make_personalized_output_name(cfg: dict, fallback_name: str = "result") -> str:
    topic_name = str(cfg.get("cover_title", "")).strip().strip("“”\"") or fallback_name
    style_name = STYLE_PRESETS.get(cfg.get("style"), {}).get("label", str(cfg.get("style", "")).strip())
    pieces = [sanitize_output_name(topic_name, fallback_name)]
    if style_name:
        pieces.append(sanitize_output_name(style_name, "风格"))
    return sanitize_output_name("-".join(piece for piece in pieces if piece), fallback_name)


def infer_style_from_path(config_path: Path) -> str | None:
    path_text = str(config_path)
    for key, value in STYLE_ALIASES.items():
        if key in path_text:
            return value
    return None


def split_cover_title(
    title: str, font: ImageFont.FreeTypeFont, maxw: int
) -> List[str]:
    best: Tuple[float, List[str]] | None = None
    for index in range(2, len(title) - 1):
        left = title[:index].strip()
        right = title[index:].strip()
        if not left or not right:
            continue
        left_w = float(font.getlength(left))
        right_w = float(font.getlength(right))
        fits = left_w <= maxw and right_w <= maxw
        penalty = 0 if fits else 1_000_000
        score = penalty + max(left_w, right_w) + abs(left_w - right_w) * 0.35
        if best is None or score < best[0]:
            best = (score, [left, right])
    if best:
        return best[1]

    wrapped = wrap(title, font, maxw)
    if len(wrapped) >= 2:
        return [wrapped[0], "".join(wrapped[1:])]
    return [title]


def fit_cover_title(
    title: str,
    bold_font_path: Path,
    base_size: int,
    min_size: int,
    maxw: int,
) -> Tuple[ImageFont.FreeTypeFont, List[str]]:
    size = base_size
    font = load_font(str(bold_font_path), size)
    title_width = float(font.getlength(title))
    # 先按比例缩字号，只有缩到最小值还超宽时，才退到两行。
    if title_width > maxw:
        scaled_size = max(min_size, int(math.floor(base_size * maxw / title_width)))
        size = scaled_size
        font = load_font(str(bold_font_path), size)
        while size > min_size and float(font.getlength(title)) > maxw:
            size -= 1
            font = load_font(str(bold_font_path), size)
    if float(font.getlength(title)) <= maxw:
        return font, [title]

    font = load_font(str(bold_font_path), min_size)
    return font, split_cover_title(title, font, maxw)


def validate_page(page: dict, index: int) -> None:
    if not isinstance(page, dict):
        raise ValueError(f"第 {index + 2} 页配置必须是对象。")
    if "title" not in page or not isinstance(page["title"], str) or not page["title"].strip():
        raise ValueError(f"第 {index + 2} 页缺少有效的 title。")
    if "items" not in page or not isinstance(page["items"], list) or not page["items"]:
        raise ValueError(f"第 {index + 2} 页缺少有效的 items 数组。")
    page_type = page.get("type", "auto")
    if page_type not in ALLOWED_TYPES:
        raise ValueError(f"第 {index + 2} 页 type 只能是 auto / list / compare / tag。")


def resolve_page_type(page: dict) -> str:
    page_type = page.get("type", "auto")
    return detect_type(page["items"]) if page_type == "auto" else page_type


def load_background_for_style(style_name: str, assets_dir: Path, size: Tuple[int, int]) -> Image.Image:
    style = STYLE_PRESETS[style_name]
    bg_path = assets_dir / style["background"]
    if not bg_path.exists():
        raise FileNotFoundError(f"未找到底图文件：{bg_path}")
    return load_fitted_background(str(bg_path), size[0], size[1]).copy()


def render_cover(cfg: dict, out_dir: Path, assets_dir: Path, regular_font: Path, bold_font: Path) -> Path:
    style = STYLE_PRESETS[cfg["style"]]
    cover_cfg = style["cover"]
    width, height = style["cover_size"]
    image = load_background_for_style(cfg["style"], assets_dir, (width, height))
    draw = ImageDraw.Draw(image)
    color = style["text_color"]
    cover_top_text = str(cfg.get("cover_top_text", cover_cfg["top_text"])).strip() or cover_cfg["top_text"]
    cover_bottom_text = str(cfg.get("cover_bottom_text", cover_cfg["bottom_text"])).strip() or cover_cfg["bottom_text"]

    top_font = load_font(str(regular_font), cover_cfg["top_size"])
    bottom_font = load_font(str(bold_font if cfg["style"] == "rifu" else regular_font), cover_cfg["bottom_size"])
    title_text = normalize_quotes(cfg["cover_title"])
    title_font, title_lines = fit_cover_title(
        title_text,
        bold_font,
        cover_cfg["title_size"],
        cover_cfg["title_min_size"],
        cover_cfg["title_max_width"],
    )

    draw_aligned_text(
        draw,
        width,
        cover_cfg["top_y"],
        cover_top_text,
        top_font,
        color,
        cover_cfg["top_align"],
        cover_cfg["top_x"],
    )

    title_line_height = title_font.size + cover_cfg["title_line_gap"]
    title_start_y = cover_cfg["title_y"]
    if len(title_lines) > 1:
        total_height = title_line_height * len(title_lines)
        title_start_y = cover_cfg["title_y"] - total_height // 2
    for offset, line in enumerate(title_lines):
        draw_aligned_text(
            draw,
            width,
            title_start_y + offset * title_line_height,
            line,
            title_font,
            color,
            cover_cfg["title_align"],
        )

    draw_aligned_text(
        draw,
        width,
        cover_cfg["bottom_y"],
        cover_bottom_text,
        bottom_font,
        color,
        cover_cfg["bottom_align"],
        cover_cfg["bottom_x"],
    )

    output_path = out_dir / "封面.jpg"
    image.save(output_path, format="JPEG", quality=92)
    print(f"✓ {output_path} (y={cover_cfg['bottom_y']}, safe={height - 60})")
    return output_path


def render_list_items(
    draw: ImageDraw.ImageDraw,
    items: Sequence[str],
    x: int,
    y: int,
    maxw: int,
    body_font: ImageFont.FreeTypeFont,
    body_lh: int,
    gap: int,
    color: str,
) -> int:
    for index, item in enumerate(items, start=1):
        prefix = f"{index}. "
        prefix_width = int(math.ceil(body_font.getlength(prefix)))
        draw.text((x, y), prefix, fill=color, font=body_font)
        y = draw_hanging_mixed(
            draw,
            x,
            y,
            [(item, body_font)],
            maxw,
            body_lh,
            color,
            prefix_width,
        )
        y += gap
    return y - gap if items else y


def render_tag_items(
    draw: ImageDraw.ImageDraw,
    items: Sequence[str],
    x: int,
    y: int,
    maxw: int,
    body_font: ImageFont.FreeTypeFont,
    bold_font: ImageFont.FreeTypeFont,
    body_lh: int,
    gap: int,
    color: str,
) -> int:
    for item in items:
        match = TAG_RE.match(item)
        if match:
            segments = [(match.group(1), bold_font), (match.group(2), body_font)]
        else:
            segments = [(item, body_font)]
        y = draw_mixed(draw, x, y, segments, maxw, body_lh, color)
        y += gap
    return y - gap if items else y


def render_compare_items(
    draw: ImageDraw.ImageDraw,
    items: Sequence[dict],
    x: int,
    y: int,
    maxw: int,
    body_font: ImageFont.FreeTypeFont,
    bold_font: ImageFont.FreeTypeFont,
    body_lh: int,
    pair_gap: int,
    group_gap: int,
    color: str,
) -> int:
    for item in items:
        if "normal" not in item or "better" not in item:
            raise ValueError("compare 页型中的每一项都必须包含 normal 和 better 字段。")
        y = draw_mixed(
            draw,
            x,
            y,
            [("普通:", bold_font), (str(item["normal"]), body_font)],
            maxw,
            body_lh,
            color,
        )
        y += pair_gap
        y = draw_mixed(
            draw,
            x,
            y,
            [("优化:", bold_font), (str(item["better"]), body_font)],
            maxw,
            body_lh,
            color,
        )
        y += group_gap
    return y - group_gap if items else y


def render_page(
    cfg: dict,
    page: dict,
    idx: int,
    out_dir: Path,
    assets_dir: Path,
    regular_font: Path,
    bold_font: Path,
) -> Path:
    style = STYLE_PRESETS[cfg["style"]]
    page_cfg = style["page"]
    width, height = style["page_size"]
    safe_limit = height - 60
    image = load_background_for_style(cfg["style"], assets_dir, (width, height))
    draw = ImageDraw.Draw(image)
    color = style["text_color"]

    title_font = load_font(str(bold_font), page_cfg["title_size"])
    body_font = load_font(str(regular_font), page_cfg["body_size"])
    body_bold = load_font(str(bold_font), page_cfg["body_size"])

    x = page_cfg["margin_x"]
    maxw = width - x * 2
    y = page_cfg["title_y"]

    title_lines = wrap(page["title"].strip(), title_font, maxw)
    y = draw_left_lines(draw, x, y, title_lines, title_font, page_cfg["title_lh"], color)
    y += page_cfg["body_gap_after_title"]

    page_type = resolve_page_type(page)
    items = page["items"]

    # 三种页型共用同一套字体和安全区，只在条目组织方式上分流。
    if page_type == "list":
        if not all(isinstance(item, str) for item in items):
            raise ValueError(f"第 {idx + 2} 页 list 页型要求 items 为字符串数组。")
        y = render_list_items(
            draw,
            items,
            x,
            y,
            maxw,
            body_font,
            page_cfg["body_lh"],
            page_cfg["list_gap"],
            color,
        )
    elif page_type == "tag":
        if not all(isinstance(item, str) for item in items):
            raise ValueError(f"第 {idx + 2} 页 tag 页型要求 items 为字符串数组。")
        y = render_tag_items(
            draw,
            items,
            x,
            y,
            maxw,
            body_font,
            body_bold,
            page_cfg["body_lh"],
            page_cfg["tag_gap"],
            color,
        )
    else:
        if not all(isinstance(item, dict) for item in items):
            raise ValueError(f"第 {idx + 2} 页 compare 页型要求 items 为对象数组。")
        y = render_compare_items(
            draw,
            items,
            x,
            y,
            maxw,
            body_font,
            body_bold,
            page_cfg["body_lh"],
            page_cfg["compare_pair_gap"],
            page_cfg["compare_group_gap"],
            color,
        )

    if y > safe_limit:
        print(f"警告: 第{idx + 2}页内容超出安全区 (y={y}, safe={safe_limit})")

        # Add visual overflow warning overlay
        banner_height = 60
        banner_y = height - banner_height

        # Convert image to RGBA for compositing
        image_rgba = image.convert("RGBA")

        # Create overlay with semi-transparent red/orange warning banner
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Draw semi-transparent red banner at bottom
        overlay_draw.rectangle(
            [(0, banner_y), (width, height)],
            fill=(200, 60, 60, 180)  # RGBA: red-orange with 70% opacity
        )

        # Draw warning text on the banner
        warning_text = "⚠ 内容超出安全区，建议拆分此页"
        warning_font = load_font(str(regular_font), 32)

        # Calculate text position for centering
        text_bbox = overlay_draw.textbbox((0, 0), warning_text, font=warning_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        text_x = (width - text_width) // 2
        text_y = banner_y + (banner_height - text_height) // 2

        overlay_draw.text(
            (text_x, text_y),
            warning_text,
            fill=(255, 255, 255, 255),  # White text, fully opaque
            font=warning_font
        )

        # Composite overlay onto image
        image_rgba = Image.alpha_composite(image_rgba, overlay)

        # Convert back to RGB for JPEG saving
        image = image_rgba.convert("RGB")

    output_path = out_dir / f"第{idx + 2}页.jpg"
    image.save(output_path, format="JPEG", quality=92)
    print(f"✓ {output_path} (y={y}, safe={safe_limit})")
    return output_path


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        cfg = json.load(file)

    # 移除 content_style 字段(它是元数据,用于 AI 生成的内容分类,与排版无关)
    cfg.pop("content_style", None)

    raw_style = str(cfg.get("style", "")).strip()
    if raw_style.startswith("{") and raw_style.endswith("}"):
        inferred_style = infer_style_from_path(config_path)
        if inferred_style:
            cfg["style"] = inferred_style
        else:
            raise ValueError(
                f"style 当前还是模板占位符 {raw_style}，说明生成 JSON 时没有把它替换掉。"
                "请改成 banxia / rifu，或直接写中文 半夏 / 日富。"
            )
    elif not raw_style:
        inferred_style = infer_style_from_path(config_path)
        if inferred_style:
            cfg["style"] = inferred_style
        else:
            raise ValueError("style 为空，且无法从文件路径推断风格，请填写 banxia / rifu。")
    else:
        try:
            cfg["style"] = normalize_style(raw_style)
        except ValueError:
            raise ValueError(
                f"style={raw_style!r} 无效，只能是 banxia / rifu，也支持直接写中文 半夏 / 日富。"
            ) from None
    if not isinstance(cfg.get("cover_title"), str) or not cfg["cover_title"].strip():
        raise ValueError("cover_title 不能为空。")
    if "cover_top_text" in cfg and not isinstance(cfg["cover_top_text"], str):
        raise ValueError("cover_top_text 必须是字符串。")
    if "cover_bottom_text" in cfg and not isinstance(cfg["cover_bottom_text"], str):
        raise ValueError("cover_bottom_text 必须是字符串。")
    if not isinstance(cfg.get("pages"), list) or not cfg["pages"]:
        raise ValueError("pages 必须是非空数组。")

    for index, page in enumerate(cfg["pages"]):
        validate_page(page, index)
    return cfg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="小红书图文本地批量排版工具")
    parser.add_argument("config", help="JSON 配置文件路径")
    parser.add_argument(
        "--out",
        default=None,
        help="输出目录；不传时自动保存到 ./output/封面标题-风格",
    )
    parser.add_argument(
        "--assets",
        default=str(SCRIPT_DIR / "assets"),
        help="底图目录，默认 ./assets",
    )
    parser.add_argument(
        "--font-regular",
        default=None,
        help="常规字体路径；不传时自动检测",
    )
    parser.add_argument(
        "--font-bold",
        default=None,
        help="加粗字体路径；不传时自动检测",
    )
    return parser.parse_args()


def main() -> None:
    init_styles(SCRIPT_DIR)
    args = parse_args()
    started_at = time.perf_counter()

    config_path = Path(args.config).expanduser().resolve()
    assets_dir = Path(args.assets).expanduser().resolve()

    if not config_path.exists():
        raise FileNotFoundError(f"未找到配置文件：{config_path}")
    if config_path.is_dir():
        json_files = sorted(config_path.glob("*.json"))
        if json_files:
            candidates = "、".join(path.name for path in json_files[:5])
            raise IsADirectoryError(
                f"你传入的是目录，不是 JSON 文件：{config_path}\n"
                f"这个目录下可用的 JSON 有：{candidates}\n"
                "请把命令改成具体文件路径，例如："
                f"{json_files[0]}"
            )
        raise IsADirectoryError(
            f"你传入的是目录，不是 JSON 文件：{config_path}\n"
            "这个目录里暂时没有找到可用的 .json 文件。"
        )

    cfg = load_config(config_path)
    if args.out:
        out_dir = Path(args.out).expanduser().resolve()
    else:
        out_dir = (SCRIPT_DIR / "output" / make_personalized_output_name(cfg, config_path.stem)).resolve()
    expected_output_names = build_expected_output_names(cfg)
    prepare_output_dir(out_dir, expected_output_names)
    regular_font = Path(args.font_regular).expanduser().resolve() if args.font_regular else find_font(bold=False)
    bold_font = Path(args.font_bold).expanduser().resolve() if args.font_bold else find_font(bold=True)

    if count_han_chars(cfg["cover_title"]) > 5:
        print(
            f"提示: 当前 cover_title 为“{cfg['cover_title']}”，超过 5 个汉字。"
            "为了让封面更稳，建议尽量压缩到 2~5 个字。"
        )
    cover_top_text = str(cfg.get("cover_top_text", "")).strip()
    if cover_top_text and count_han_chars(cover_top_text) > 10:
        print(
            f"提示: 当前 cover_top_text 为“{cover_top_text}”，偏长。"
            "封面上方小字建议尽量控制在 6~10 个字，"
            "比如“写小说可用的”或“可以写进小说里的”。"
        )

    generated_files: List[Path] = []
    generated_files.append(render_cover(cfg, out_dir, assets_dir, regular_font, bold_font))
    for index, page in enumerate(cfg["pages"]):
        generated_files.append(
            render_page(cfg, page, index, out_dir, assets_dir, regular_font, bold_font)
        )
    write_output_manifest(out_dir, generated_files, status="complete")

    elapsed = time.perf_counter() - started_at
    print(f"完成，共输出 {len(generated_files)} 张图片，耗时 {elapsed:.2f}s")


if __name__ == "__main__":
    main()
