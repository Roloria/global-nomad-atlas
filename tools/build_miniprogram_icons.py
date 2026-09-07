#!/usr/bin/env python3
"""
生成小程序 tabBar 图标 PNG 与处理品牌徽章 Logo（tools/build_miniprogram_icons.py）

- 品牌徽章：assets/logo-source.png（牛马徽章，用户提供）→ 裁边缩放为 logo-badge.png，
  徽章自带圆形底色，浅/深主题共用同一张
- Tab 图标：Lucide 风格描边图标 × 4 个配色变体（浅/深 × 普通/选中）

实现：macOS 自带 qlmanage 将 SVG 渲染为白底 PNG，再按
「像素 = 前景色×α + 白×(1-α)」反解 α，重建透明背景（单色图形无损）。

用法：python3 tools/build_miniprogram_icons.py
"""
import os
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "miniprogram", "miniprogram", "assets", "icons")
SOURCE_LOGO = os.path.join(ROOT, "assets", "logo-source.png")
SIZE = 192  # 渲染尺寸（viewBox 24 的 8 倍，显示端 ≤60rpx，足够清晰）
LOGO_SIZE = 288

# 配色变体（与小程序主题令牌一致）
VARIANTS = {
    "": "#98948A",            # 浅色主题 · 未选中
    "-active": "#C96442",     # 浅色主题 · 选中
    "-dark": "#74808D",       # 深色主题 · 未选中
    "-active-dark": "#3BC9DB" # 深色主题 · 选中
}

# Lucide 风格 tab 图标（stroke=2，与官网图标体系同源）
ICONS = {
    # 城市榜：奖杯（榜单/排名，正式风格）
    "tab-city": '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>',
    # 社区地图：地球
    "tab-globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><path d="M2 12h20"/>',
    # 共建：双人（官网 i-users）
    "tab-users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
}


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def svg(stroke_color, body, filled=False):
    if filled:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
                f'width="{SIZE}" height="{SIZE}" fill="{stroke_color}">{body}</svg>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            f'width="{SIZE}" height="{SIZE}" fill="none" stroke="{stroke_color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')


def render(name, color, body, filled=False):
    """渲染 SVG → 白底 PNG → 反解 alpha → 透明 PNG"""
    rgb = hex_rgb(color)
    with tempfile.TemporaryDirectory() as tmp:
        svg_path = os.path.join(tmp, name + ".svg")
        with open(svg_path, "w") as f:
            f.write(svg(color, body, filled))
        subprocess.run(["qlmanage", "-t", "-s", str(SIZE), "-o", tmp, svg_path],
                       check=True, capture_output=True)
        png_path = os.path.join(tmp, name + ".svg.png")
        im = Image.open(png_path).convert("RGB")
        if im.size != (SIZE, SIZE):
            im = im.resize((SIZE, SIZE), Image.LANCZOS)

        # 反解 alpha：选与背景白差异最大的通道，数值最稳
        diffs = [255 - c for c in rgb]
        ch = diffs.index(max(diffs))
        c_ch = rgb[ch]
        px = im.load()
        out = Image.new("RGBA", im.size)
        opx = out.load()
        for y in range(im.size[1]):
            for x in range(im.size[0]):
                m = px[x, y][ch]
                if c_ch == 255:
                    a = 1.0 if m < 255 else 0.0
                else:
                    a = (255 - m) / (255 - c_ch)
                a = max(0.0, min(1.0, a))
                opx[x, y] = (rgb[0], rgb[1], rgb[2], round(a * 255))
        out.save(os.path.join(OUT, name + ".png"))
        return out


def verify(name):
    im = Image.open(os.path.join(OUT, name + ".png")).convert("RGBA")
    px = im.load()
    corner_a = px[1, 1][3]
    opaque = sum(1 for x in range(im.size[0]) for y in range(im.size[1]) if px[x, y][3] > 200)
    return im.size[0], corner_a, opaque


def build_badge():
    """品牌徽章：assets/logo-source.png → logo-badge.png（裁边 + 居中方画布 + 缩放）"""
    im = Image.open(SOURCE_LOGO).convert("RGBA")
    bbox = im.getbbox()
    if not bbox:
        raise SystemExit("logo-source.png 无可见内容")
    im = im.crop(bbox)
    side = max(im.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - im.size[0]) // 2, (side - im.size[1]) // 2))
    canvas = canvas.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
    canvas.save(os.path.join(OUT, "logo-badge.png"))
    print(f"✓ logo-badge.png  {LOGO_SIZE}×{LOGO_SIZE}  ← {os.path.relpath(SOURCE_LOGO, ROOT)}")


def main():
    os.makedirs(OUT, exist_ok=True)
    build_badge()
    jobs = [{"name": n + suffix, "color": color, "body": body, "filled": False}
            for n, body in ICONS.items() for suffix, color in VARIANTS.items()]

    for job in jobs:
        name, color, body, filled = job["name"], job["color"], job["body"], job["filled"]
        render(name, color, body, filled)
        size, corner_a, opaque = verify(name)
        flag = "✓" if corner_a == 0 and opaque > 100 else "✗"
        print(f"{flag} {name}.png  {size}×{size}  角落α={corner_a}  实心像素={opaque}")

    print(f"\n输出目录: {OUT}")


if __name__ == "__main__":
    sys.exit(main())
