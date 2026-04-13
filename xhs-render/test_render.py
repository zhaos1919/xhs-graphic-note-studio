import tempfile
import unittest
from unittest.mock import Mock
from pathlib import Path
from render import (
    build_expected_output_names,
    load_output_manifest,
    prepare_output_dir,
    tokenize,
    normalize_quotes,
    normalize_style,
    detect_type,
    sanitize_output_name,
    make_personalized_output_name,
    count_han_chars,
    trim_trailing_spaces,
    validate_page,
    resolve_page_type,
    write_output_manifest,
)

# Curly quotes for testing
LQ = chr(0x201C)  # "
RQ = chr(0x201D)  # "


class TestTokenize(unittest.TestCase):
    """Test the tokenize function with various text inputs."""

    def test_tokenize_chinese(self):
        """Test tokenization of Chinese text."""
        result = tokenize("你好")
        self.assertIn("你", result)
        self.assertIn("好", result)

    def test_tokenize_english(self):
        """Test tokenization of English words."""
        result = tokenize("hello world")
        self.assertIn("hello", result)
        self.assertIn("world", result)

    def test_tokenize_mixed_text(self):
        """Test tokenization of mixed Chinese and English."""
        result = tokenize("你好hello世界")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_tokenize_with_newlines(self):
        """Test tokenization with newline characters."""
        result = tokenize("hello\nworld")
        self.assertIn("\n", result)
        self.assertIn("hello", result)
        self.assertIn("world", result)

    def test_tokenize_with_spaces(self):
        """Test tokenization with spaces."""
        result = tokenize("hello world")
        self.assertIn("hello", result)
        self.assertIn(" ", result)
        self.assertIn("world", result)

    def test_tokenize_empty_string(self):
        """Test tokenization of empty string."""
        result = tokenize("")
        self.assertEqual(result, [])

    def test_tokenize_punctuation(self):
        """Test tokenization with punctuation."""
        result = tokenize("hello,world!")
        self.assertIn("hello", result)
        self.assertIn(",", result)
        self.assertIn("world", result)
        self.assertIn("!", result)

    def test_tokenize_numbers_underscore(self):
        """Test tokenization of numbers and underscores."""
        result = tokenize("test_123")
        self.assertIn("test_123", result)


class TestNormalizeQuotes(unittest.TestCase):
    """Test the normalize_quotes function."""

    def test_normalize_quotes_normal_input(self):
        """Test normalize_quotes with normal input."""
        result = normalize_quotes("hello")
        self.assertEqual(result, LQ + "hello" + RQ)

    def test_normalize_quotes_already_quoted_double(self):
        """Test normalize_quotes with already double-quoted input."""
        result = normalize_quotes(LQ + "hello" + RQ)
        self.assertEqual(result, LQ + "hello" + RQ)

    def test_normalize_quotes_with_spaces(self):
        """Test normalize_quotes with leading/trailing spaces."""
        result = normalize_quotes("  hello  ")
        self.assertEqual(result, LQ + "hello" + RQ)

    def test_normalize_quotes_with_english_quotes(self):
        """Test normalize_quotes with English quotation marks."""
        result = normalize_quotes('"hello"')
        self.assertEqual(result, LQ + "hello" + RQ)

    def test_normalize_quotes_empty_string(self):
        """Test normalize_quotes with empty string."""
        result = normalize_quotes("")
        self.assertEqual(result, LQ + RQ)

    def test_normalize_quotes_mixed_quotes(self):
        """Test normalize_quotes with mixed quote types."""
        result = normalize_quotes('"你好"')
        self.assertEqual(result, LQ + "你好" + RQ)


class TestNormalizeStyle(unittest.TestCase):
    """Test the normalize_style function."""

    def test_normalize_style_banxia_pinyin(self):
        """Test normalize_style with banxia pinyin."""
        result = normalize_style("banxia")
        self.assertEqual(result, "banxia")

    def test_normalize_style_banxia_chinese(self):
        """Test normalize_style with Chinese banxia."""
        result = normalize_style("半夏")
        self.assertEqual(result, "banxia")

    def test_normalize_style_banxia_full(self):
        """Test normalize_style with full name banxia."""
        result = normalize_style("半夏风格")
        self.assertEqual(result, "banxia")

    def test_normalize_style_rifu_pinyin(self):
        """Test normalize_style with rifu pinyin."""
        result = normalize_style("rifu")
        self.assertEqual(result, "rifu")

    def test_normalize_style_rifu_chinese(self):
        """Test normalize_style with Chinese rifu."""
        result = normalize_style("日富")
        self.assertEqual(result, "rifu")

    def test_normalize_style_rifu_full(self):
        """Test normalize_style with full name rifu."""
        result = normalize_style("日富风格")
        self.assertEqual(result, "rifu")

    def test_normalize_style_rifu_one_day_new(self):
        """Test normalize_style with name rifu."""
        result = normalize_style("日富一日新")
        self.assertEqual(result, "rifu")

    def test_normalize_style_richu_alias(self):
        """Test normalize_style with richu alias."""
        result = normalize_style("richu")
        self.assertEqual(result, "rifu")

    def test_normalize_style_invalid(self):
        """Test normalize_style with invalid value."""
        with self.assertRaises(ValueError):
            normalize_style("invalid_style")

    def test_normalize_style_case_insensitive(self):
        """Test normalize_style with mixed case."""
        result = normalize_style("BANXIA")
        self.assertEqual(result, "banxia")

    def test_normalize_style_with_spaces(self):
        """Test normalize_style with surrounding spaces."""
        result = normalize_style("  rifu  ")
        self.assertEqual(result, "rifu")


class TestDetectType(unittest.TestCase):
    """Test the detect_type function."""

    def test_detect_type_empty_list(self):
        """Test detect_type with empty list."""
        result = detect_type([])
        self.assertEqual(result, "list")

    def test_detect_type_string_list(self):
        """Test detect_type with list of strings."""
        result = detect_type(["item1", "item2", "item3"])
        self.assertEqual(result, "list")

    def test_detect_type_with_tags(self):
        """Test detect_type with items containing tags."""
        result = detect_type(["【标签】content", "【另一个】more content"])
        self.assertEqual(result, "tag")

    def test_detect_type_compare(self):
        """Test detect_type with compare structure."""
        items = [
            {"normal": "普通方案", "better": "优化方案"},
            {"normal": "方案A", "better": "方案B"},
        ]
        result = detect_type(items)
        self.assertEqual(result, "compare")

    def test_detect_type_mixed_invalid(self):
        """Test detect_type with mixed types raises error."""
        with self.assertRaises(ValueError):
            detect_type(["string", 123, {"key": "value"}])

    def test_detect_type_dict_without_required_fields(self):
        """Test detect_type with dict items missing required fields."""
        items = [{"only_normal": "value"}]
        with self.assertRaises(ValueError):
            detect_type(items)

    def test_detect_type_single_string(self):
        """Test detect_type with single string."""
        result = detect_type(["single item"])
        self.assertEqual(result, "list")

    def test_detect_type_single_tag(self):
        """Test detect_type with single tag."""
        result = detect_type(["【标签】内容"])
        self.assertEqual(result, "tag")

    def test_detect_type_numbers_mixed_error(self):
        """Test detect_type with numbers raises error."""
        with self.assertRaises(ValueError):
            detect_type([1, 2, 3])


class TestSanitizeOutputName(unittest.TestCase):
    """Test the sanitize_output_name function."""

    def test_sanitize_output_name_normal(self):
        """Test sanitize_output_name with normal name."""
        result = sanitize_output_name("my_project")
        self.assertEqual(result, "my_project")

    def test_sanitize_output_name_with_illegal_chars(self):
        """Test sanitize_output_name with illegal path characters."""
        result = sanitize_output_name("file<name>test")
        self.assertIn("_", result)
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)

    def test_sanitize_output_name_with_colons(self):
        """Test sanitize_output_name removes colons."""
        result = sanitize_output_name("my:name:test")
        self.assertNotIn(":", result)

    def test_sanitize_output_name_with_slashes(self):
        """Test sanitize_output_name removes slashes."""
        result = sanitize_output_name("path/to/file")
        self.assertNotIn("/", result)

    def test_sanitize_output_name_with_backslashes(self):
        """Test sanitize_output_name removes backslashes."""
        result = sanitize_output_name("path\\to\\file")
        self.assertNotIn("\\", result)

    def test_sanitize_output_name_empty_string(self):
        """Test sanitize_output_name with empty string."""
        result = sanitize_output_name("")
        self.assertEqual(result, "result")

    def test_sanitize_output_name_whitespace_only(self):
        """Test sanitize_output_name with whitespace only."""
        result = sanitize_output_name("   ")
        self.assertEqual(result, "result")

    def test_sanitize_output_name_with_fallback(self):
        """Test sanitize_output_name with custom fallback."""
        result = sanitize_output_name("", fallback="custom_fallback")
        self.assertEqual(result, "custom_fallback")

    def test_sanitize_output_name_with_multiple_spaces(self):
        """Test sanitize_output_name normalizes spaces."""
        result = sanitize_output_name("my   project   name")
        self.assertNotIn("   ", result)

    def test_sanitize_output_name_with_dots(self):
        """Test sanitize_output_name removes trailing dots."""
        result = sanitize_output_name("name...")
        self.assertFalse(result.endswith("."))

    def test_sanitize_output_name_chinese(self):
        """Test sanitize_output_name with Chinese characters."""
        result = sanitize_output_name("项目名称")
        self.assertEqual(result, "项目名称")


class TestMakePersonalizedOutputName(unittest.TestCase):
    """Test the make_personalized_output_name function."""

    def test_make_personalized_output_name_full_config(self):
        """Test make_personalized_output_name with full config."""
        cfg = {
            "cover_title": "我的小说",
            "style": "banxia"
        }
        result = make_personalized_output_name(cfg)
        self.assertIn("我的小说", result)
        self.assertIn("半夏", result)

    def test_make_personalized_output_name_missing_style(self):
        """Test make_personalized_output_name with missing style."""
        cfg = {
            "cover_title": "标题"
        }
        result = make_personalized_output_name(cfg)
        self.assertIn("标题", result)

    def test_make_personalized_output_name_empty_title(self):
        """Test make_personalized_output_name with empty title."""
        cfg = {
            "cover_title": "",
            "style": "rifu"
        }
        result = make_personalized_output_name(cfg)
        # When title is empty, function uses fallback and includes style
        self.assertIn("result", result)
        self.assertIn("日富", result)

    def test_make_personalized_output_name_with_quotes(self):
        """Test make_personalized_output_name strips quotes from title."""
        cfg = {
            "cover_title": '"有引号的标题"',
            "style": "banxia"
        }
        result = make_personalized_output_name(cfg)
        self.assertNotIn('"', result)

    def test_make_personalized_output_name_custom_fallback(self):
        """Test make_personalized_output_name with custom fallback."""
        cfg = {
            "cover_title": "",
        }
        result = make_personalized_output_name(cfg, fallback_name="custom")
        self.assertEqual(result, "custom")

    def test_make_personalized_output_name_with_illegal_chars(self):
        """Test make_personalized_output_name sanitizes illegal chars."""
        cfg = {
            "cover_title": "标题<test>",
            "style": "rifu"
        }
        result = make_personalized_output_name(cfg)
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)


class TestCountHanChars(unittest.TestCase):
    """Test the count_han_chars function."""

    def test_count_han_chars_pure_chinese(self):
        """Test count_han_chars with pure Chinese text."""
        result = count_han_chars("你好世界")
        self.assertEqual(result, 4)

    def test_count_han_chars_mixed(self):
        """Test count_han_chars with mixed Chinese and English."""
        result = count_han_chars("你好hello世界")
        self.assertEqual(result, 4)

    def test_count_han_chars_pure_english(self):
        """Test count_han_chars with pure English."""
        result = count_han_chars("hello world")
        self.assertEqual(result, 0)

    def test_count_han_chars_empty(self):
        """Test count_han_chars with empty string."""
        result = count_han_chars("")
        self.assertEqual(result, 0)

    def test_count_han_chars_with_numbers(self):
        """Test count_han_chars with numbers."""
        result = count_han_chars("你好123世界456")
        self.assertEqual(result, 4)

    def test_count_han_chars_punctuation(self):
        """Test count_han_chars ignores punctuation."""
        result = count_han_chars("你好，世界!")
        self.assertEqual(result, 4)

    def test_count_han_chars_single_char(self):
        """Test count_han_chars with single character."""
        result = count_han_chars("中")
        self.assertEqual(result, 1)


class TestTrimTrailingSpaces(unittest.TestCase):
    """Test the trim_trailing_spaces function."""

    def test_trim_trailing_spaces_with_trailing_spaces(self):
        """Test trim_trailing_spaces removes trailing spaces."""
        mock_font = Mock()
        segments = [("hello", mock_font), ("  ", mock_font)]
        result = TestTrimTrailingSpaces._call_trim(segments)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "hello")

    def test_trim_trailing_spaces_empty_segments(self):
        """Test trim_trailing_spaces with empty segments."""
        mock_font = Mock()
        segments = [("", mock_font), ("", mock_font)]
        result = TestTrimTrailingSpaces._call_trim(segments)
        self.assertEqual(len(result), 0)

    def test_trim_trailing_spaces_no_trailing(self):
        """Test trim_trailing_spaces with no trailing spaces."""
        mock_font = Mock()
        segments = [("hello", mock_font), ("world", mock_font)]
        result = TestTrimTrailingSpaces._call_trim(segments)
        self.assertEqual(len(result), 2)

    def test_trim_trailing_spaces_middle_spaces(self):
        """Test trim_trailing_spaces preserves middle content."""
        mock_font = Mock()
        segments = [("hello  world", mock_font)]
        result = TestTrimTrailingSpaces._call_trim(segments)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "hello  world")

    def test_trim_trailing_spaces_last_segment_space_stripped(self):
        """Test trim_trailing_spaces strips trailing space from last segment."""
        mock_font = Mock()
        segments = [("hello", mock_font), ("world  ", mock_font)]
        result = TestTrimTrailingSpaces._call_trim(segments)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1][0], "world")

    def test_trim_trailing_spaces_empty_list(self):
        """Test trim_trailing_spaces with empty list."""
        result = TestTrimTrailingSpaces._call_trim([])
        self.assertEqual(result, [])

    @staticmethod
    def _call_trim(segments):
        """Helper to call trim_trailing_spaces."""
        return trim_trailing_spaces(segments)


class TestValidatePage(unittest.TestCase):
    """Test the validate_page function."""

    def test_validate_page_valid(self):
        """Test validate_page with valid page."""
        page = {
            "title": "有效的标题",
            "items": ["item1", "item2"]
        }
        validate_page(page, 0)

    def test_validate_page_not_dict(self):
        """Test validate_page raises error if page is not dict."""
        with self.assertRaises(ValueError) as ctx:
            validate_page("not a dict", 0)
        self.assertIn("第 2 页", str(ctx.exception))

    def test_validate_page_missing_title(self):
        """Test validate_page raises error if title missing."""
        page = {
            "items": ["item1"]
        }
        with self.assertRaises(ValueError) as ctx:
            validate_page(page, 0)
        self.assertIn("缺少有效的 title", str(ctx.exception))

    def test_validate_page_empty_title(self):
        """Test validate_page raises error if title is empty."""
        page = {
            "title": "   ",
            "items": ["item1"]
        }
        with self.assertRaises(ValueError) as ctx:
            validate_page(page, 0)
        self.assertIn("缺少有效的 title", str(ctx.exception))

    def test_validate_page_title_not_string(self):
        """Test validate_page raises error if title is not string."""
        page = {
            "title": 123,
            "items": ["item1"]
        }
        with self.assertRaises(ValueError) as ctx:
            validate_page(page, 0)
        self.assertIn("缺少有效的 title", str(ctx.exception))

    def test_validate_page_missing_items(self):
        """Test validate_page raises error if items missing."""
        page = {
            "title": "标题"
        }
        with self.assertRaises(ValueError) as ctx:
            validate_page(page, 0)
        self.assertIn("缺少有效的 items", str(ctx.exception))

    def test_validate_page_empty_items(self):
        """Test validate_page raises error if items array is empty."""
        page = {
            "title": "标题",
            "items": []
        }
        with self.assertRaises(ValueError) as ctx:
            validate_page(page, 0)
        self.assertIn("缺少有效的 items", str(ctx.exception))

    def test_validate_page_invalid_type(self):
        """Test validate_page raises error for invalid type."""
        page = {
            "title": "标题",
            "items": ["item1"],
            "type": "invalid_type"
        }
        with self.assertRaises(ValueError) as ctx:
            validate_page(page, 0)
        self.assertIn("type 只能是", str(ctx.exception))

    def test_validate_page_valid_type_auto(self):
        """Test validate_page accepts type auto."""
        page = {
            "title": "标题",
            "items": ["item1"],
            "type": "auto"
        }
        validate_page(page, 0)

    def test_validate_page_valid_type_list(self):
        """Test validate_page accepts type list."""
        page = {
            "title": "标题",
            "items": ["item1"],
            "type": "list"
        }
        validate_page(page, 0)

    def test_validate_page_valid_type_compare(self):
        """Test validate_page accepts type compare."""
        page = {
            "title": "标题",
            "items": [{"normal": "a", "better": "b"}],
            "type": "compare"
        }
        validate_page(page, 0)

    def test_validate_page_valid_type_tag(self):
        """Test validate_page accepts type tag."""
        page = {
            "title": "标题",
            "items": ["【标签】内容"],
            "type": "tag"
        }
        validate_page(page, 0)

    def test_validate_page_index_in_error_message(self):
        """Test validate_page includes correct page index in error."""
        page = {"title": ""}
        with self.assertRaises(ValueError) as ctx:
            validate_page(page, 5)
        self.assertIn("第 7 页", str(ctx.exception))


class TestResolvePageType(unittest.TestCase):
    """Test the resolve_page_type function."""

    def test_resolve_page_type_explicit_auto(self):
        """Test resolve_page_type with explicit auto type."""
        page = {
            "type": "auto",
            "items": ["item1", "item2"]
        }
        result = resolve_page_type(page)
        self.assertEqual(result, "list")

    def test_resolve_page_type_explicit_list(self):
        """Test resolve_page_type with explicit list type."""
        page = {
            "type": "list",
            "items": ["item1"]
        }
        result = resolve_page_type(page)
        self.assertEqual(result, "list")

    def test_resolve_page_type_explicit_tag(self):
        """Test resolve_page_type with explicit tag type."""
        page = {
            "type": "tag",
            "items": ["【标签】内容"]
        }
        result = resolve_page_type(page)
        self.assertEqual(result, "tag")

    def test_resolve_page_type_explicit_compare(self):
        """Test resolve_page_type with explicit compare type."""
        page = {
            "type": "compare",
            "items": [{"normal": "a", "better": "b"}]
        }
        result = resolve_page_type(page)
        self.assertEqual(result, "compare")

    def test_resolve_page_type_auto_detect_list(self):
        """Test resolve_page_type auto-detects list."""
        page = {
            "items": ["item1", "item2", "item3"]
        }
        result = resolve_page_type(page)
        self.assertEqual(result, "list")

    def test_resolve_page_type_auto_detect_tag(self):
        """Test resolve_page_type auto-detects tag."""
        page = {
            "items": ["【标签1】内容1", "【标签2】内容2"]
        }
        result = resolve_page_type(page)
        self.assertEqual(result, "tag")

    def test_resolve_page_type_auto_detect_compare(self):
        """Test resolve_page_type auto-detects compare."""
        page = {
            "items": [
                {"normal": "普通", "better": "优化"},
                {"normal": "方案A", "better": "方案B"}
            ]
        }
        result = resolve_page_type(page)
        self.assertEqual(result, "compare")

    def test_resolve_page_type_default_type_missing(self):
        """Test resolve_page_type defaults to auto if type missing."""
        page = {
            "items": ["item1"]
        }
        result = resolve_page_type(page)
        self.assertEqual(result, "list")

    def test_resolve_page_type_respects_explicit_over_auto(self):
        """Test resolve_page_type respects explicit over content."""
        page = {
            "type": "list",
            "items": [
                {"normal": "a", "better": "b"}
            ]
        }
        result = resolve_page_type(page)
        self.assertEqual(result, "list")


class TestOutputDirManagement(unittest.TestCase):
    """Test manifest-based output directory cleanup."""

    def test_build_expected_output_names(self):
        """Expected file names should follow cover + numbered pages."""
        cfg = {"pages": [{}, {}, {}]}
        self.assertEqual(
            build_expected_output_names(cfg),
            ["封面.jpg", "第2页.jpg", "第3页.jpg", "第4页.jpg"],
        )

    def test_prepare_output_dir_blocks_unmanaged_conflicts(self):
        """Should not delete matching JPGs unless xhs-render created them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            (out_dir / "封面.jpg").write_bytes(b"cover")

            with self.assertRaises(FileExistsError) as ctx:
                prepare_output_dir(out_dir, ["封面.jpg", "第2页.jpg"])

            self.assertIn("为避免误删", str(ctx.exception))
            self.assertTrue((out_dir / "封面.jpg").exists())

    def test_prepare_output_dir_cleans_only_managed_files(self):
        """Should remove old managed files while keeping unrelated JPGs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            write_output_manifest(
                out_dir,
                ["封面.jpg", "第2页.jpg", "第9页.jpg"],
                status="complete",
            )
            (out_dir / "封面.jpg").write_bytes(b"old-cover")
            (out_dir / "第2页.jpg").write_bytes(b"old-page-2")
            (out_dir / "第9页.jpg").write_bytes(b"old-page-9")
            (out_dir / "保留.jpg").write_bytes(b"keep-me")

            prepare_output_dir(out_dir, ["封面.jpg", "第2页.jpg"])

            self.assertFalse((out_dir / "封面.jpg").exists())
            self.assertFalse((out_dir / "第2页.jpg").exists())
            self.assertFalse((out_dir / "第9页.jpg").exists())
            self.assertTrue((out_dir / "保留.jpg").exists())
            self.assertEqual(load_output_manifest(out_dir), {"封面.jpg", "第2页.jpg"})


if __name__ == "__main__":
    unittest.main()
