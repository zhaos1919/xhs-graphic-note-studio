#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { spawnSync } = require('node:child_process');

const cwd = process.cwd();
const templateMap = {
  richu: 'web/templates/richu-cover.html',
  sunrise: 'web/templates/richu-cover.html',
  '日富': 'web/templates/richu-cover.html',
  banxia: 'web/templates/banxia-cover.html',
  absurd: 'web/templates/banxia-cover.html',
  '半夏': 'web/templates/banxia-cover.html'
};

function parseArgs(argv) {
  const args = {
    title: '',
    template: 'richu',
    top: '',
    bottom: '',
    filename: '',
    printOnly: false
  };
  const positionals = [];

  for (let i = 0; i < argv.length; i += 1) {
    const cur = argv[i];
    if (!cur.startsWith('--')) {
      positionals.push(cur);
      continue;
    }

    const [key, inlineValue] = cur.split('=');
    const nextValue = inlineValue ?? argv[i + 1];
    const useNext = inlineValue == null;

    if (key === '--title' && nextValue) {
      args.title = nextValue;
      if (useNext) i += 1;
    } else if (key === '--template' && nextValue) {
      args.template = nextValue;
      if (useNext) i += 1;
    } else if (key === '--top' && nextValue) {
      args.top = nextValue;
      if (useNext) i += 1;
    } else if (key === '--bottom' && nextValue) {
      args.bottom = nextValue;
      if (useNext) i += 1;
    } else if (key === '--filename' && nextValue) {
      args.filename = nextValue;
      if (useNext) i += 1;
    } else if (key === '--print-only') {
      args.printOnly = true;
    } else if (key === '--help' || key === '-h') {
      args.help = true;
    }
  }

  if (!args.title && positionals.length > 0) {
    args.title = positionals.join(' ');
  }

  return args;
}

function getTemplateFile(templateArg) {
  const key = String(templateArg || '').toLowerCase();
  if (templateMap[key]) {
    return templateMap[key];
  }
  if (templateArg && templateMap[templateArg]) {
    return templateMap[templateArg];
  }
  return templateMap.richu;
}

function printHelp() {
  console.log(`用法:
  npm run generate -- --title "你的标题"
  npm run generate

可选参数:
  --template richu|banxia
  --top "上方文字"
  --bottom "下方文字"
  --filename "导出文件名.png"
  --print-only

示例:
  npm run generate -- --title "普通女孩也能写出高级感" --template banxia
  npm run studio`);
}

function buildUrl(args) {
  if (!args.title) {
    throw new Error('请提供标题：--title "你的标题"');
  }

  const templateFile = getTemplateFile(args.template);
  const templatePath = path.resolve(cwd, templateFile);
  if (!fs.existsSync(templatePath)) {
    throw new Error(`模板文件不存在: ${templatePath}`);
  }
  const pageUrl = new URL(pathToFileURL(templatePath).href);

  pageUrl.searchParams.set('title', args.title);
  pageUrl.searchParams.set('auto', '1');
  if (args.top) pageUrl.searchParams.set('topText', args.top);
  if (args.bottom) pageUrl.searchParams.set('bottomText', args.bottom);
  if (args.filename) pageUrl.searchParams.set('fileName', args.filename);

  return pageUrl.href;
}

function openStudioPage() {
  const candidateNames = [
    'web/studio/index.html',
    'web/studio/simple.html',
    'web/studio/advanced.html',
    '傻瓜一键出图.html',
    '一键出图操作台.html'
  ];
  let studioPath = '';

  for (const name of candidateNames) {
    const fullPath = path.resolve(cwd, name);
    if (fs.existsSync(fullPath)) {
      studioPath = fullPath;
      break;
    }
  }

  if (!studioPath) {
    throw new Error(`未找到操作台文件，请检查: ${candidateNames.join(', ')}`);
  }
  openInChrome(pathToFileURL(studioPath).href);
}

function openInChrome(url) {
  const withChrome = spawnSync('open', ['-a', 'Google Chrome', url], {
    stdio: 'inherit'
  });
  if (withChrome.status === 0) {
    return;
  }

  const fallback = spawnSync('open', [url], {
    stdio: 'inherit'
  });
  if (fallback.status !== 0) {
    throw new Error('无法调用 open 命令打开模板页面');
  }
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    return;
  }

  if (!args.title) {
    openStudioPage();
    console.log('未提供标题，已打开可视化操作台。');
    return;
  }

  const url = buildUrl(args);

  if (args.printOnly) {
    console.log(url);
    return;
  }

  openInChrome(url);
  console.log('已触发自动出图，文件会由浏览器自动下载保存。');
}

try {
  main();
} catch (error) {
  const message = String(error && error.message ? error.message : error);
  console.error(`出错: ${message}`);
  process.exitCode = 1;
}
