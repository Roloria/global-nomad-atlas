#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心页面串联海报生成器
========================
读取四张核心页截图（默认 /tmp/shot_*.png，1280×800 浅色版），生成自包含 HTML 海报
（截图 base64 内嵌，单文件可分发）。品牌条、动线连接符、CTA、页脚齐备。

用法：
  1. 用浏览器对新站四页截图 → /tmp/shot_{home,index,city,en}.png
  2. python3 tools/make_showcase_poster.py
输出：宣传/海报_核心页面串联_GlobalNomadAtlas.html
"""
import base64
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SHOTS_DIR = Path("/tmp")
OUT = PROJECT / "宣传" / "海报_核心页面串联_GlobalNomadAtlas.html"
LOGO = PROJECT / "docs" / "assets" / "logo.png"
BASE = "https://roloria.github.io/global-nomad-atlas"

SHOTS = [
    ("shot_home.png", "01 · 官网入口", "三大支柱 · 共建故事 · 一句话讲清项目",
     f"{BASE}/home/"),
    ("shot_index.png", "02 · 城市榜单", "80 城 × 12 维加权评分 · 汇率切换 · 区域/国家/排名筛选 · 可排序",
     f"{BASE}/"),
    ("shot_city.png", "03 · 城市详情", "每城一页：综合分 · 12 维明细 · 签证速览 · 最佳季节 —— canonical + hreflang 双语 SEO",
     f"{BASE}/city/chiang-mai/"),
    ("shot_en.png", "04 · English Edition", "Global Nomad Atlas —— 面向国际游民圈的可收录英文版，CN / EN 原地切换",
     f"{BASE}/en/"),
]
ARROWS = ["从官网进入榜单", "点开任意城市 ↗", "右上角 CN / EN 切换"]


def b64(p: Path) -> str:
    return base64.b64encode(p.read_bytes()).decode()


def build() -> Path:
    logo64 = b64(LOGO)
    sections, connectors = [], []
    for i, (img, title, desc, url) in enumerate(SHOTS):
        no, name = title.split(" · ", 1)
        sections.append(f'''
    <section class="beat">
      <div class="beat-head">
        <div class="beat-no">{no}</div>
        <div>
          <h2>{name}</h2>
          <p>{desc}</p>
        </div>
      </div>
      <figure class="browser">
        <div class="bar"><i></i><i></i><i></i><span>{url}</span></div>
        <img src="data:image/png;base64,{b64(SHOTS_DIR / img)}" alt="{title}">
      </figure>
    </section>''')
        if i < len(ARROWS):
            connectors.append(f'''
    <div class="connector"><span class="line"></span><span class="tag">{ARROWS[i]}</span><span class="line"></span><span class="dot">▼</span></div>''')
    beats = ""
    for i, s in enumerate(sections):
        beats += s + (connectors[i] if i < len(connectors) else "")

    html = HTML_HEAD.replace("__LOGO_B64__", logo64) + beats + HTML_TAIL
    OUT.write_text(html, encoding="utf-8")
    return OUT


HTML_HEAD = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>全球数字游民城市评分榜 · 核心页面串联海报 | Global Nomad Atlas</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#faf9f5;--bg2:#f0eee6;--card:#ffffff;--ink:#23272d;--ink2:#5c6470;--ink3:#8a929e;--line:#e5e1d8;--terra:#c96442}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;line-height:1.6}
.poster{max-width:920px;margin:0 auto;padding:56px 28px 64px}
.brand{display:flex;align-items:center;gap:12px;margin-bottom:26px}
.brand img{width:44px;height:44px;border-radius:50%;border:1px solid var(--line);box-shadow:0 2px 8px rgba(35,39,45,.06)}
.brand .zh{font-size:20px;font-weight:800;letter-spacing:.02em}
.brand .en{font-size:12px;color:var(--ink3);letter-spacing:.14em;text-transform:uppercase;margin-top:1px}
.brand .divider{width:1px;height:26px;background:var(--line);margin:0 2px}
.eyebrow{font-size:12px;letter-spacing:.35em;color:var(--terra);font-weight:700}
h1{font-family:Georgia,"Noto Serif SC","Songti SC",serif;font-size:46px;line-height:1.28;margin:18px 0 14px}
h1 em{font-style:normal;color:var(--terra)}
.lede{font-size:15px;color:var(--ink2);max-width:640px}
.nums{display:flex;flex-wrap:wrap;gap:10px;margin:26px 0 8px}
.num{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 18px}
.num b{font-size:22px;font-variant-numeric:tabular-nums}
.num span{font-size:12px;color:var(--ink3);margin-left:6px}
.rule{height:1px;background:var(--line);margin:34px 0}
.beat{margin-top:8px}
.beat-head{display:flex;gap:16px;align-items:baseline;margin:26px 0 14px}
.beat-no{font-family:Georgia,serif;font-size:15px;color:var(--terra);border:1.5px solid var(--terra);border-radius:999px;padding:2px 13px;font-weight:700;white-space:nowrap}
.beat-head h2{font-family:Georgia,"Noto Serif SC",serif;font-size:24px}
.beat-head p{font-size:13px;color:var(--ink2);margin-top:2px}
.browser{border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 14px 40px rgba(35,39,45,.08);background:var(--card)}
.browser .bar{display:flex;align-items:center;gap:6px;padding:9px 14px;background:var(--bg2);border-bottom:1px solid var(--line)}
.browser .bar i{width:10px;height:10px;border-radius:50%;background:#ddd6c8}
.browser .bar i:nth-child(1){background:#e8a098}.browser .bar i:nth-child(2){background:#e8c898}.browser .bar i:nth-child(3){background:#9fc9a0}
.browser .bar span{margin-left:10px;font-size:11px;color:var(--ink3);font-family:ui-monospace,Menlo,monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.browser img{display:block;width:100%;height:auto}
.connector{display:flex;align-items:center;gap:14px;margin:26px 0 4px;padding-left:4px}
.connector .line{flex:1;height:0;border-top:2px dashed var(--line)}
.connector .tag{font-size:12px;color:var(--terra);background:rgba(201,100,66,.08);border:1px solid rgba(201,100,66,.25);border-radius:999px;padding:4px 14px;font-weight:600;white-space:nowrap}
.connector .dot{color:var(--terra);font-size:13px}
.cta-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:30px}
.btn{display:inline-block;padding:10px 20px;border-radius:12px;font-size:14px;font-weight:600;text-decoration:none;border:1px solid var(--line);background:var(--card);color:var(--ink)}
.btn.primary{background:var(--terra);border-color:var(--terra);color:#fff}
footer{margin-top:44px;padding-top:22px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;align-items:baseline}
footer .slogan{font-family:Georgia,"Noto Serif SC",serif;font-size:17px}
footer .meta{font-size:12px;color:var(--ink3)}
@media(max-width:640px){h1{font-size:32px}.beat-head{flex-direction:column;gap:6px}}
@media print{.poster{padding-top:24px}}
</style>
</head>
<body>
<div class="poster">
  <div class="brand">
    <img src="data:image/png;base64,__LOGO_B64__" alt="牛马迁移指南 logo">
    <div>
      <div class="zh">牛马迁移指南</div>
      <div class="en">Global Nomad Atlas</div>
    </div>
    <div class="divider"></div>
    <div style="font-size:12px;color:var(--ink3);letter-spacing:.3em;font-weight:700;">全球数字游民城市评分榜</div>
  </div>
  <div class="eyebrow">OPEN DATA · COMMUNITY MAINTAINED · 开源共建</div>
  <h1>你的下一座城，<br>不该靠<em>运气</em>选。</h1>
  <p class="lede">一份由全球数字游民亲手维护的开放城市数据库——评分公式公开，人人可编辑，每一次改动都留痕、可回滚、永久开源。以下四个核心页面，串起一次完整的选城旅程。</p>
  <div class="nums">
    <div class="num"><b>80</b><span>座城市</span></div>
    <div class="num"><b>40</b><span>国家 / 地区</span></div>
    <div class="num"><b>12</b><span>评分维度</span></div>
    <div class="num"><b>60</b><span>社区地图</span></div>
    <div class="num"><b>CN / EN</b><span>双语切换</span></div>
  </div>
  <div class="rule"></div>
'''

HTML_TAIL = '''
  <div class="cta-row">
    <a class="btn primary" href="https://roloria.github.io/global-nomad-atlas/">打开城市榜单</a>
    <a class="btn" href="https://roloria.github.io/global-nomad-atlas/home/">项目官网</a>
    <a class="btn" href="https://docs.qq.com/sheet/DREppWERNRWdwcXRR">腾讯文档共建表</a>
    <a class="btn" href="https://github.com/Roloria/global-nomad-atlas">GitHub</a>
  </div>
  <footer>
    <div class="slogan">你的下一座城，不该靠运气选。</div>
    <div class="meta">🐮 牛马迁移指南 · Global Nomad Atlas · 开源数据，公式可复算 · 2026-09</div>
  </footer>
</div>
</body>
</html>
'''

if __name__ == "__main__":
    out = build()
    print(f"生成: {out} ({out.stat().st_size // 1024} KB)")
