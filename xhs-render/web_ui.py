#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import shutil
import sys
import threading
import urllib.parse
import webbrowser
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from job_runner import RenderJob, dedupe_dir, open_path, run_render_job, suggest_output_name


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RUNS_ROOT = SCRIPT_DIR / "output" / "webui"
HOST = "127.0.0.1"


HTML_PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>小红书本地排版网页版</title>
  <style>
    :root {
      --bg: linear-gradient(180deg, #f7f6f2 0%, #eef5f0 100%);
      --panel: rgba(255,255,255,0.86);
      --line: rgba(34, 34, 34, 0.08);
      --text: #25252f;
      --muted: #67656b;
      --accent: #2b5f4d;
      --accent-soft: #e8f0eb;
      --danger: #a04242;
      --shadow: 0 24px 60px rgba(38, 38, 54, 0.10);
      --serif: "Songti SC", "STSong", "Noto Serif CJK SC", serif;
      --sans: "PingFang SC", "Microsoft YaHei", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: var(--sans);
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(148, 211, 189, 0.28), transparent 34%),
        radial-gradient(circle at bottom right, rgba(234, 214, 173, 0.25), transparent 30%),
        var(--bg);
      min-height: 100vh;
    }
    .shell {
      width: min(1180px, calc(100vw - 32px));
      margin: 24px auto;
      display: grid;
      gap: 18px;
    }
    .hero, .panel {
      background: var(--panel);
      backdrop-filter: blur(16px);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow);
    }
    .hero {
      padding: 28px 30px;
      display: grid;
      gap: 10px;
    }
    .eyebrow {
      font-size: 13px;
      letter-spacing: 0.18em;
      color: var(--accent);
    }
    h1 {
      margin: 0;
      font-family: var(--serif);
      font-size: clamp(30px, 5vw, 52px);
      font-weight: 700;
      line-height: 1.05;
    }
    .lead {
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
      max-width: 820px;
      font-size: 15px;
    }
    .grid {
      display: grid;
      grid-template-columns: 1.12fr 0.88fr;
      gap: 18px;
    }
    .panel {
      padding: 24px;
    }
    .section-title {
      margin: 0 0 8px;
      font-family: var(--serif);
      font-size: 28px;
      font-weight: 700;
    }
    .section-desc {
      margin: 0 0 18px;
      color: var(--muted);
      line-height: 1.7;
      font-size: 14px;
    }
    .upload-grid {
      display: grid;
      gap: 14px;
    }
    .picker {
      border: 1px dashed rgba(43, 95, 77, 0.26);
      background: linear-gradient(180deg, rgba(232,240,235,0.82) 0%, rgba(255,255,255,0.72) 100%);
      border-radius: 22px;
      padding: 18px;
      display: grid;
      gap: 10px;
    }
    .picker strong {
      font-size: 17px;
    }
    .picker span {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.65;
    }
    .picker input[type="file"] {
      width: 100%;
      font: inherit;
    }
    .text-input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 14px 16px;
      font: inherit;
      resize: vertical;
      background: rgba(255,255,255,0.86);
      color: var(--text);
    }
    .text-input.name {
      min-height: 48px;
      resize: none;
      padding-top: 12px;
      padding-bottom: 12px;
    }
    .text-input.json {
      min-height: 240px;
      font-family: "SFMono-Regular", "Menlo", "Consolas", monospace;
      line-height: 1.6;
      font-size: 13px;
    }
    .select-input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 12px 16px;
      font: inherit;
      background: rgba(255,255,255,0.86);
      color: var(--text);
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }
    button, .ghost-link {
      appearance: none;
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      font: inherit;
      cursor: pointer;
      text-decoration: none;
      transition: transform .18s ease, box-shadow .18s ease, opacity .18s ease;
    }
    button:hover, .ghost-link:hover {
      transform: translateY(-1px);
    }
    .primary {
      background: var(--accent);
      color: #fff;
      box-shadow: 0 12px 24px rgba(43, 95, 77, 0.18);
    }
    .secondary {
      background: #fff;
      color: var(--text);
      border: 1px solid var(--line);
    }
    .meta {
      display: grid;
      gap: 10px;
      align-content: start;
    }
    .meta-card {
      border-radius: 22px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.72);
      padding: 18px;
    }
    .meta-card h3 {
      margin: 0 0 8px;
      font-size: 18px;
      font-family: var(--serif);
    }
    .meta-card p, .meta-card li {
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
      font-size: 14px;
    }
    .meta-card ul {
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 8px;
    }
    .selection {
      margin-top: 16px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.7;
      white-space: pre-wrap;
      min-height: 54px;
    }
    .status {
      margin-top: 16px;
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(255,255,255,0.82);
      border: 1px solid var(--line);
      white-space: pre-wrap;
      line-height: 1.7;
      min-height: 64px;
      font-size: 14px;
    }
    .status.error {
      color: var(--danger);
      border-color: rgba(160, 66, 66, 0.18);
      background: rgba(255, 245, 245, 0.82);
    }
    .results {
      display: none;
      grid-column: 1 / -1;
      padding: 24px;
    }
    .results.active {
      display: block;
    }
    .result-top {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 18px;
      align-items: center;
    }
    .result-list {
      display: grid;
      gap: 18px;
    }
    .result-item {
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 18px;
      background: rgba(255,255,255,0.72);
    }
    .result-item h3 {
      margin: 0 0 8px;
      font-size: 20px;
      font-family: var(--serif);
    }
    .result-links {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 12px 0 16px;
    }
    .path-note {
      margin: 0 0 12px;
      color: var(--muted);
      line-height: 1.7;
      font-size: 13px;
      word-break: break-all;
    }
    .thumb-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 12px;
    }
    .thumb {
      display: grid;
      gap: 8px;
      text-decoration: none;
      color: inherit;
    }
    .thumb img {
      width: 100%;
      aspect-ratio: 3 / 4;
      object-fit: cover;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: #fff;
    }
    .thumb span {
      font-size: 12px;
      color: var(--muted);
      line-height: 1.5;
      word-break: break-all;
    }
    .validation-status {
      margin-top: 8px;
      padding: 10px 12px;
      border-radius: 12px;
      font-size: 13px;
      line-height: 1.5;
      min-height: 22px;
      display: none;
    }
    .validation-status.valid {
      display: block;
      background: rgba(76, 175, 80, 0.1);
      color: #2e7d32;
      border: 1px solid rgba(76, 175, 80, 0.3);
    }
    .validation-status.invalid {
      display: block;
      background: rgba(244, 67, 54, 0.1);
      color: #c62828;
      border: 1px solid rgba(244, 67, 54, 0.3);
    }
    .text-input.json.invalid {
      border-color: rgba(244, 67, 54, 0.5);
    }
    .text-input.json.valid {
      border-color: rgba(76, 175, 80, 0.5);
    }
    @media (max-width: 900px) {
      .grid {
        grid-template-columns: 1fr;
      }
      .shell {
        width: min(100vw - 18px, 1180px);
      }
      .hero, .panel {
        border-radius: 22px;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="eyebrow">LOCAL WEB STUDIO</div>
      <h1>小红书图文本地排版<br />网页版</h1>
      <p class="lead">这版适合 Windows 和 macOS 共用。你只需要在浏览器里上传一个 JSON、多个 JSON，或者整个 JSON 文件夹，然后点一下开始出图。结果会直接生成在本地项目的 <code>xhs-render/output/webui</code> 下面，并在页面里显示预览和下载入口。</p>
    </section>

    <section class="panel">
      <h2 class="section-title">上传并出图</h2>
      <p class="section-desc">支持单个 JSON、多选 JSON 和整文件夹上传。上传文件夹时，建议用 Chrome / Edge，浏览器会保留文件夹里的 JSON 层级。</p>
      <div class="upload-grid">
        <label class="picker">
          <strong>选择单个或多个 JSON</strong>
          <span>适合一次处理几篇内容。可以直接多选多个 `.json` 文件。</span>
          <input id="jsonFiles" type="file" accept=".json,application/json" multiple />
        </label>

        <label class="picker">
          <strong>选择整个 JSON 文件夹</strong>
          <span>适合批量处理。浏览器会把文件夹里的所有 JSON 一次性传上来。</span>
          <input id="jsonFolder" type="file" accept=".json,application/json" webkitdirectory directory multiple />
        </label>

        <div class="picker">
          <strong>或者直接粘贴 JSON 文本</strong>
          <span>适合直接粘贴 AI 返回的 JSON。支持粘贴带 <code>```json</code> 外层代码块的内容，系统会自动剥掉。</span>
          <input id="jsonName" class="text-input name" type="text" placeholder="可选：给这次粘贴内容起个名字，比如 宿命设定.json" />
          <select id="pasteStyle" class="select-input">
            <option value="auto">排版风格：跟随 JSON 原文</option>
            <option value="banxia">排版风格：半夏</option>
            <option value="rifu">排版风格：日富</option>
          </select>
          <textarea id="jsonText" class="text-input json" placeholder="把 JSON 直接粘贴到这里，不用先新建文件。"></textarea>
          <div id="jsonValidation" class="validation-status"></div>
        </div>
      </div>

      <div class="actions">
        <button id="renderBtn" class="primary">开始出图</button>
        <button id="clearBtn" class="secondary" type="button">清空选择</button>
        <a class="ghost-link secondary" href="/open/json" target="_blank">打开 JSON 目录</a>
        <a class="ghost-link secondary" href="/open/output" target="_blank">打开输出目录</a>
        <a class="ghost-link secondary" href="/open/prompt" target="_blank">打开 AI 模板</a>
      </div>

      <div id="selection" class="selection">还没有选择文件。</div>
      <div id="status" class="status">等待操作。</div>
    </section>

    <aside class="panel meta">
      <div class="meta-card">
        <h3>适合谁用</h3>
        <p>不想碰命令行、路径、参数的人。尤其适合 Windows 用户，浏览器里选文件就能跑。</p>
      </div>
      <div class="meta-card">
        <h3>使用提醒</h3>
        <ul>
          <li>第一次使用前，先安装思源宋体。</li>
          <li>封面上方小字尽量短，优先“写小说可用的”。</li>
          <li>封面主标题尽量压缩到 2 到 5 个字。</li>
          <li>如果浏览器里传了很多文件，页面会按批次统一生成结果。</li>
        </ul>
      </div>
      <div class="meta-card">
        <h3>结果位置</h3>
        <p>所有网页版结果都会放在 <code>xhs-render/output/webui</code> 里，每次生成一个独立批次目录，方便回看和打包。</p>
      </div>
    </aside>

    <section id="results" class="panel results">
      <div class="result-top">
        <div>
          <h2 class="section-title" style="margin-bottom: 6px;">本次结果</h2>
          <p id="resultMeta" class="section-desc" style="margin: 0;">等待生成。</p>
        </div>
        <div class="result-links">
          <a id="zipLink" class="ghost-link primary" href="#" download>下载本次结果 ZIP</a>
          <a id="batchFolderLink" class="ghost-link secondary" href="#" target="_blank">打开本次结果目录</a>
        </div>
      </div>
      <div id="resultList" class="result-list"></div>
    </section>
  </div>

  <script>
    const jsonFilesInput = document.getElementById('jsonFiles');
    const jsonFolderInput = document.getElementById('jsonFolder');
    const jsonNameInput = document.getElementById('jsonName');
    const pasteStyleInput = document.getElementById('pasteStyle');
    const jsonTextInput = document.getElementById('jsonText');
    const renderBtn = document.getElementById('renderBtn');
    const clearBtn = document.getElementById('clearBtn');
    const selectionEl = document.getElementById('selection');
    const statusEl = document.getElementById('status');
    const resultsEl = document.getElementById('results');
    const resultMetaEl = document.getElementById('resultMeta');
    const resultListEl = document.getElementById('resultList');
    const zipLinkEl = document.getElementById('zipLink');
    const batchFolderLinkEl = document.getElementById('batchFolderLink');

    function collectFiles() {
      const files = [];
      const seen = new Set();
      for (const file of Array.from(jsonFilesInput.files || [])) {
        const key = `single::${file.name}::${file.size}`;
        if (!seen.has(key)) {
          files.push({ file, relativePath: file.name });
          seen.add(key);
        }
      }
      for (const file of Array.from(jsonFolderInput.files || [])) {
        const relativePath = file.webkitRelativePath || file.name;
        const key = `folder::${relativePath}::${file.size}`;
        if (!seen.has(key)) {
          files.push({ file, relativePath });
          seen.add(key);
        }
      }
      return files;
    }

    function renderSelection() {
      const files = collectFiles();
      const hasPastedText = Boolean((jsonTextInput.value || '').trim());
      if (!files.length && !hasPastedText) {
        selectionEl.textContent = '还没有选择文件。';
        return;
      }
      const lines = [];
      if (files.length) {
        lines.push(`已选择 ${files.length} 个文件：`);
        lines.push(...files.slice(0, 8).map(item => `- ${item.relativePath}`));
        if (files.length > 8) {
          lines.push(`- 还有 ${files.length - 8} 个文件未展开`);
        }
      }
      if (hasPastedText) {
        const pastedName = (jsonNameInput.value || '').trim() || '粘贴内容.json';
        lines.push(`- 已填写粘贴内容：${pastedName}`);
        if (pasteStyleInput.value !== 'auto') {
          lines.push(`- 已强制排版：${pasteStyleInput.value === 'banxia' ? '半夏' : '日富'}`);
        }
      }
      selectionEl.textContent = lines.join('\\n');
    }

    function setStatus(text, isError = false) {
      statusEl.textContent = text;
      statusEl.classList.toggle('error', isError);
    }

    function resetResults() {
      resultsEl.classList.remove('active');
      resultMetaEl.textContent = '等待生成。';
      resultListEl.innerHTML = '';
      zipLinkEl.href = '#';
      batchFolderLinkEl.href = '#';
    }

    function createResultCard(item) {
      const card = document.createElement('article');
      card.className = 'result-item';

      const title = document.createElement('h3');
      title.textContent = item.name;
      card.appendChild(title);

      const log = document.createElement('p');
      log.className = 'section-desc';
      log.style.margin = '0';
      log.textContent = item.log || '无日志。';
      card.appendChild(log);

      if (item.folder_path) {
        const path = document.createElement('p');
        path.className = 'path-note';
        path.textContent = `保存位置：${item.folder_path}`;
        card.appendChild(path);
      }

      const links = document.createElement('div');
      links.className = 'result-links';

      const folderLink = document.createElement('a');
      folderLink.className = 'ghost-link secondary';
      folderLink.href = item.folder_url;
      folderLink.target = '_blank';
      folderLink.textContent = '打开这个结果目录';
      links.appendChild(folderLink);

      card.appendChild(links);

      const grid = document.createElement('div');
      grid.className = 'thumb-grid';
      for (const image of item.images) {
        const link = document.createElement('a');
        link.className = 'thumb';
        link.href = image.url;
        link.target = '_blank';

        const img = document.createElement('img');
        img.src = image.url;
        img.alt = image.name;
        link.appendChild(img);

        const caption = document.createElement('span');
        caption.textContent = image.name;
        link.appendChild(caption);
        grid.appendChild(link);
      }
      card.appendChild(grid);
      return card;
    }

    async function submitRender() {
      const files = collectFiles();
      const pastedText = (jsonTextInput.value || '').trim();
      const pastedName = (jsonNameInput.value || '').trim();
      if (!files.length && !pastedText) {
        setStatus('请先选择 JSON 文件，或者直接粘贴 JSON 文本。', true);
        return;
      }

      renderBtn.disabled = true;
      clearBtn.disabled = true;
      resetResults();
      setStatus('正在出图，请稍等……如果文件较多，浏览器会停一会儿，这是正常的。');

      const formData = new FormData();
      files.forEach(item => {
        formData.append('json_files', item.file, item.relativePath);
      });
      if (pastedText) {
        formData.append('json_text', pastedText);
        formData.append('json_name', pastedName);
        formData.append('style_override', pasteStyleInput.value || 'auto');
      }

      try {
        const response = await fetch('/render', {
          method: 'POST',
          body: formData
        });
        const data = await response.json();
        if (!response.ok || !data.ok) {
          throw new Error(data.error || '出图失败。');
        }

        setStatus(data.message || '出图完成。');
        resultsEl.classList.add('active');
        resultMetaEl.textContent = data.summary;
        zipLinkEl.href = data.zip_url;
        batchFolderLinkEl.href = data.batch_folder_url;
        resultListEl.innerHTML = '';
        setStatus(`${data.message || '出图完成。'}\n已保存到：${data.primary_output_path || data.batch_folder_path}`);
        data.results.forEach(item => {
          resultListEl.appendChild(createResultCard(item));
        });
        resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } catch (error) {
        setStatus(String(error.message || error), true);
      } finally {
        renderBtn.disabled = false;
        clearBtn.disabled = false;
      }
    }

    function clearAll() {
      jsonFilesInput.value = '';
      jsonFolderInput.value = '';
      jsonNameInput.value = '';
      pasteStyleInput.value = 'auto';
      jsonTextInput.value = '';
      renderSelection();
      resetResults();
      setStatus('等待操作。');
    }

    function validateJsonInput() {
      const jsonValidationEl = document.getElementById('jsonValidation');
      const inputText = (jsonTextInput.value || '').trim();

      // Clear validation if empty
      if (!inputText) {
        jsonValidationEl.className = 'validation-status';
        jsonValidationEl.textContent = '';
        jsonTextInput.classList.remove('valid', 'invalid');
        return;
      }

      // Strip code block markers if present
      let cleanedText = inputText;
      if (cleanedText.startsWith('```')) {
        const lines = cleanedText.split('\\n');
        if (lines.length > 1) {
          // Remove first line with ```
          lines.shift();
          // Remove last line if it's ```
          if (lines[lines.length - 1].trim() === '```') {
            lines.pop();
          }
          cleanedText = lines.join('\\n').trim();
        }
      }

      // Try to parse JSON
      try {
        JSON.parse(cleanedText);
        jsonValidationEl.className = 'validation-status valid';
        jsonValidationEl.textContent = '✓ JSON 语法正确';
        jsonTextInput.classList.remove('invalid');
        jsonTextInput.classList.add('valid');
      } catch (error) {
        // Extract line and column info from error message
        let errorMsg = '✗ JSON 语法错误';
        const match = error.message.match(/position (\d+)/);
        if (match) {
          const position = parseInt(match[1], 10);
          const lines = cleanedText.substring(0, position).split('\\n');
          const line = lines.length;
          const column = lines[lines.length - 1].length + 1;
          errorMsg = `✗ JSON 语法错误：第 ${line} 行第 ${column} 列`;
        }
        jsonValidationEl.className = 'validation-status invalid';
        jsonValidationEl.textContent = errorMsg;
        jsonTextInput.classList.remove('valid');
        jsonTextInput.classList.add('invalid');
      }
    }

    jsonFilesInput.addEventListener('change', renderSelection);
    jsonFolderInput.addEventListener('change', renderSelection);
    jsonNameInput.addEventListener('input', renderSelection);
    pasteStyleInput.addEventListener('change', renderSelection);
    jsonTextInput.addEventListener('input', () => {
      validateJsonInput();
      renderSelection();
    });
    renderBtn.addEventListener('click', submitRender);
    clearBtn.addEventListener('click', clearAll);
  </script>
</body>
</html>
"""

def normalize_json_filename(name: str) -> str:
    cleaned = (name or "").strip()
    if not cleaned:
        return "粘贴内容.json"
    cleaned = cleaned.replace("\\", "/").split("/")[-1]
    if not cleaned.lower().endswith(".json"):
        cleaned += ".json"
    return cleaned


def normalize_pasted_json_text(text: str) -> str:
    cleaned = (text or "").strip().lstrip("\ufeff")
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def apply_style_override(parsed_json: object, file_name: str, style_override: str) -> object:
    if not isinstance(parsed_json, dict):
        return parsed_json

    patched = dict(parsed_json)

    # 移除 content_style 字段(它是元数据,与排版无关,由 render.py 的 load_config 处理)
    patched.pop("content_style", None)

    override = (style_override or "").strip()
    if override in {"banxia", "rifu"}:
        patched["style"] = override
        return patched

    raw_style = str(patched.get("style", "")).strip()

    # 如果 style 缺失或还是占位符,尝试推断或报错
    if not raw_style or (raw_style.startswith("{") and raw_style.endswith("}")):
        lower_name = file_name.lower()
        if "半夏" in file_name or "banxia" in lower_name:
            patched["style"] = "banxia"
        elif "日富" in file_name or "rifu" in lower_name or "richu" in lower_name:
            patched["style"] = "rifu"
        else:
            # 如果无法推断且 style 缺失,使用默认或返回需要用户指定风格的提示
            if not patched.get("style"):
                patched["style"] = ""  # 让 render.py 的 load_config 处理错误提示

    return patched


def make_job_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def ensure_run_dirs(job_id: str) -> Dict[str, Path]:
    job_root = RUNS_ROOT / job_id
    input_root = job_root / "inputs"
    output_root = job_root / "outputs"
    input_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)
    return {"job_root": job_root, "input_root": input_root, "output_root": output_root}


def cleanup_old_runs(runs_root: Path, keep: int = 20) -> None:
    """Clean up old batch runs, keeping only the most recent ones.

    Keeps the most recent `keep` directories (sorted lexicographically by name).
    Older directories are deleted using shutil.rmtree with error handling.
    """
    try:
        if not runs_root.exists():
            return

        # List all subdirectories
        subdirs = sorted([d for d in runs_root.iterdir() if d.is_dir()])

        # If there are more than `keep` directories, delete the oldest ones
        if len(subdirs) > keep:
            to_delete = subdirs[: len(subdirs) - keep]
            for old_dir in to_delete:
                try:
                    shutil.rmtree(old_dir)
                except Exception:
                    # Silently ignore deletion errors to prevent crashing
                    pass
    except Exception:
        # Silently ignore any errors in cleanup to prevent crashing the app
        pass


def json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def html_response(handler: BaseHTTPRequestHandler, payload: str, status: int = 200) -> None:
    data = payload.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def file_response(handler: BaseHTTPRequestHandler, file_path: Path) -> None:
    if not file_path.exists() or not file_path.is_file():
        handler.send_error(HTTPStatus.NOT_FOUND, "File not found")
        return
    content_type, _ = mimetypes.guess_type(str(file_path))
    content_type = content_type or "application/octet-stream"
    stat = file_path.stat()
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(stat.st_size))
    handler.end_headers()
    with file_path.open("rb") as fh:
        shutil.copyfileobj(fh, handler.wfile)


def to_url_path(path: Path) -> str:
    relative = path.relative_to(RUNS_ROOT).as_posix()
    return "/runs/" + urllib.parse.quote(relative)


def to_open_url(path: Path) -> str:
    relative = path.relative_to(RUNS_ROOT).as_posix()
    return "/open/run?path=" + urllib.parse.quote(relative)


class FormField:
    """Represents a field in a multipart form (file or text)."""
    def __init__(self, name: str, value: str | BytesIO, filename: Optional[str] = None):
        self.name = name
        self.filename = filename
        self.file = value if isinstance(value, BytesIO) else BytesIO(value.encode('utf-8') if isinstance(value, str) else value)
        self.value = value if isinstance(value, str) else None

    def __str__(self) -> str:
        if isinstance(self.value, str):
            return self.value
        return ""


class MultipartForm:
    """Container for parsed multipart form data with dict-like access."""
    def __init__(self):
        self.fields: Dict[str, List[FormField]] = {}

    def add_field(self, name: str, field: FormField) -> None:
        if name not in self.fields:
            self.fields[name] = []
        self.fields[name].append(field)

    def __contains__(self, key: str) -> bool:
        return key in self.fields

    def __getitem__(self, key: str) -> Any:
        """Returns list of fields if key exists, else returns empty list."""
        return self.fields.get(key, [])

    def getfirst(self, key: str, default: str = "") -> str:
        """Get first field value as string, or default if not found."""
        fields = self.fields.get(key, [])
        if not fields:
            return default
        field = fields[0]
        if isinstance(field.value, str):
            return field.value
        return str(field) or default


def parse_multipart_form(rfile, headers: dict, content_length: int) -> MultipartForm:
    """
    Parse multipart form data from request body.

    Args:
        rfile: File-like object to read request body from
        headers: HTTP headers dict (case-insensitive lookup)
        content_length: Content-Length header value as integer

    Returns:
        MultipartForm object with parsed fields
    """
    form = MultipartForm()

    # Get Content-Type header (case-insensitive)
    content_type = headers.get("Content-Type", "")
    if not content_type:
        for key, value in headers.items():
            if key.lower() == "content-type":
                content_type = value
                break

    # Extract boundary from Content-Type
    boundary_match = None
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary_match = part[9:].strip('"')
            break

    if not boundary_match:
        return form

    boundary = boundary_match.encode('utf-8')
    body = rfile.read(content_length)

    # Split by boundary
    parts = body.split(b'--' + boundary)

    for part in parts[1:-1]:  # Skip first empty part and last closing boundary
        if not part or part == b'--\r\n' or part == b'--':
            continue

        # Remove trailing boundary marker and newlines
        if part.endswith(b'--\r\n'):
            part = part[:-4]
        elif part.endswith(b'--\n'):
            part = part[:-3]
        elif part.endswith(b'\r\n'):
            part = part[:-2]
        elif part.endswith(b'\n'):
            part = part[:-1]

        # Split headers from content
        try:
            header_end = part.index(b'\r\n\r\n')
            header_section = part[:header_end]
            content = part[header_end + 4:]
        except ValueError:
            try:
                header_end = part.index(b'\n\n')
                header_section = part[:header_end]
                content = part[header_end + 2:]
            except ValueError:
                continue

        # Parse headers
        field_name = None
        filename = None

        header_lines = header_section.split(b'\r\n')
        if not header_lines:
            header_lines = header_section.split(b'\n')

        for header_line in header_lines:
            if not header_line:
                continue

            if b':' not in header_line:
                continue

            key, value = header_line.split(b':', 1)
            key = key.strip().lower()
            value = value.strip()

            if key == b'content-disposition':
                # Parse: form-data; name="field_name"; filename="file.json"
                value_str = value.decode('utf-8', errors='ignore')
                for segment in value_str.split(';'):
                    segment = segment.strip()
                    if segment.startswith('name='):
                        field_name = segment[5:].strip('"')
                    elif segment.startswith('filename='):
                        filename = segment[9:].strip('"')

        if not field_name:
            continue

        # Create field object
        if filename:
            # File field
            field = FormField(field_name, BytesIO(content), filename=filename)
        else:
            # Text field
            field_value = content.decode('utf-8', errors='ignore')
            field = FormField(field_name, field_value)

        form.add_field(field_name, field)

    return form


class WebUIHandler(BaseHTTPRequestHandler):
    server_version = "XHSRenderWeb/1.0"

    def log_message(self, format: str, *args) -> None:
        return

    def do_HEAD(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            data = HTML_PAGE.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            html_response(self, HTML_PAGE)
            return

        if path.startswith("/runs/"):
            relative = urllib.parse.unquote(path.removeprefix("/runs/"))
            target = (RUNS_ROOT / relative).resolve()
            if RUNS_ROOT.resolve() not in target.parents and target != RUNS_ROOT.resolve():
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
                return
            file_response(self, target)
            return

        if path == "/open/output":
            RUNS_ROOT.mkdir(parents=True, exist_ok=True)
            open_path(RUNS_ROOT)
            html_response(self, "<meta charset='utf-8'><p>已尝试打开输出目录，可以关闭这个页面。</p>")
            return

        if path == "/open/run":
            relative = urllib.parse.parse_qs(parsed.query).get("path", [""])[0].strip("/")
            if not relative:
                html_response(self, "<meta charset='utf-8'><p>没有收到要打开的结果路径。</p>", status=400)
                return
            target = (RUNS_ROOT / urllib.parse.unquote(relative)).resolve()
            root = RUNS_ROOT.resolve()
            if target != root and root not in target.parents:
                self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
                return
            if not target.exists():
                html_response(self, "<meta charset='utf-8'><p>目标结果目录不存在，可能已经被移动或删除。</p>", status=404)
                return
            open_path(target)
            html_response(self, "<meta charset='utf-8'><p>已尝试打开本次结果目录，可以关闭这个页面。</p>")
            return

        if path == "/open/json":
            target = PROJECT_ROOT / "json"
            if target.exists():
                open_path(target)
                html_response(self, "<meta charset='utf-8'><p>已尝试打开 JSON 目录，可以关闭这个页面。</p>")
            else:
                html_response(self, "<meta charset='utf-8'><p>当前项目里没有找到 json 目录。</p>", status=404)
            return

        if path == "/open/prompt":
            target = SCRIPT_DIR / "ai_json_prompt_template.txt"
            if target.exists():
                open_path(target)
                html_response(self, "<meta charset='utf-8'><p>已尝试打开 AI 模板，可以关闭这个页面。</p>")
            else:
                html_response(self, "<meta charset='utf-8'><p>没有找到 AI 模板文件。</p>", status=404)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/render":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            json_response(self, {"ok": False, "error": "请求格式不正确，请重新选择文件后再试。"}, status=400)
            return

        # Get Content-Length header
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            content_length = 0

        if content_length <= 0:
            json_response(self, {"ok": False, "error": "请求格式不正确，请重新选择文件后再试。"}, status=400)
            return

        # Parse multipart form data
        form = parse_multipart_form(self.rfile, self.headers, content_length)

        raw_files = form["json_files"] if "json_files" in form else []
        if not isinstance(raw_files, list):
            raw_files = [raw_files]

        valid_fields = [field for field in raw_files if getattr(field, "filename", None)]
        json_text = form.getfirst("json_text", "")
        json_name = form.getfirst("json_name", "")
        style_override = form.getfirst("style_override", "auto")
        has_pasted_text = bool(str(json_text).strip())
        if not valid_fields and not has_pasted_text:
            json_response(self, {"ok": False, "error": "没有收到 JSON 文件，也没有检测到粘贴的 JSON 文本。"}, status=400)
            return

        try:
            payload = self._handle_render(
                valid_fields,
                json_text=json_text,
                json_name=json_name,
                style_override=style_override,
            )
            json_response(self, payload)
        except Exception as exc:  # pragma: no cover
            json_response(self, {"ok": False, "error": str(exc)}, status=500)

    def _handle_render(
        self,
        file_fields: List[FormField],
        json_text: str = "",
        json_name: str = "",
        style_override: str = "auto",
    ) -> dict:
        RUNS_ROOT.mkdir(parents=True, exist_ok=True)
        cleanup_old_runs(RUNS_ROOT)
        job_id = make_job_id()
        dirs = ensure_run_dirs(job_id)
        results: List[dict] = []
        success = 0
        failed = 0

        entries: List[dict] = []
        used_output_dirs: set[Path] = set()

        for field in file_fields:
            entries.append({"kind": "file", "field": field})

        pasted_text = normalize_pasted_json_text(json_text)
        if pasted_text:
            try:
                parsed = json.loads(pasted_text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"粘贴的 JSON 解析失败：第 {exc.lineno} 行第 {exc.colno} 列附近有格式问题。") from None
            file_name = normalize_json_filename(json_name)
            parsed = apply_style_override(parsed, file_name, style_override)
            entries.append(
                {
                    "kind": "text",
                    "file_name": file_name,
                    "parsed_json": parsed,
                }
            )

        for index, entry in enumerate(entries, start=1):
            if entry["kind"] == "file":
                field = entry["field"]
                raw_name = field.filename or f"upload-{index}.json"
                relative_name = raw_name.replace("\\", "/").strip("/")
                file_name = Path(relative_name).name
                if not file_name.lower().endswith(".json"):
                    continue

                input_path = dirs["input_root"] / f"{index:03d}-{file_name}"
                with input_path.open("wb") as fh:
                    shutil.copyfileobj(field.file, fh)
            else:
                file_name = entry["file_name"]
                input_path = dirs["input_root"] / f"{index:03d}-{file_name}"
                with input_path.open("w", encoding="utf-8") as fh:
                    json.dump(entry["parsed_json"], fh, ensure_ascii=False, indent=2)
                    fh.write("\n")

            personalized_name = suggest_output_name(input_path)
            item_out_dir = dedupe_dir(dirs["output_root"] / personalized_name, used_output_dirs)
            execution = run_render_job(
                RenderJob(config_path=input_path, out_dir=item_out_dir),
                python_exe=sys.executable,
                job_index=index,
                total=len(entries),
            )
            raw_log = execution.output.strip()
            clean_log = raw_log if raw_log else "没有输出日志。"
            if entry["kind"] == "text":
                clean_log = f"来源：网页直接粘贴\n{clean_log}"

            if execution.returncode == 0:
                image_files = sorted(item_out_dir.glob("*.jpg"))
                if image_files:
                    success += 1
                    results.append(
                        {
                            "name": file_name,
                            "log": clean_log,
                            "folder_url": to_open_url(item_out_dir),
                            "folder_path": str(item_out_dir),
                            "images": [
                                {"name": image.name, "url": to_url_path(image)}
                                for image in image_files
                            ],
                        }
                    )
                else:
                    failed += 1
                    results.append(
                        {
                            "name": file_name,
                            "log": clean_log + "\n未检测到输出图片，已按失败处理。",
                            "folder_url": to_open_url(item_out_dir),
                            "folder_path": str(item_out_dir),
                            "images": [],
                        }
                    )
            else:
                failed += 1
                results.append(
                    {
                        "name": file_name,
                        "log": clean_log,
                        "folder_url": to_open_url(dirs["job_root"]),
                        "folder_path": str(dirs["job_root"]),
                        "images": [],
                    }
                )

        if not results:
            raise RuntimeError("没有找到可处理的 JSON 文件。")

        archive_base = dirs["job_root"] / "results"
        shutil.make_archive(str(archive_base), "zip", root_dir=dirs["output_root"])

        summary = f"本次共处理 {len(results)} 个文件，成功 {success} 个，失败 {failed} 个。"
        primary_output_path = ""
        if success == 1:
            for item in results:
                if item.get("images"):
                    primary_output_path = item.get("folder_path", "")
                    break
        message = "出图完成。" if success > 0 else "本次没有成功生成图片。"
        return {
            "ok": True,
            "message": message,
            "summary": summary,
            "results": results,
            "zip_url": to_url_path(archive_base.with_suffix(".zip")),
            "batch_folder_url": to_open_url(dirs["job_root"]),
            "batch_folder_path": str(dirs["job_root"]),
            "primary_output_path": primary_output_path,
        }


def open_browser_later(url: str) -> None:
    def runner() -> None:
        webbrowser.open(url)

    threading.Timer(0.7, runner).start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="小红书本地排版网页版")
    parser.add_argument("--host", default=HOST, help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=8765, help="监听端口，默认 8765")
    parser.add_argument("--no-open", action="store_true", help="启动后不自动打开浏览器")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    cleanup_old_runs(RUNS_ROOT)
    server = ThreadingHTTPServer((args.host, args.port), WebUIHandler)
    url = f"http://{args.host}:{args.port}"
    print(f"小红书本地排版网页版已启动：{url}")
    print("按 Ctrl+C 可停止服务。")
    if not args.no_open:
        open_browser_later(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
