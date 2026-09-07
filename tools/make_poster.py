#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nomadic Cartography — 全球数字游民城市榜 宣传海报生成器（v2）"""
import math, random, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

random.seed(20260821)

# ---------- 路径 ----------
FONT_DIR = "/Users/kevinwang/.workbuddy/skills/canvas-design/canvas-fonts"
CJK_FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
OUT = "/Users/kevinwang/WorkBuddy/数字游民/宣传/数字游民城市榜_海报.png"

# ---------- 画布 ----------
W, H = 2400, 3600
BG = (11, 27, 43)          # #0B1B2B 深空蓝
PANEL = (14, 34, 54)       # 面板
CREAM = (244, 236, 216)    # #F4ECD8 米白
TERRA = (224, 116, 74)     # #E0744A 暖赭
GOLD = (232, 176, 75)      # #E8B04B 金
MUTE = (143, 168, 188)     # #8FA8BC 冷灰蓝
GRID = (143, 168, 188)

img = Image.new("RGB", (W, H), BG)

# ---------- 字体 ----------
def F(name, size):
    return ImageFont.truetype(f"{FONT_DIR}/{name}.ttf", size)
def C(size):
    return ImageFont.truetype(CJK_FONT, size)

F_DISP   = F("BigShoulders-Bold", 250)     # 主标题
F_DISP_S = F("BigShoulders-Bold", 96)
F_KICK  = F("JetBrainsMono-Bold", 34)
F_SUB   = C(46)
F_MONO  = F("JetBrainsMono-Regular", 30)
F_MONO_S= F("JetBrainsMono-Regular", 24)
F_BODY  = C(32)
F_BODY_S= C(26)
F_TAG   = F("WorkSans-Bold", 40)
F_CJK_TAG = C(40)

# ---------- 工具 ----------
def circle(d, cx, cy, r, fill=None, outline=None, width=1):
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=fill, outline=outline, width=width)

def text(d, s, x, y, font, fill, anchor="la"):
    d.text((x, y), s, font=font, fill=fill, anchor=anchor)

def has_cjk(s): return bool(re.search(r'[\u4e00-\u9fff]', s))

def draw_text(d, s, x, y, en_font, cjk_font, fill, anchor="la"):
    """混排：英文用 en_font，中文用 cjk_font"""
    if not has_cjk(s):
        text(d, s, x, y, en_font, fill, anchor)
        return
    # 简单整段用 CJK 字体，避免逐字排版的复杂 baseline 差异
    text(d, s, x, y, cjk_font, fill, anchor)

def vignette(im, strength=0.55):
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([-W*0.25, -H*0.25, W*1.25, H*1.25], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(400))
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(im, Image.blend(im, dark, strength), mask)

# =====================================================================
# 1. 顶部标题区
# =====================================================================
MARGIN = 150
y = 170
text(draw := ImageDraw.Draw(img), "OPEN-SOURCE CITY ATLAS", MARGIN, y, F_KICK, GOLD, "la")
y += 60
lines = ["GLOBAL", "DIGITAL", "NOMAD"]
for i, ln in enumerate(lines):
    text(draw, ln, MARGIN, y + i*220, F_DISP, CREAM, "la")
title_end_y = y + 3*220

sub_x = 1500
text(draw, "80 CITIES", sub_x, 200, F_DISP_S, TERRA, "la")
text(draw, "12 DIMENSIONS", sub_x, 310, F_DISP_S, TERRA, "la")
text(draw, "COMMUNITY-RATED", sub_x, 420, F_DISP_S, TERRA, "la")
text(draw, "全球数字游民城市榜", sub_x, 540, F_SUB, MUTE, "la")
text(draw, "开放共建 · 数据透明 · 开源可追溯", sub_x, 600, F_BODY, MUTE, "la")

draw.line([MARGIN, title_end_y+40, W-MARGIN, title_end_y+40], fill=GRID, width=2)

# =====================================================================
# 2. 世界地图面板
# =====================================================================
MAP_X0, MAP_Y0, MAP_X1, MAP_Y1 = MARGIN, title_end_y+90, W-MARGIN, title_end_y+90+1500
map_w = MAP_X1 - MAP_X0
map_h = MAP_Y1 - MAP_Y0

draw.rounded_rectangle([MAP_X0, MAP_Y0, MAP_X1, MAP_Y1], radius=24, fill=PANEL, outline=GRID, width=2)

def lon2x(lon):  return MAP_X0 + (lon+180)/360 * map_w
def lat2y(lat):  return MAP_Y0 + (85-lat)/145 * map_h

for lon in range(-150, 151, 30):
    x = lon2x(lon)
    draw.line([x, MAP_Y0+10, x, MAP_Y1-10], fill=(GRID[0],GRID[1],GRID[2],60), width=1)
for lat in range(-30, 76, 30):
    yv = lat2y(lat)
    draw.line([MAP_X0+10, yv, MAP_X1-10, yv], fill=(GRID[0],GRID[1],GRID[2],60), width=1)

cities = [
 ("Mexico City",19.43,-99.13,50000),("Bali",-8.65,115.13,30000),("Lisbon",38.72,-9.14,16000),
 ("Barcelona",41.39,2.17,9600),("Shanghai",31.23,121.47,5000),("Dali",25.6,100.27,5000),
 ("Chiang Mai",18.79,98.98,5000),("Beijing",39.90,116.40,4500),("Medellin",6.24,-75.58,4200),
 ("Hangzhou",30.27,120.15,4000),("Shenzhen",22.54,114.06,4000),("Ho Chi Minh",10.82,106.63,3800),
 ("Chengdu",30.57,104.07,3500),("Bangkok",13.76,100.50,3200),("Buenos Aires",-34.60,-58.38,3000),
 ("Hanoi",21.03,105.85,2500),("Bangalore",12.97,77.59,2500),("Tbilisi",41.72,44.78,2400),
 ("Tulum",20.21,-87.46,2400),("Berlin",52.52,13.40,2200),("Las Palmas",28.12,-15.43,2200),
 ("Kuala Lumpur",3.14,101.69,2200),("Playa del Carmen",20.63,-87.08,2000),("Istanbul",41.01,28.98,2000),
 ("Dubai",25.20,55.27,1900),("Phuket",7.88,98.39,1900),("Tokyo",35.68,139.69,1800),
 ("Nanjing",32.06,118.80,1800),("Xi'an",34.34,108.94,1800),("Cape Town",-33.92,18.42,1800),
 ("Rio",-22.91,-43.17,1800),("Goa",15.30,73.96,1800),("Cartagena",10.39,-75.51,1800),
 ("Budapest",47.50,19.04,1700),("Singapore",1.35,103.82,1600),("Prague",50.08,14.44,1600),
 ("Panama City",8.98,-79.52,1600),("Sanya",18.25,109.51,1500),("Kunming",25.04,102.71,1500),
 ("Suzhou",31.30,120.62,1500),("Bansko",41.84,23.49,1500),("Da Nang",16.05,108.22,1500),
 ("Jakarta",-6.21,106.85,1500),("Taipei",25.03,121.57,1400),("Krakow",50.06,19.94,1400),
 ("Lima",-12.05,-77.04,1400),("Porto",41.15,-8.61,1300),("Seoul",37.57,126.98,1300),
 ("Tenerife",28.29,-16.63,1300),("Athens",37.98,23.73,1300),("Penang",5.41,100.33,1300),
 ("Phnom Penh",11.56,104.92,1300),("Tallinn",59.44,24.75,1200),("Xiamen",24.48,118.09,1200),
 ("Qingdao",36.07,120.38,1200),("Lijiang",26.87,100.23,1200),("San Miguel",20.91,-100.74,1200),
 ("Nairobi",-1.29,36.82,1200),("Manila",14.60,120.98,1200),("Madeira",32.76,-16.96,1100),
 ("Split",43.51,16.44,1100),("Florianopolis",-27.60,-48.55,1100),("Oaxaca",17.06,-96.73,1100),
 ("Cebu",10.32,123.90,1100),("Johannesburg",-26.20,28.05,1100),("Yangshuo",24.78,110.49,1000),
 ("Montevideo",-34.90,-56.16,1000),("Belgrade",44.79,20.45,900),("Cabo San Lucas",22.89,-109.92,900),
 ("Siem Reap",13.36,103.86,900),("Samui",9.51,100.00,800),("Sofia",42.70,23.32,800),
 ("Antigua",14.56,-90.73,800),("Marrakech",31.63,-7.99,800),("Abu Dhabi",24.45,54.38,700),
 ("Taghazout",30.52,-9.70,700),("Cairo",30.04,31.24,700),("Kigali",-1.94,30.06,600),
 ("Anji",30.64,119.68,500),("Doha",25.29,51.53,500),
]

def city_r(n): return 3 + 19*math.sqrt(n/50000)

def quad_bezier(p0, p1, p2, steps=40):
    pts = []
    for t in [i/steps for i in range(steps+1)]:
        x = (1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0]
        y = (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1]
        pts.append((x,y))
    return pts

# 航线弧（枢纽城市间，二次贝塞尔平滑曲线）
hubs = {"Lisbon":(38.72,-9.14),"Bangkok":(13.76,100.50),"Mexico City":(19.43,-99.13),
        "Tokyo":(35.68,139.69),"Bali":(-8.65,115.13),"Dubai":(25.20,55.27),"Cape Town":(-33.92,18.42)}
routes = [("Lisbon","Mexico City"),("Lisbon","Bali"),("Bali","Tokyo"),("Dubai","Cape Town"),
          ("Mexico City","Bali"),("Lisbon","Tokyo"),("Dubai","Bangkok")]
for a,b in routes:
    x1,y1 = lon2x(hubs[a][1]), lat2y(hubs[a][0])
    x2,y2 = lon2x(hubs[b][1]), lat2y(hubs[b][0])
    mx,my = (x1+x2)/2, (y1+y2)/2
    dx,dy = x2-x1, y2-y1
    dist = math.hypot(dx,dy)
    if dist>0:
        px,py = -dy/dist, dx/dist
        curve = 0.18 * dist
        cx,cy = mx + px*curve, my + py*curve
        pts = quad_bezier((x1,y1),(cx,cy),(x2,y2))
        draw.line(pts, fill=(GOLD[0],GOLD[1],GOLD[2],55), width=2)

# 图例：光点大小代表游民数
# 城市光点（在 RGBA 层统一绘制后再合成，避免反复转换）
glow_layer = Image.new("RGBA", (W, H), (0,0,0,0))
gd = ImageDraw.Draw(glow_layer)
for name,lat,lon,n in sorted(cities, key=lambda c:c[3]):
    cx, cy = lon2x(lon), lat2y(lat)
    r = city_r(n)
    big = n >= 15000
    gc = GOLD if big else CREAM
    gd.ellipse([cx-r*2.4, cy-r*2.4, cx+r*2.4, cy+r*2.4], fill=(gc[0],gc[1],gc[2],38))
glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(12))
img = Image.alpha_composite(img.convert("RGBA"), glow_layer).convert("RGB")
draw = ImageDraw.Draw(img)

for name,lat,lon,n in cities:
    cx, cy = lon2x(lon), lat2y(lat)
    r = city_r(n)
    big = n >= 15000
    fill = GOLD if big else CREAM
    circle(draw, cx, cy, r, fill=fill)

text(draw, "80 NODES · 6 CONTINENTS · ONE OPEN ATLAS", MAP_X0+24, MAP_Y1-46, F_MONO_S, MUTE, "la")
# 图例
lx, ly = MAP_X1-420, MAP_Y1-46
circle(draw, lx, ly-6, 4, fill=CREAM)
text(draw, "= 1K NOMADS", lx+16, ly-4, F_MONO_S, MUTE, "la")
circle(draw, lx+160, ly-6, 9, fill=GOLD)
text(draw, "= 50K", lx+178, ly-4, F_MONO_S, MUTE, "la")

# =====================================================================
# 3. 左下：12 维评分雷达（里斯本画像）
# =====================================================================
RX, RY, R = 470, MAP_Y1+380, 260
dims = [("NET","网络",7.5),("COMM","社群",8.0),("LIFE","生活",8.0),("SAFE","安全",8.5),
        ("AIR","空气",7.0),("NIGHT","夜生活",8.0),("TEMP","气温",8.0),("SEASON","季节",8.0),
        ("COST","成本",5.5),("NOMAD","游民",6.0),("VISA","签证",7.0),("OVER","综合",7.9)]
n = len(dims)
for i in range(n):
    ang = -math.pi/2 + i*2*math.pi/n
    ex, ey = RX+R*math.cos(ang), RY+R*math.sin(ang)
    draw.line([RX,RY,ex,ey], fill=(GRID[0],GRID[1],GRID[2],70), width=1)
for rr in [R*0.25,R*0.5,R*0.75,R]:
    pts=[(RX+rr*math.cos(-math.pi/2+i*2*math.pi/n), RY+rr*math.sin(-math.pi/2+i*2*math.pi/n)) for i in range(n)]
    draw.line(pts+[pts[0]], fill=(GRID[0],GRID[1],GRID[2],40), width=1)
poly=[(RX+R*(d[2]/10)*math.cos(-math.pi/2+i*2*math.pi/n), RY+R*(d[2]/10)*math.sin(-math.pi/2+i*2*math.pi/n)) for i,d in enumerate(dims)]
draw.polygon(poly, fill=(TERRA[0],TERRA[1],TERRA[2],55), outline=TERRA, width=3)
for i,d in enumerate(dims):
    ang=-math.pi/2+i*2*math.pi/n
    px,py=RX+R*(d[2]/10)*math.cos(ang), RY+R*(d[2]/10)*math.sin(ang)
    circle(draw,px,py,5,fill=GOLD)
    lx,ly=RX+(R+36)*math.cos(ang), RY+(R+36)*math.sin(ang)
    anchor="ma" if ly<RY else "la"
    if abs(math.cos(ang))<0.3: anchor="ma" if ly<RY else "la"
    elif math.cos(ang)>0: anchor="la"
    else: anchor="ra"
    text(draw,d[1],lx,ly,F_BODY_S,CREAM,anchor)
text(draw,"SCORING MODEL",RX-R,RY-R-90,F_KICK,GOLD,"la")
text(draw,"12 AXES · WEIGHTED FORMULA",RX-R,RY-R-54,F_MONO_S,MUTE,"la")
text(draw,"SAMPLE · LISBON 7.9",RX-R,RY+R+28,F_MONO_S,MUTE,"la")

# =====================================================================
# 4. 右下：TOP 5 城市迷你评分条
# =====================================================================
TX, TY = 1180, MAP_Y1+150
text(draw,"TOP 5 · BY OVERALL SCORE",TX,TY,F_KICK,GOLD,"la")
top5=[("Lisbon 里斯本",7.9),("Shanghai 上海",7.6),("Tokyo 东京",7.6),
      ("Taipei 台北",7.7),("Barcelona 巴塞罗那",7.4)]
by=TY+70
for name,sc in top5:
    draw_text(draw,name,TX,by,F_BODY,F_BODY,CREAM,"la")
    bw=700
    bx=TX+430
    draw.rounded_rectangle([bx,by+4,bx+bw,by+30],radius=6,fill=(GRID[0],GRID[1],GRID[2],40))
    draw.rounded_rectangle([bx,by+4,bx+int(bw*sc/10),by+30],radius=6,fill=TERRA)
    text(draw,f"{sc:.1f}",bx+bw+20,by+2,F_MONO,GOLD,"la")
    by+=70
text(draw,"综合分按公开加权公式计算 · 社区可复算",TX,by+20,F_BODY_S,MUTE,"la")

# =====================================================================
# 5. 底部脚注带
# =====================================================================
FY = H-270
draw.line([MARGIN,FY-40,W-MARGIN,FY-40],fill=GRID,width=2)
text(draw,"你的下一座城，不该靠运气选。",MARGIN,FY,F_CJK_TAG,CREAM,"la")
text(draw,"YOUR NEXT CITY SHOULDN'T BE LEFT TO CHANCE.",MARGIN,FY+60,F_BODY,MUTE,"la")
ly=FY+120
text(draw,"EDIT  ·  docs.qq.com/sheet/DREppWERNRWdwcXRR",MARGIN,ly,F_MONO,MUTE,"la")
text(draw,"STAR  ·  github.com/Roloria/global-nomad-atlas",MARGIN,ly+50,F_MONO,MUTE,"la")
text(draw,"VIEW  ·  roloria.github.io/global-nomad-atlas",MARGIN,ly+100,F_MONO,MUTE,"la")
qx,qy=W-MARGIN-180,FY-10
draw.rounded_rectangle([qx,qy,qx+180,qy+180],radius=10,outline=CREAM,width=3)
random.seed(7)
for i in range(11):
    for j in range(11):
        if random.random()>0.5:
            draw.rectangle([qx+12+i*15,qy+12+j*15,qx+12+i*15+12,qy+12+j*15+12],fill=CREAM)
text(draw,"SCAN TO EXPLORE",qx,qy+200,F_MONO_S,MUTE,"ma")

# ---------- 暗角 & 输出 ----------
img = vignette(img, 0.5)
img.save(OUT, "PNG")
print("saved:", OUT, img.size)
