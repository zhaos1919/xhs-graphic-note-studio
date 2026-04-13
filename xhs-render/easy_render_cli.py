#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import sys
from pathlib import Path
from typing import Iterable

from job_runner import DEFAULT_OUTPUT_ROOT, build_jobs_for_targets, open_path, run_render_job


def _consume_futures(
    executor: concurrent.futures.Executor,
    jobs,
) -> tuple[int, int]:
    success = 0
    failed = 0
    futures = {}
    for index, job in enumerate(jobs, start=1):
        future = executor.submit(
            run_render_job,
            job,
            python_exe=sys.executable,
            job_index=index,
            total=len(jobs),
        )
        futures[future] = index

    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        if result.returncode == 0:
            success += 1
            print(f"✓ [{result.job_index}/{len(jobs)}] 成功")
        else:
            failed += 1
            print(f"✗ [{result.job_index}/{len(jobs)}] 失败")
            if result.output:
                print(f"  错误信息：{result.output[:200]}")
    return success, failed


def run_jobs(targets: Iterable[Path]) -> int:
    jobs, open_target = build_jobs_for_targets(targets, output_root=DEFAULT_OUTPUT_ROOT)

    if not jobs:
        print("没有找到可执行的渲染任务。")
        return 1

    print(f"开始出图，共 {len(jobs)} 个任务。")
    success = 0
    failed = 0

    for index, job in enumerate(jobs, start=1):
        print(f"[{index}/{len(jobs)}] {job.config_path}")
        print(f"  输出目录：{job.out_dir}")

    print("\n开始并行渲染...\n")

    max_workers = min(len(jobs), 4)
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            success, failed = _consume_futures(executor, jobs)
    except (OSError, PermissionError):
        print("提示: 当前环境不支持进程并行，已自动切换为线程模式。")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            success, failed = _consume_futures(executor, jobs)

    print(f"\n完成：成功 {success} 个，失败 {failed} 个。")
    if open_target and success > 0:
        open_path(open_target)

    return 0 if failed == 0 else 1


def main() -> None:
    if len(sys.argv) <= 1:
        print("请传入一个 JSON 文件或文件夹路径。")
        raise SystemExit(1)
    raise SystemExit(run_jobs(Path(arg) for arg in sys.argv[1:]))


if __name__ == "__main__":
    main()
