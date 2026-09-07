#!/usr/bin/env node
/**
 * 从 docs/index.html（榜单网站的单一数据源）提取内嵌 JSON，
 * 生成小程序数据模块 miniprogram/miniprogram/data/*.js。
 *
 * 用法：node tools/build_miniprogram_data.js
 * 每次网站数据更新后重新运行即可同步小程序。
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const HTML = path.join(ROOT, "docs", "index.html");
const OUT = path.join(ROOT, "miniprogram", "miniprogram", "data");

const html = fs.readFileSync(HTML, "utf8");

function extract(name) {
  const m = html.match(new RegExp(`const ${name} = (\\[[\\s\\S]*?\\]);`));
  if (!m) throw new Error(`未在 docs/index.html 中找到 ${name}`);
  const data = JSON.parse(m[1]);
  return data;
}

const cities = extract("CITIES_DATA");
const communities = extract("COMMUNITIES_DATA");

if (!cities.length || !communities.length) {
  throw new Error("提取结果为空，请检查 docs/index.html 数据行");
}

fs.mkdirSync(OUT, { recursive: true });

const banner = (name, src) =>
  `// ⚠️ 自动生成文件：由 tools/build_miniprogram_data.js 从 ${src} 提取，请勿手改。\n` +
  `// 数据更新流程：更新 data/*.csv → 同步到 docs/index.html → 重新运行 node tools/build_miniprogram_data.js\n`;

fs.writeFileSync(
  path.join(OUT, "cities.js"),
  banner("CITIES_DATA", "docs/index.html CITIES_DATA") + `module.exports = ` + JSON.stringify(cities) + `;\n`
);
fs.writeFileSync(
  path.join(OUT, "communities.js"),
  banner("COMMUNITIES_DATA", "docs/index.html COMMUNITIES_DATA") + `module.exports = ` + JSON.stringify(communities) + `;\n`
);

console.log(`✓ cities.js      ${cities.length} 座城市`);
console.log(`✓ communities.js ${communities.length} 个社区`);
console.log(`输出目录: ${OUT}`);
