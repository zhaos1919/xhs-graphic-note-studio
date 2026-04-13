STYLE_PRESETS = {
    "banxia": {
        "label": "半夏",
        "page_size": (1242, 1656),
        "cover_size": (1080, 1350),
        "background": "banxia_bg.jpg",
        "text_color": "#282832",
        "page": {
            "margin_x": 90,
            "title_y": 96,
            "title_size": 50,
            "title_lh": 74,
            "body_gap_after_title": 42,
            "body_size": 43,
            "body_lh": 68,
            "list_gap": 14,
            "tag_gap": 16,
            "compare_pair_gap": 8,
            "compare_group_gap": 76,
        },
        "cover": {
            "top_text": "写小说可用的",
            "top_size": 53,
            "top_y": 324,
            "top_align": "center",
            "top_x": None,
            "title_size": 120,
            "title_min_size": 92,
            "title_y": 633,
            "title_max_width": 700,
            "title_line_gap": 18,
            "title_align": "center",
            "bottom_text": "小说素材｜写作技巧｜干货分享",
            "bottom_size": 42,
            "bottom_y": 1107,
            "bottom_align": "center",
            "bottom_x": None,
        },
    },
    "rifu": {
        "label": "日富",
        "page_size": (1532, 2048),
        "cover_size": (1532, 2048),
        "background": "rifu_bg.jpg",
        "text_color": "#1a1a1a",
        "page": {
            "margin_x": 82,
            "title_y": 108,
            "title_size": 68,
            "title_lh": 106,
            "body_gap_after_title": 40,
            "body_size": 46,
            "body_lh": 86,
            "list_gap": 18,
            "tag_gap": 20,
            "compare_pair_gap": 12,
            "compare_group_gap": 98,
        },
        "cover": {
            "top_text": "可以写进小说的",
            "top_size": 72,
            "top_y": 421,
            "top_align": "left",
            "top_x": 136,
            "title_size": 185,
            "title_min_size": 133,
            "title_y": 891,
            "title_max_width": 1010,
            "title_line_gap": 28,
            "title_align": "center",
            "bottom_text": "小说素材、干货分享",
            "bottom_size": 62,
            "bottom_y": 1688,
            "bottom_align": "center",
            "bottom_x": None,
        },
    },
}


def load_custom_styles(config_dir) -> dict:
    """
    Load custom styles from custom_styles.json if it exists.
    Custom styles override built-in ones with the same key.
    Silently returns without changes if file not found.
    Wrapped in try/except to never crash.
    """
    from pathlib import Path

    try:
        custom_file = Path(config_dir) / "custom_styles.json"
        if not custom_file.exists():
            return STYLE_PRESETS

        import json
        with custom_file.open("r", encoding="utf-8") as f:
            custom_styles = json.load(f)

        if isinstance(custom_styles, dict):
            STYLE_PRESETS.update(custom_styles)
    except Exception:
        # Silently ignore any errors
        pass

    return STYLE_PRESETS


def init_styles(config_dir=None):
    """
    Initialize styles, optionally loading custom styles from config_dir.
    If config_dir is provided, calls load_custom_styles(config_dir).
    Returns the current STYLE_PRESETS dict.
    """
    if config_dir:
        load_custom_styles(config_dir)
    return STYLE_PRESETS
