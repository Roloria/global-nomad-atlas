#!/usr/bin/env node
/** 小程序静态校验：JS 语法、JSON 合法性、WXML 标签配对、app.json 页面完整性 */
const fs = require("fs");
const path = require("path");

const SRC = path.resolve(__dirname, "..", "miniprogram", "miniprogram");
let errors = [];

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((d) => {
    const p = path.join(dir, d.name);
    return d.isDirectory() ? walk(p) : [p];
  });
}

const files = walk(SRC);

// 1. JS 语法
for (const f of files.filter((f) => f.endsWith(".js"))) {
  try {
    new Function(fs.readFileSync(f, "utf8"));
  } catch (e) {
    errors.push(`[JS] ${path.relative(SRC, f)}: ${e.message}`);
  }
}

// 2. JSON 合法性
for (const f of files.filter((f) => f.endsWith(".json"))) {
  try {
    JSON.parse(fs.readFileSync(f, "utf8"));
  } catch (e) {
    errors.push(`[JSON] ${path.relative(SRC, f)}: ${e.message}`);
  }
}

// 3. WXML 标签配对
const VOID = new Set(["input", "image", "import", "include", "slider", "switch", "icon", "progress", "checkbox", "radio"]);
for (const f of files.filter((f) => f.endsWith(".wxml"))) {
  const src = fs.readFileSync(f, "utf8");
  const stack = [];
  const re = /<\/?([a-zA-Z][\w-]*)((?:"[^"]*"|'[^']*'|[^"'>])*?)(\/?)>/g;
  let m;
  while ((m = re.exec(src))) {
    const [full, tag, attrs, selfClose] = m;
    if (full.startsWith("</")) {
      const top = stack.pop();
      if (top !== tag) errors.push(`[WXML] ${path.relative(SRC, f)}: 期望 </${top}>，实际 </${tag}>`);
    } else if (!selfClose && !VOID.has(tag)) {
      stack.push(tag);
    }
  }
  if (stack.length) errors.push(`[WXML] ${path.relative(SRC, f)}: 未闭合标签 ${stack.join(", ")}`);
}

// 4. app.json 页面/TabBar 完整性
const appJson = JSON.parse(fs.readFileSync(path.join(SRC, "app.json"), "utf8"));
for (const p of appJson.pages) {
  for (const ext of [".js", ".wxml", ".json", ".wxss"]) {
    if (!fs.existsSync(path.join(SRC, p + ext))) errors.push(`[APP] 缺少页面文件 ${p}${ext}`);
  }
}
const tabPages = new Set(appJson.tabBar.list.map((t) => t.pagePath));
for (const p of tabPages) {
  if (!appJson.pages.includes(p)) errors.push(`[APP] tabBar 页面 ${p} 未在 pages 中注册`);
}
if (!fs.existsSync(path.join(SRC, "custom-tab-bar", "index.js")) && appJson.tabBar.custom) {
  errors.push("[APP] tabBar.custom=true 但缺少 custom-tab-bar/index");
}

// 5. 数据一致性
const cities = require(path.join(SRC, "data", "cities.js"));
const communities = require(path.join(SRC, "data", "communities.js"));
if (cities.length !== 80) errors.push(`[DATA] 城市数 ${cities.length} ≠ 80`);
if (communities.length !== 60) errors.push(`[DATA] 社区数 ${communities.length} ≠ 60`);

if (errors.length) {
  console.error("✗ 校验失败：");
  errors.forEach((e) => console.error("  " + e));
  process.exit(1);
} else {
  console.log(`✓ 全部通过：${files.length} 个文件，${cities.length} 城 × ${communities.length} 社区，页面 ${appJson.pages.length} 个`);
}
