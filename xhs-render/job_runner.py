from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from render import make_personalized_output_name


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_ROOT = SCRIPT_DIR / "output"


@dataclass(frozen=True)
class RenderJob:
    config_path: Path
    out_dir: Path


@dataclass(frozen=True)
class RenderExecutionResult:
    job_index: int
    total: int
    config_path: Path
    out_dir: Path
    returncode: int
    output: str


def suggest_output_name(config_path: Path) -> str:
    fallback_name = config_path.stem
    try:
        with config_path.open("r", encoding="utf-8") as file:
            cfg = json.load(file)
    except Exception:
        return fallback_name
    if not isinstance(cfg, dict):
        return fallback_name
    return make_personalized_output_name(cfg, fallback_name)


def dedupe_dir(path: Path, used_paths: set[Path]) -> Path:
    candidate = path
    suffix = 2
    while candidate in used_paths:
        candidate = path.with_name(f"{path.name} {suffix}")
        suffix += 1
    used_paths.add(candidate)
    return candidate


def build_jobs_for_path(target: Path, output_root: Path = DEFAULT_OUTPUT_ROOT) -> tuple[list[RenderJob], Path]:
    if not target.exists():
        raise FileNotFoundError(f"未找到路径：{target}")

    if target.is_file():
        out_dir = output_root / suggest_output_name(target)
        return [RenderJob(config_path=target, out_dir=out_dir)], out_dir

    json_files = sorted(path for path in target.rglob("*.json") if path.is_file())
    if not json_files:
        raise FileNotFoundError(f"这个文件夹里没有找到 JSON 文件：{target}")

    batch_root = output_root / target.name
    jobs: list[RenderJob] = []
    used_dirs: set[Path] = set()
    for json_file in json_files:
        relative_parent = json_file.parent.relative_to(target)
        personalized_name = suggest_output_name(json_file)
        out_dir = dedupe_dir(batch_root / relative_parent / personalized_name, used_dirs)
        jobs.append(RenderJob(config_path=json_file, out_dir=out_dir))
    return jobs, batch_root


def build_jobs_for_targets(
    targets: Iterable[Path],
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> tuple[list[RenderJob], Path | None]:
    jobs: list[RenderJob] = []
    open_target: Path | None = None
    for raw_target in targets:
        target = raw_target.expanduser().resolve()
        new_jobs, current_open_target = build_jobs_for_path(target, output_root=output_root)
        jobs.extend(new_jobs)
        open_target = current_open_target if open_target is None else output_root
    return jobs, open_target


def run_render_job(
    job: RenderJob,
    *,
    python_exe: str | None = None,
    job_index: int = 1,
    total: int = 1,
    script_dir: Path = SCRIPT_DIR,
) -> RenderExecutionResult:
    command = [
        python_exe or sys.executable,
        str(script_dir / "render.py"),
        str(job.config_path),
        "--out",
        str(job.out_dir),
    ]
    completed = subprocess.run(
        command,
        cwd=str(script_dir),
        capture_output=True,
        text=True,
    )
    return RenderExecutionResult(
        job_index=job_index,
        total=total,
        config_path=job.config_path,
        out_dir=job.out_dir,
        returncode=completed.returncode,
        output=(completed.stdout or "") + (completed.stderr or ""),
    )


def open_path(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.platform.startswith("win"):
        subprocess.run(["explorer", str(path)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["xdg-open", str(path)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
