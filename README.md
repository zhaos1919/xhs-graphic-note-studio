# 小红书图文笔记自动制作

本项目是小红书图文笔记的制作工具集，包含两套能力：纯 Python 本地排版（推荐）和 Node.js 浏览器模板出图（主要用于封面与模板页）。

## 快速开始：推荐方案 xhs-render（Python 本地排版）

如果你想一次性生成 **封面 + 多张内页**，使用这个方案：

1. **双击启动**（推荐）：
   - macOS：双击 `双击启动本地排版.app`
   - Windows：双击 `双击启动本地排版-Windows.vbs`

2. **选择 JSON 文件或粘贴 JSON 文本**，自动出图

3. **结果保存到 `xhs-render/output/` 目录**

详细说明请查看 **[`xhs-render/README.md`](xhs-render/README.md)**。

### xhs-render 的特点

- 纯 Python + Pillow，无需浏览器，运行更快
- 生成完整的图文卡片：**1 张封面 + 多张内页**
- 支持两种排版风格：`半夏`（1080×1350）和 `日富`（1532×2048）
- 直接支持 JSON 批量渲染，支持命令行、GUI、Web UI 三种入口
- GUI、CLI、Web UI 共用同一套任务调度逻辑，行为更一致
- 输出高质量 JPEG，适合直接上传小红书

---

## 备选方案：浏览器模板出图（Node.js，仅封面）

如果你只需要 **生成单个封面**，可以用这个方案：

1. 双击 `双击启动操作台.command`
2. 在总控页选择你要做的模块：
   - 选题自动工坊（自动生成文本 + 封面）
   - 傻瓜封面
   - 高级封面
   - 日富正文（基于浏览器模板）
   - 半夏正文（基于浏览器模板）

也可以运行：

```bash
npm run studio
```

### 浏览器模板的特点

- 基于 Node.js + Playwright + HTML 模板
- 仅支持生成 **单页或双页封面**
- 需要启动本地浏览器
- 不支持多内页的批量排版

## 常用命令

### xhs-render（推荐）

```bash
# 最简单：GUI 双击启动
双击启动本地排版.app  （macOS）
双击启动本地排版-Windows.vbs  （Windows）

# Web UI
python3 xhs-render/web_ui.py

# 命令行
cd xhs-render
python3 render.py examples/banxia_example.json
python3 render.py examples/rifu_example.json
python3 render.py <config.json> --out ./output/<目录名>
```

### 浏览器模板（Node.js，仅封面）

```bash
npm run studio                 # 总控页
npm run studio:auto            # 选题自动工坊
npm run studio:cover           # 傻瓜封面
npm run studio:advanced        # 高级封面
npm run studio:body:richu      # 日富正文
npm run studio:body:banxia     # 半夏正文
npm run generate -- --title "你的标题"   # 命令行封面出图
```

## Vercel 部署

方式一：网页控制台（推荐）

1. 把项目推到 GitHub 仓库
2. 登录 Vercel，点击 `Add New Project`
3. 选择该仓库并导入
4. Root Directory 选择仓库根目录（当前目录）
5. 直接 Deploy

说明：项目已包含 `vercel.json`，会自动把 `/` 跳转到 `web/studio/index.html`，并提供这些短链接：

- `/studio`
- `/studio/auto`
- `/cover`
- `/cover/advanced`
- `/body/richu`
- `/body/banxia`

方式二：CLI

```bash
npx vercel
npx vercel --prod
```

首次会有交互式提问，按默认选项即可。

## 项目结构

```text
.
├── index.html
├── vercel.json
├── .vercelignore
├── package.json
├── README.md
│
├── bin/
│   ├── open-local-render.command
│   ├── open-local-render.bat
│   ├── open-local-web.command
│   ├── open-local-web.bat
│   └── open-studio.command
├── scripts/
│   └── generate-cover.js
├── web/                          # 浏览器模板出图（Node.js）
│   ├── studio/
│   │   ├── index.html
│   │   ├── simple.html
│   │   └── advanced.html
│   ├── templates/
│   │   ├── richu-cover.html
│   │   └── banxia-cover.html
│   └── body/
│       ├── richu-body.html
│       └── banxia-body.html
│
├── xhs-render/                   # 本地 Python 排版（推荐）
│   ├── render.py
│   ├── job_runner.py             # GUI / CLI / Web UI 共用任务层
│   ├── styles.py
│   ├── easy_render.py
│   ├── easy_render_cli.py
│   ├── web_ui.py
│   ├── requirements.txt
│   ├── README.md
│   ├── assets/
│   │   ├── banxia_bg.jpg
│   │   └── rifu_bg.jpg
│   ├── examples/
│   │   ├── banxia_example.json
│   │   └── rifu_example.json
│   └── output/
│
├── json/                         # JSON 配置示例
│   ├── 日富/
│   └── 半夏/
├── prompt/                       # AI 提示词模板
│
├── 双击启动操作台.command         # 启动浏览器模板
├── 双击启动本地排版.app           # 启动 xhs-render（macOS）
├── 双击启动本地排版.command       # 启动 xhs-render（macOS 备用）
├── 双击启动本地排版-Windows.vbs   # 启动 xhs-render（Windows）
├── 双击启动本地排版-Windows.bat   # 启动 xhs-render（Windows 备用）
├── 双击启动网页版.command         # 启动 xhs-render Web UI（macOS）
└── 双击启动网页版-Windows.vbs     # 启动 xhs-render Web UI（Windows）
```

## 兼容入口

根目录旧文件名仍可继续使用，会自动跳转到新路径：

- `傻瓜一键出图.html`
- `一键出图操作台.html`
- `日富一日新封面.html`
- `半夏新封面.html`
- `日富正文出图.html`
- `半夏正文出图.html`

补充说明：

- 根目录双击脚本主要是用户入口，实际逻辑统一放在 `bin/` 和 `xhs-render/`
- `xhs-render/output/` 是本地排版的主要结果目录

## 如何选择？

| 需求 | 推荐方案 |
|------|---------|
| 生成完整的图文卡片（封面 + 多内页） | **xhs-render**（Python） |
| 只需要单个或双页封面 | 浏览器模板（Node.js） |
| 想用 JSON 批量渲染多个图文 | **xhs-render**（Python） |
| 希望离线运行，不用启动浏览器 | **xhs-render**（Python） |
| 想在网页里操作，可视化编辑 | 浏览器模板（Node.js）或 xhs-render Web UI |
| AI 自动生成内容结构 | 浏览器模板（Node.js 的"选题自动工坊"） |

## 常见问题

**xhs-render 相关**

- 字体找不到：参考 [`xhs-render/README.md` 的常见问题章节](xhs-render/README.md#常见问题)
- 如何从 AI 生成的内容直接出图：使用 AI 提示词模板生成 JSON，然后用 xhs-render 渲染

**浏览器模板相关**

- 只打开页面不下载：常见原因是浏览器拦截自动下载。优先使用页面按钮手动触发下载。
- 两个封面区分：下载文件名后缀分别为 `-日富.png` 和 `-半夏.png`。
