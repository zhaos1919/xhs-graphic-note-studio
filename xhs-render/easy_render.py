#!/usr/bin/env python3
from __future__ import annotations

import sys
import threading
from pathlib import Path
from queue import Empty, Queue
from typing import Iterable, List

from job_runner import (
    DEFAULT_OUTPUT_ROOT,
    RenderJob,
    build_jobs_for_targets,
    open_path,
    run_render_job,
)

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except Exception as exc:  # pragma: no cover
    print(
        "当前 Python 缺少 tkinter，无法启动傻瓜版界面。\n"
        "请改用 `python3 render.py 你的json.json`，或安装带 tkinter 的 Python。\n"
        f"原始错误：{exc}"
    )
    raise


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_JSON_ROOT = PROJECT_ROOT / "json"
PROMPT_TEMPLATE = SCRIPT_DIR / "ai_json_prompt_template.txt"


class EasyRenderApp:
    def __init__(self, initial_targets: List[Path] | None = None) -> None:
        self.root = tk.Tk()
        self.root.title("小红书本地排版 · 傻瓜版")
        self.root.geometry("860x640")
        self.root.minsize(760, 560)

        self.log_queue: Queue = Queue()
        self.busy = False
        self.pending_open_path: Path | None = None

        self.status_var = tk.StringVar(value="等待操作：选择一个 JSON 文件，或者直接选整个文件夹批量出图。")
        self.output_var = tk.StringVar(value=str(DEFAULT_OUTPUT_ROOT))

        self._build_ui()
        self.root.after(120, self._poll_queue)

        if initial_targets:
            self.root.after(200, lambda: self._start_from_paths(initial_targets))

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        top = ttk.Frame(self.root, padding=16)
        top.grid(row=0, column=0, sticky="nsew")
        top.columnconfigure(0, weight=1)

        ttk.Label(
            top,
            text="小红书图文傻瓜出图",
            font=("PingFang SC", 20, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            top,
            text=(
                "推荐流程：先让 AI 生成 JSON -> 再来这里选文件出图。\n"
                "不用自己写命令，也不用处理空格路径。选错文件夹时会直接提醒。"
            ),
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        actions = ttk.Frame(self.root, padding=(16, 0, 16, 12))
        actions.grid(row=1, column=0, sticky="ew")
        for idx in range(5):
            actions.columnconfigure(idx, weight=1)

        self.single_btn = ttk.Button(actions, text="选择单个 JSON 出图", command=self.pick_single_json)
        self.batch_btn = ttk.Button(actions, text="选择文件夹批量出图", command=self.pick_json_folder)
        self.output_btn = ttk.Button(actions, text="打开输出目录", command=self.open_output_root)
        self.json_btn = ttk.Button(actions, text="打开 JSON 目录", command=self.open_json_root)
        self.prompt_btn = ttk.Button(actions, text="打开 AI 模板", command=self.open_prompt_template)

        self.single_btn.grid(row=0, column=0, padx=4, sticky="ew")
        self.batch_btn.grid(row=0, column=1, padx=4, sticky="ew")
        self.output_btn.grid(row=0, column=2, padx=4, sticky="ew")
        self.json_btn.grid(row=0, column=3, padx=4, sticky="ew")
        self.prompt_btn.grid(row=0, column=4, padx=4, sticky="ew")

        middle = ttk.Frame(self.root, padding=(16, 0, 16, 0))
        middle.grid(row=2, column=0, sticky="nsew")
        middle.columnconfigure(0, weight=1)
        middle.rowconfigure(1, weight=1)

        info = ttk.LabelFrame(middle, text="当前设置", padding=12)
        info.grid(row=0, column=0, sticky="ew")
        info.columnconfigure(1, weight=1)
        ttk.Label(info, text="默认输出目录：").grid(row=0, column=0, sticky="w")
        ttk.Label(info, textvariable=self.output_var).grid(row=0, column=1, sticky="w")
        ttk.Label(
            info,
            text="单文件会输出到 output/封面标题-风格；批量模式会输出到 output/文件夹名/封面标题-风格。",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        log_frame = ttk.LabelFrame(middle, text="运行日志", padding=12)
        log_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, wrap="word", height=20, font=("Menlo", 12))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.configure(state="disabled")

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        bottom = ttk.Frame(self.root, padding=16)
        bottom.grid(row=3, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)

        ttk.Label(bottom, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

    def log(self, text: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text.rstrip() + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        for widget in (self.single_btn, self.batch_btn, self.output_btn, self.json_btn, self.prompt_btn):
            widget.configure(state=state)

    def pick_single_json(self) -> None:
        path = filedialog.askopenfilename(
            title="选择一个 JSON 文件",
            filetypes=[("JSON 文件", "*.json")],
            initialdir=str(DEFAULT_JSON_ROOT if DEFAULT_JSON_ROOT.exists() else PROJECT_ROOT),
        )
        if path:
            self._start_from_paths([Path(path)])

    def pick_json_folder(self) -> None:
        path = filedialog.askdirectory(
            title="选择一个包含 JSON 的文件夹",
            initialdir=str(DEFAULT_JSON_ROOT if DEFAULT_JSON_ROOT.exists() else PROJECT_ROOT),
        )
        if path:
            self._start_from_paths([Path(path)])

    def open_output_root(self) -> None:
        DEFAULT_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        open_path(DEFAULT_OUTPUT_ROOT)

    def open_json_root(self) -> None:
        target = DEFAULT_JSON_ROOT if DEFAULT_JSON_ROOT.exists() else PROJECT_ROOT
        open_path(target)

    def open_prompt_template(self) -> None:
        if PROMPT_TEMPLATE.exists():
            open_path(PROMPT_TEMPLATE)
        else:
            messagebox.showwarning("未找到模板", f"没有找到模板文件：{PROMPT_TEMPLATE}")

    def _start_from_paths(self, paths: Iterable[Path]) -> None:
        if self.busy:
            return
        try:
            jobs, open_target = build_jobs_for_targets(paths, output_root=DEFAULT_OUTPUT_ROOT)
        except Exception as exc:
            messagebox.showerror("无法开始出图", str(exc))
            return

        if not jobs:
            messagebox.showwarning("没有任务", "没有找到可执行的渲染任务。")
            return

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        self.pending_open_path = open_target
        self.set_busy(True)
        self.status_var.set(f"正在出图：共 {len(jobs)} 个任务，请稍等...")
        self.log(f"开始出图，共 {len(jobs)} 个任务。")

        worker = threading.Thread(target=self._run_jobs, args=(jobs,), daemon=True)
        worker.start()

    def _run_jobs(self, jobs: List[RenderJob]) -> None:
        success = 0
        failed = 0
        for index, job in enumerate(jobs, start=1):
            self.log_queue.put(("log", f"\n[{index}/{len(jobs)}] {job.config_path}"))
            self.log_queue.put(("log", f"输出目录：{job.out_dir}"))
            result = run_render_job(
                job,
                python_exe=sys.executable,
                job_index=index,
                total=len(jobs),
            )
            if result.output.strip():
                self.log_queue.put(("log", result.output.rstrip()))
            if result.returncode == 0:
                success += 1
            else:
                failed += 1
        self.log_queue.put(("done", {"success": success, "failed": failed, "total": len(jobs)}))

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.log_queue.get_nowait()
                if kind == "log":
                    self.log(str(payload))
                elif kind == "done":
                    self._finish(payload)
        except Empty:
            pass
        self.root.after(120, self._poll_queue)

    def _finish(self, payload: dict) -> None:
        self.set_busy(False)
        success = payload["success"]
        failed = payload["failed"]
        total = payload["total"]
        if failed == 0:
            self.status_var.set(f"已完成：{success}/{total} 个任务成功。")
            self.log("\n全部完成。")
            if self.pending_open_path and messagebox.askyesno("出图完成", "已出图完成，是否打开输出目录？"):
                open_path(self.pending_open_path)
        else:
            self.status_var.set(f"已完成：成功 {success}，失败 {failed}。请看日志。")
            messagebox.showwarning("部分任务失败", "有任务出图失败，请看下方日志。")

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    initial_targets = [Path(arg) for arg in sys.argv[1:]]
    app = EasyRenderApp(initial_targets=initial_targets or None)
    app.run()


if __name__ == "__main__":
    main()
