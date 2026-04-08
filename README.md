# 小红书图文自动制作

项目已整合为「封面制作 + 正文制作」双模块，并提供统一入口。

## 快速开始

1. 双击 `双击启动操作台.command`
2. 在总控页选择你要做的模块：
- 傻瓜封面
- 高级封面
- 日富正文
- 半夏正文

也可以运行：

```bash
npm run studio
```

## 模块说明

- 封面模块：用于封面图（标题驱动，支持单模板或双模板下载）
- 正文模块：用于正文页批量排版出图（支持原始文本解析、多页导出）

## 常用命令

```bash
npm run studio                 # 总控页（推荐）
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
├── bin/
│   └── open-studio.command
├── scripts/
│   └── generate-cover.js
├── web/
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
├── 双击启动操作台.command
└── README.md
```

## 兼容入口

根目录旧文件名仍可继续使用，会自动跳转到新路径：

- `傻瓜一键出图.html`
- `一键出图操作台.html`
- `日富一日新封面.html`
- `半夏新封面.html`
- `日富正文出图.html`
- `半夏正文出图.html`

## 常见问题

- 只打开页面不下载：常见原因是浏览器拦截自动下载。优先使用页面按钮手动触发下载。
- 两个封面区分：下载文件名后缀分别为 `-日富.png` 和 `-半夏.png`。
