import json
import tempfile
import unittest
from pathlib import Path

from job_runner import build_jobs_for_targets, suggest_output_name


class TestJobRunner(unittest.TestCase):
    def test_suggest_output_name_uses_title_and_style(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "demo.json"
            config_path.write_text(
                json.dumps({"cover_title": "测试标题", "style": "banxia"}, ensure_ascii=False),
                encoding="utf-8",
            )
            self.assertEqual(suggest_output_name(config_path), "测试标题-半夏")

    def test_build_jobs_for_targets_keeps_nested_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target_dir = root / "jsons"
            nested_dir = target_dir / "nested"
            nested_dir.mkdir(parents=True)

            (target_dir / "a.json").write_text(
                json.dumps({"cover_title": "甲", "style": "banxia"}, ensure_ascii=False),
                encoding="utf-8",
            )
            (nested_dir / "b.json").write_text(
                json.dumps({"cover_title": "乙", "style": "rifu"}, ensure_ascii=False),
                encoding="utf-8",
            )

            jobs, open_target = build_jobs_for_targets([target_dir], output_root=root / "out")

            self.assertEqual(len(jobs), 2)
            self.assertEqual(open_target, root / "out" / "jsons")
            self.assertEqual(jobs[0].out_dir, root / "out" / "jsons" / "甲-半夏")
            self.assertEqual(jobs[1].out_dir, root / "out" / "jsons" / "nested" / "乙-日富")


if __name__ == "__main__":
    unittest.main()
