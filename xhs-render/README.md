# 小红书图文本地批量排版工具

一个纯本地运行的 Python 命令行工具，用 JSON 批量渲染小红书图文卡片，包含封面和多张内页，不依赖 AI 出图。

## 环境依赖

- Python 3.9+
- Pillow 10+
- 字体：Noto Serif CJK SC（思源宋体）Regular + Bold

字体安装：

- macOS：`brew install font-noto-serif-cjk-sc`
- Windows：从 Google Fonts 下载 Noto Serif CJK SC 并安装到系统字体目录

## 快速开始

最省事的方式：

1. 在仓库根目录双击对应系统的网页版启动文件
2. 选一个 JSON 文件、直接选整个 JSON 文件夹，或者把 JSON 文本直接粘贴到网页里
3. 等它自动出图并打开输出目录

如果你把 JSON 文件或整个 JSON 文件夹直接拖到 `双击启动本地排版.app` 上，也会直接开始出图。

也可以在 `xhs-render` 目录里手动运行无界面批量入口：

```bash
python3 easy_render_cli.py ../json/你的文件.json
```

如果你更想直接在浏览器里操作：

```bash
python3 web_ui.py
```

如果你更习惯命令行，仍然可以继续用下面这些命令：

```bash
cd xhs-render
python3 -m pip install -r requirements.txt
python3 render.py examples/banxia_example.json
```

再跑另一套风格：

```bash
python3 render.py examples/rifu_example.json
```

如果要自定义输出目录：

```bash
python3 render.py examples/banxia_example.json --out ./output/banxia
```

如果不传 `--out`，程序会自动按“封面标题-排版风格”创建目录，例如：

```bash
python3 render.py examples/banxia_example.json
```

默认会输出到：

```text
xhs-render/output/贪污手段-半夏
```

## 命令行

```bash
python render.py <config.json> [--out OUTPUT_DIR] [--assets ASSETS_DIR]
```

- `config.json`：图文配置文件
- `--out`：输出目录；不传时自动保存到 `./output/封面标题-风格`
- `--assets`：底图目录，默认 `./assets`

## 傻瓜版界面

- 启动文件： [easy_render_cli.py](/Users/工作/vibe%20coding/小红书图文笔记自动制作/xhs-render/easy_render_cli.py)
- AppleScript 源文件： [silent_launcher.applescript](/Users/工作/vibe%20coding/小红书图文笔记自动制作/xhs-render/silent_launcher.applescript)
- 无终端双击入口： [双击启动本地排版.app](/Users/工作/vibe%20coding/小红书图文笔记自动制作/双击启动本地排版.app)
- 备用入口： [双击启动本地排版.command](/Users/工作/vibe%20coding/小红书图文笔记自动制作/双击启动本地排版.command)
- Windows 双击入口： [双击启动本地排版-Windows.vbs](/Users/工作/vibe%20coding/小红书图文笔记自动制作/双击启动本地排版-Windows.vbs)
- Windows 备用入口： [双击启动本地排版-Windows.bat](/Users/工作/vibe%20coding/小红书图文笔记自动制作/双击启动本地排版-Windows.bat)

功能：

- 用 macOS 原生选择框选单个 JSON 出图
- 用 macOS 原生选择框选整个文件夹批量出图
- 自动按“封面标题-排版风格”分配输出目录，避免互相覆盖
- 运行完成后可一键打开输出目录
- 可直接打开 JSON 目录和 AI 提示模板

说明：

- 如果你不想看到终端窗口，请优先双击 `.app`
- `.command` 现在仍然保留，主要用于排错或手动查看运行过程
- Windows 上优先双击 `.vbs`，这样通常不会弹黑窗口
- 如果 Windows 上需要排错或看报错，再改用 `.bat`

## 本地网页版

- 服务脚本： [web_ui.py](/Users/工作/vibe%20coding/小红书图文笔记自动制作/xhs-render/web_ui.py)
- macOS 启动： [双击启动网页版.command](/Users/工作/vibe%20coding/小红书图文笔记自动制作/双击启动网页版.command)
- Windows 启动： [双击启动网页版-Windows.vbs](/Users/工作/vibe%20coding/小红书图文笔记自动制作/双击启动网页版-Windows.vbs)
- Windows 备用： [双击启动网页版-Windows.bat](/Users/工作/vibe%20coding/小红书图文笔记自动制作/双击启动网页版-Windows.bat)

网页版特点：

- 浏览器里直接上传单个 JSON、多选 JSON 或整个文件夹
- 支持直接粘贴 JSON 文本，不用先新建文件再上传
- 粘贴 JSON 时可在网页里直接强制指定“半夏 / 日富”，避免 `{style}` 占位符没替换时出不了图
- 支持批量渲染，并在页面里显示结果预览
- 自动生成 ZIP 下载链接
- 结果统一落在 `xhs-render/output/webui`
- 每个结果子目录会尽量自动命名成“封面标题-排版风格”
- 不需要手动处理空格路径和命令参数

如果你想长期跨 macOS / Windows 共用，我更建议优先用这版。

## 跨平台启动建议

### macOS

- 推荐： [双击启动本地排版.app](/Users/工作/vibe%20coding/小红书图文笔记自动制作/双击启动本地排版.app)
- 备用： [双击启动本地排版.command](/Users/工作/vibe%20coding/小红书图文笔记自动制作/双击启动本地排版.command)

### Windows

- 推荐： [双击启动本地排版-Windows.vbs](/Users/工作/vibe%20coding/小红书图文笔记自动制作/双击启动本地排版-Windows.vbs)
- 备用： [双击启动本地排版-Windows.bat](/Users/工作/vibe%20coding/小红书图文笔记自动制作/双击启动本地排版-Windows.bat)

Windows 使用前提：

- 先安装 Python 3
- 安装时勾选 `Add python.exe to PATH`
- 若双击 `.vbs` 没反应，可先双击 `.bat` 看报错

## 目录说明

```text
xhs-render/
├── render.py
├── job_runner.py
├── styles.py
├── easy_render.py
├── easy_render_cli.py
├── web_ui.py
├── requirements.txt
├── README.md
├── assets/
│   ├── banxia_bg.jpg
│   └── rifu_bg.jpg
├── examples/
│   ├── banxia_example.json
│   └── rifu_example.json
└── output/
```

## JSON 字段说明

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `style` | string | 是 | 排版风格：`banxia` 或 `rifu`；此字段仅控制排版布局 |
| `content_style` | string | 否 | 内容风格元数据（可选）：用于标记内容类型（如 `guofeng`、`xuanhuan` 等），不影响排版，由 AI 生成时使用 |
| `cover_top_text` | string | 否 | 封面上方小字；不传时使用风格默认文案 |
| `cover_title` | string | 是 | 封面主标题，渲染时会自动包上中文弯引号 |
| `cover_bottom_text` | string | 否 | 封面底部小字；不传时使用风格默认文案 |
| `pages` | array | 是 | 内页数组，每项对应一张图 |
| `pages[].title` | string | 是 | 当前内页标题 |
| `pages[].items` | array | 是 | 当前页内容 |
| `pages[].type` | string | 否 | 可选 `auto` / `list` / `compare` / `tag`，默认 `auto` |

完整示例：

```json
{
  "style": "banxia",
  "cover_top_text": "宅斗桥段用的",
  "cover_title": "贪污手段",
  "pages": [
    {
      "title": "页标题",
      "type": "auto",
      "items": ["示例内容"]
    }
  ]
}
```

封面建议：

- `cover_top_text` 建议写成短提示，优先类似“写小说可用的”“可以写进小说里的”“写小说必存的”
- `cover_top_text` 尽量控制在 6 到 10 个汉字左右，不要写成长句或整段宣传语
- `cover_title` 尽量压缩到 2 到 5 个汉字，这样更容易一行展示，也更像小红书封面主标题
- 如果 `cover_title` 太长，程序会优先缩字号，实在放不下才会自动分成两行

## 三种页型示例

普通列表 `list`：

```json
{
  "title": "台词素材",
  "items": [
    "台词一",
    "台词二",
    "台词三"
  ]
}
```

对比组 `compare`：

```json
{
  "title": "写法升级",
  "items": [
    {
      "normal": "他很生气。",
      "better": "他指节发白，一字未说。"
    }
  ]
}
```

分类标签 `tag`：

```json
{
  "title": "贪污分类",
  "items": [
    "【名目类】火耗、鼠耗、脚钱",
    "【手法类】虚报、冒领、克扣"
  ]
}
```

## 风格参数

### `banxia`

- 内页尺寸：`1242 × 1656`
- 封面尺寸：`1080 × 1350`
- 主色：`#282832`
- 内页左右边距：`90px`
- 标题字号 / 行高：`50 / 68`
- 正文字号 / 行高：`43 / 60`

### `rifu`

- 内页尺寸：`1532 × 2048`
- 封面尺寸：`1532 × 2048`
- 主色：`#1a1a1a`
- 内页左右边距：`82px`
- 标题字号 / 行高：`68 / 106`
- 正文字号 / 行高：`46 / 86`

## 输出规则

- 封面固定输出为 `封面.jpg`
- 内页从 `第2页.jpg` 开始编号
- 输出格式为 JPEG，质量 `92`
- 每张图都会在控制台打印日志，例如：

```text
✓ /abs/path/output/第2页.jpg (y=1208, safe=1596)
```

- 如果内容超出安全区，会继续出图，但控制台会打印警告

## AI 生成 JSON 的推荐模板

仓库里已经放了一份可直接复制的模板：

- [ai_json_prompt_template.txt](/Users/工作/vibe%20coding/小红书图文笔记自动制作/xhs-render/ai_json_prompt_template.txt)

推荐替换这几个占位词再发给 AI：

- `{style_label}`：填内容风格，例如”古风””现言””玄幻””悬疑””校园””都市””仙侠””通用”
- `{topic}`：填你的主题
- `{page_count}`：填 `7页` 或 `8页`

这版模板专门强化了几件事：

- 封面上方小字 `cover_top_text` 必须跟主题走，不再固定
- 封面大字 `cover_title` 必须压缩到 2 到 5 个字，减少封面失衡的情况
- 正文标点规则更严格，标题类字段不带标点，正文类字段必须自然收尾
- 正文每页信息密度更高，但按页型分档限量，避免”机械凑满”
- 模板会优先逼 AI 产出”小众、冷门、带机制”的素材，而不是泛泛的热门设定词

模板中的双字段设计：

- `style` 字段必须是 `banxia` 或 `rifu`（排版布局风格，由工具渲染时使用）
- `content_style` 字段用于记录内容风格元数据（如 `guofeng`、`xuanhuan` 等），不影响实际排版
- 这样 AI 生成的 JSON 既符合模板要求，又能被工具直接渲染，无需额外修改
- 如果 JSON 中有 `content_style` 字段，工具会自动忽略它，不会产生渲染错误

使用提醒：

- 如果你走网页版粘贴 JSON，工具会自动移除 `content_style` 字段（如果存在的话），你可以选择覆盖 `style` 值
- 如果你走命令行直渲染 JSON 文件，`style` 必须是 `banxia / rifu`；`content_style` 会被自动移除
- 本工具的排版仍然只有 `banxia / rifu` 两套，`content_style` 仅用于内容分类记录，不扩展排版能力

## 排版默认值调整

为了让正文画面更舒展、文字在画面里更“占版”，默认样式已经做过一轮放宽：

- 正文行高调大
- 列表、标签、对比组之间的间距调大
- 标题整体上移一点，减少上方留白

如果你直接用旧 JSON 重新渲染，不改内容，也会看到版面比之前更松、更满。

示例：

```json
{
  "style": "banxia",
  "cover_top_text": "宅斗高能用的",
  "cover_title": "捉奸桥段",
  "pages": [
    {
      "title": "常见抓现行场景",
      "type": "list",
      "items": [
        "......"
      ]
    }
  ]
}
```

## 常见问题

### 1. 字体找不到

症状：程序启动后直接报错，提示未找到 Noto Serif CJK SC / 思源宋体。

解决：

- macOS 先执行 `brew install font-noto-serif-cjk-sc`
- Windows 确认字体已经安装到系统字体目录
- 如果你已经安装过，重新打开终端再运行一次

### 2. 中文显示异常或像乱码

通常是因为程序回退到了错误字体，或者系统没有成功加载思源宋体。优先确认 Regular 和 Bold 两个字重都已安装。

### 3. 内容太多怎么办

程序会在每页渲染后检查最终 `y` 坐标，超过 `H - 60` 时打印警告。建议把当前页拆成两页，或者删掉 1 到 2 条过长条目。

## 说明

- `job_runner.py` 集中管理任务扫描、输出目录命名和子进程渲染，GUI / CLI / Web UI 共用
- `styles.py` 集中管理风格参数，后续扩展第三种风格时直接新增配置即可
- `render.py` 已实现字体查找、像素级换行、混合字重同行排版、封面自适应缩放和三种页型自动识别
