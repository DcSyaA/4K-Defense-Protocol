# -*- coding: utf-8 -*-
"""STRONGHOLD PROTOCOL 4K — v3: 2x, animated 暴躁铁皮 judgement line."""
import os, math, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageSequence

OUT = os.path.dirname(os.path.abspath(__file__))
SKIN = os.path.join(OUT, "4K Defense Protocol")
SRC_GRAVEL = os.path.join(SKIN, "砾.png")
SRC_IDLE = os.path.join(SKIN, "暴躁铁皮Idle.gif")
SRC_SKILL = os.path.join(SKIN, "暴躁铁皮Skill.gif")
SRC_LOGO = os.path.join(SKIN, "素材参考", "图标_卫戍协议.png")
SRC_ALLY = os.path.join(SKIN, "素材参考", "图标_卫戍协议：盟约.png")

F_CJK = "C:/Windows/Fonts/msyhbd.ttc"
F_BAHN = "C:/Windows/Fonts/bahnschrift.ttf"

S = 2
STAGE_W = 400          # 判定线贴图 = 舞台矩形宽度（与列总宽一致，1:1 不缩放）
HINT_STRETCH = 1.78    # 判定线贴图会被横向拉到整屏宽，16:9 下约 1.78 倍，预压缩抵消
HINT_H = 480


def px(v):
    return int(round(v * S))


def B(a, b, c, d):
    return (px(a), px(b), px(c), px(d))


def BF(a, b, c, d):
    return (px(a), px(b), px(c) - 1, px(d) - 1)


def P(x, y):
    return (px(x), px(y))


def fnt(path, size, var=None):
    f = ImageFont.truetype(path, px(size))
    if var:
        try:
            f.set_variation_by_name(var)
        except Exception:
            pass
    return f


GOLD = (216, 166, 66)
TEAL = (58, 186, 160)
CW, KEY_H, NOTE_H, HEAD_H, BODY_H, TAIL_H = 100, 90, 84, 62, 24, 20


def new(w, h):
    return Image.new("RGBA", (px(w), px(h)), (0, 0, 0, 0))


def grad_v(w, h, top, bottom):
    im = Image.new("RGBA", (px(w), px(h)))
    d = ImageDraw.Draw(im)
    for y in range(px(h)):
        t = y / max(1, px(h) - 1)
        d.line([(0, y), (px(w), y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(4)))
    return im


def grad_h(w, h, left, right):
    im = Image.new("RGBA", (px(w), px(h)))
    d = ImageDraw.Draw(im)
    for x in range(px(w)):
        t = x / max(1, px(w) - 1)
        d.line([(x, 0), (x, px(h))], fill=tuple(int(left[i] + (right[i] - left[i]) * t) for i in range(4)))
    return im


def panel(w, h, r=3, top=(46, 47, 50, 248), bottom=(26, 26, 28, 250), border=(58, 132, 120, 190)):
    mask = Image.new("L", (px(w), px(h)), 0)
    ImageDraw.Draw(mask).rounded_rectangle(B(0, 0, w - 1, h - 1), px(r), fill=255)
    im = Image.new("RGBA", (px(w), px(h)), (0, 0, 0, 0))
    im.paste(grad_v(w, h, top, bottom), (0, 0), mask)
    ImageDraw.Draw(im).rounded_rectangle(B(0, 0, w - 1, h - 1), px(r), outline=border, width=max(1, px(1)))
    return im


def fit(im, bw, bh, mirror=False):
    w, h = im.size
    s = min(px(bw) / w, px(bh) / h)
    r = im.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
    return r.transpose(Image.FLIP_LEFT_RIGHT) if mirror else r


def fit_square(im, box):
    """按 alpha 包围盒居中缩放（修 hit 图标视觉不居中）。"""
    bb = im.getchannel("A").getbbox()
    if bb:
        im = im.crop(bb)
    w, h = im.size
    s = min(px(box) / w, px(box) / h)
    return im.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)


def load_sprite(path):
    im = Image.open(path).convert("RGBA")
    return im.crop(im.getchannel("A").getbbox())


def prep_ui(im, boost=1.2, cut=38):
    a = im.getchannel("A").point(lambda v: 0 if v < cut else min(255, int(v * boost)))
    out = im.copy()
    out.putalpha(a)
    return out


# ---------- GIF 抠图 ----------
def radial_glow(w, h, color, peak=60):
    im = Image.new("RGBA", (px(w), px(h)), (0, 0, 0, 0))
    pix = im.load()
    for y in range(px(h)):
        for x in range(px(w)):
            dd = math.hypot((x - px(w) / 2) / (px(w) / 2), (y - px(h) / 2) / (px(h) / 2))
            a = int(peak * max(0.0, 1 - dd) ** 2)
            if a > 0:
                pix[x, y] = (color[0], color[1], color[2], a)
    return im


def key_frame(rgba, bg=(242, 242, 242), tol=16):
    arr = np.asarray(rgba.convert("RGB")).astype(np.int16)
    cand = (np.abs(arr - np.array(bg, dtype=np.int16)).max(axis=2) < tol)
    h, w = cand.shape
    filled = np.zeros_like(cand)
    stack = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    while stack:
        y, x = stack.pop()
        if filled[y, x] or not cand[y, x]:
            continue
        xl = x
        while xl > 0 and cand[y, xl - 1] and not filled[y, xl - 1]:
            xl -= 1
        xr = x
        while xr < w - 1 and cand[y, xr + 1] and not filled[y, xr + 1]:
            xr += 1
        filled[y, xl:xr + 1] = True
        for ny in (y - 1, y + 1):
            if 0 <= ny < h:
                idx = np.flatnonzero(cand[ny, xl:xr + 1] & ~filled[ny, xl:xr + 1])
                for i in idx:
                    stack.append((ny, xl + int(i)))
    alpha = np.where(filled, 0, 255).astype(np.uint8)
    out = rgba.convert("RGBA")
    out.putalpha(Image.fromarray(alpha, "L").filter(ImageFilter.MinFilter(3))
                 .filter(ImageFilter.GaussianBlur(0.6)))
    return out


def load_gif(path):
    frames = [key_frame(f.convert("RGBA")) for f in ImageSequence.Iterator(Image.open(path))]
    # 统一包围盒，避免逐帧抖动
    x0, y0, x1, y1 = 10 ** 6, 10 ** 6, 0, 0
    for f in frames:
        bb = f.getchannel("A").getbbox()
        x0, y0 = min(x0, bb[0]), min(y0, bb[1])
        x1, y1 = max(x1, bb[2]), max(y1, bb[3])
    return [f.crop((x0, y0, x1, y1)) for f in frames]


IDLE = load_gif(SRC_IDLE)
SKILL = load_gif(SRC_SKILL)
SPR_G = load_sprite(SRC_GRAVEL)
LOGO_EN = prep_ui(Image.open(SRC_LOGO).convert("RGBA").crop((12, 8, 116, 44)))
LOGO_EN = LOGO_EN.resize((px(104), px(36)), Image.LANCZOS)
LOGO_CN = prep_ui(Image.open(SRC_LOGO).convert("RGBA").crop((118, 2, 176, 50)))
LOGO_CN = LOGO_CN.resize((px(58), px(48)), Image.LANCZOS)
EMBLEM = prep_ui(Image.open(SRC_ALLY).convert("RGBA").crop((114, 3, 168, 48)))


# ---------------- 音符卡 ----------------
def card(w=CW, h=NOTE_H):
    """透明底卡片：只保留描边、立绘、底部文本框与缎带。"""
    im = new(w, h)
    d = ImageDraw.Draw(im)
    g = fit(SPR_G, w - 10, h - 18)
    ax = int(px(w) / 2 - g.width / 2 + px(2))
    ay = int(px(h) - px(24) - g.height)
    im.alpha_composite(g, (ax, ay))

    box_h = 22
    box_y = h - box_h - 3
    tb = grad_h(w - 4, box_h, (44, 116, 99, 215), (33, 35, 39, 225))
    tbm = Image.new("L", (px(w - 4), px(box_h)), 0)
    ImageDraw.Draw(tbm).rounded_rectangle(B(0, 0, w - 5, box_h - 1), px(2), fill=255)
    im.paste(tb, P(2, box_y), tbm)
    d.text(P(7, box_y + 2), "STRONGHOLD PROTOCOL", font=fnt(F_BAHN, 5, "Bold Condensed"), fill=(12, 44, 38, 235))
    d.text(P(7, box_y + 6), "砾", font=fnt(F_CJK, 9.5), fill=(242, 246, 248, 255))

    bar = Image.new("RGBA", (px(w - 14), px(3)), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar)
    bd.rounded_rectangle(BF(0, 0, w - 14, 3), px(1), fill=(52, 168, 142, 240))
    im.alpha_composite(bar, P(7, box_y + 17))
    # 描边（内部完全透明）
    d.rounded_rectangle(B(0, 0, w - 1, h - 1), px(3), outline=(58, 132, 120, 170), width=max(1, px(1)))
    return im


def hold_body():
    im = new(CW, BODY_H)
    d = ImageDraw.Draw(im)
    d.rectangle(BF(34, 0, CW - 34, BODY_H), fill=(30, 92, 80, 165))
    d.rectangle(BF(34, 0, 37, BODY_H), fill=(96, 214, 190, 200))
    d.rectangle(BF(CW - 37, 0, CW - 34, BODY_H), fill=(96, 214, 190, 200))
    return im


def hold_tail():
    im = new(CW, TAIL_H)
    d = ImageDraw.Draw(im)
    d.polygon([P(34, 0), P(CW - 34, 0), P(CW - 34, 5), P(CW // 2, TAIL_H), P(34, 5)],
              fill=(44, 138, 118, 215))
    d.line([P(34, 0), P(CW - 34, 0)], fill=(150, 236, 216, 170), width=max(1, px(1)))
    return im


# ---------------- 键帽 ----------------
KEY_H = 162


def key_frame(machine, pressed=False, mode="4k"):
    im = new(CW, KEY_H)
    if mode == "7k":
        g = machine.resize((px(100), px(110)), Image.LANCZOS)
        y = int((px(KEY_H) - g.height) / 2)
    else:
        g = machine.resize((px(93), px(KEY_H)), Image.LANCZOS)
        y = 0
    x = int(px(CW) / 2 - g.width / 2)
    if pressed:
        glow = radial_glow(110, 160, (47, 200, 170), 80)
        im.alpha_composite(glow, (int(px(CW) / 2 - px(55)), int(y + g.height / 2 - px(80))))
    im.alpha_composite(g, (x, y))
    return im


def hint_base(w=STAGE_W, h=HINT_H):
    im = new(w, h)
    d = ImageDraw.Draw(im)
    f = fnt(F_CJK, 34)
    bb = d.textbbox((0, 0), "不屈", font=f)
    d.text((px(w) / 2 - (bb[2] - bb[0]) / 2 - bb[0], px(8)), "不屈", font=f,
           fill=(238, 241, 244, 250))
    return im


# ---------------- 侧栏 ----------------
def side(num):
    """侧栏：参考 UI1/UI2 —— 直角、细边、青绿描边、LEVEL 大字块、黄黑警戒带。"""
    w, h = 96, 480
    im = new(w, h)
    d = ImageDraw.Draw(im)
    d.rectangle(B(0, 0, w - 1, h - 1), fill=(15, 17, 20, 236))
    for x in (0, w - 1):
        d.line([P(x, 0), P(x, h)], fill=(58, 190, 168, 120), width=max(1, px(1)))
    # 顶部黄黑警戒带
    for i in range(-1, w // 8 + 2):
        d.polygon([P(i * 8, 0), P(i * 8 + 4, 0), P(i * 8, 6), P(i * 8 - 4, 6)],
                  fill=(214, 176, 58, 235))
    d.rectangle(B(0, 6, w - 1, 7), fill=(15, 17, 20, 255))
    # LEVEL 块
    d.rectangle(B(8, 18, w - 9, 104), fill=(22, 58, 52, 235), outline=(80, 210, 184, 130))
    d.text(P(15, 24), "LEVEL", font=fnt(F_BAHN, 9, "Bold Condensed"), fill=(150, 226, 208, 235))
    d.line([P(15, 36), P(w - 16, 36)], fill=(80, 210, 184, 110), width=max(1, px(1)))
    d.text(P(16, 40), "IV", font=fnt(F_BAHN, 40, "Bold Condensed"), fill=(240, 248, 246, 255))
    d.text(P(w - 30, 74), "SP", font=fnt(F_BAHN, 9, "Bold Condensed"), fill=(120, 200, 186, 200))
    # 竖排字标
    lg = LOGO_EN.rotate(90, expand=True)
    im.alpha_composite(lg, (int(px(w) / 2 - lg.width / 2), px(124)))
    # 分隔 + 中文标
    for yy in (250, 262):
        d.line([P(14, yy), P(w - 15, yy)], fill=(80, 120, 114, 130), width=max(1, px(1)))
    cn = LOGO_CN.resize((int(LOGO_CN.width * 0.62), int(LOGO_CN.height * 0.62)), Image.LANCZOS)
    im.alpha_composite(cn, (int(px(w) / 2 - cn.width / 2), px(276)))
    # 三条菜单式细块
    for i, yy in enumerate((360, 382, 404)):
        d.rectangle(B(12, yy, w - 13, yy + 14), fill=(26, 30, 34, 210), outline=(70, 100, 96, 120))
        d.rectangle(B(12, yy, 15, yy + 14), fill=(58, 190, 168, 200) if i == 0 else (90, 100, 106, 160))
        d.line([P(22, yy + 7), P(w - 22, yy + 7)], fill=(120, 130, 136, 150), width=max(1, px(1)))
    # 底部编号
    d.line([P(14, 440), P(w - 15, 440)], fill=(80, 120, 114, 130), width=max(1, px(1)))
    d.text(P(15, 448), "SP-" + num, font=fnt(F_BAHN, 13, "Bold Condensed"), fill=(190, 200, 208, 235))
    return im


# ---------------- 判定戳 ----------------
def load_icon(name, color, box=58):
    im = Image.open(os.path.join(SKIN, name + ".png")).convert("RGBA")
    r, g, b, a = im.split()
    r = r.point(lambda v: v * color[0] // 255)
    g = g.point(lambda v: v * color[1] // 255)
    b = b.point(lambda v: v * color[2] // 255)
    im = Image.merge("RGBA", (r, g, b, a))
    return fit_square(im, box)


def hitburst_icon(name, label, color, ratio=1.0):
    W, H = 96, 112
    im = Image.new("RGBA", (px(W), px(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy, r = px(W) / 2, px(H) / 2 - px(2), px(36)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(26, 28, 31, 225))
    box = (cx - r, cy - r, cx + r, cy + r)
    d.arc(box, 90, 360, fill=(112, 120, 128, 255), width=px(5))
    d.arc(box, 90, 90 + 270 * min(1.0, ratio), fill=(47, 200, 170, 255), width=px(5))
    icon = load_icon(name, color, 40)
    im.alpha_composite(icon, (int(cx - icon.width / 2), int(cy - icon.height / 2)))
    f = fnt(F_CJK, 16)
    bb = d.textbbox((0, 0), label, font=f)
    d.text((px(W) / 2 - (bb[2] - bb[0]) / 2 - bb[0], px(H) - px(19)),
           label, font=f, fill=(236, 240, 243, 250))
    return im


def miss_icon():
    W, H = 96, 112
    im = Image.new("RGBA", (px(W), px(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy, r = px(W) / 2, px(H) / 2 - px(2), px(36)
    d.rounded_rectangle((cx - r, cy - r, cx + r, cy + r), px(11),
                        outline=(52, 186, 160, 255), width=px(6))
    f = fnt(F_CJK, 38)
    bb = d.textbbox((0, 0), "区", font=f)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]),
           "区", font=f, fill=(52, 186, 160, 255))
    return im


def digit(ch):
    W, H = 36, 58
    im = Image.new("RGBA", (px(W), px(H)), (0, 0, 0, 0))
    f = fnt(F_BAHN, 50, "Bold Condensed")
    d = ImageDraw.Draw(im)
    bb = d.textbbox((0, 0), ch, font=f)
    pos = (px(W) / 2 - (bb[2] - bb[0]) / 2 - bb[0], px(H) / 2 - (bb[3] - bb[1]) / 2 - bb[1])
    sh = Image.new("RGBA", (px(W), px(H)), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text(pos, ch, font=f, fill=(0, 0, 0, 170))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(px(3))))
    d.text(pos, ch, font=f, fill=(236, 239, 242, 255))
    return im


# ---------------- 生成 ----------------
files = {}
files["mania-stage-hint.png"] = hint_base()

files["mania-stage-left.png"] = side("01")
files["mania-stage-right.png"] = side("02")
notes = [card() for _ in range(4)]
heads = [card(CW, HEAD_H) for _ in range(4)]
# 键帽 = 暴躁铁皮：4K / 7K 两套（按键槽高固定、宽随列宽，需分别补偿）
files["spk4.png"] = key_frame(IDLE[0], False, "4k")
files["spk4d.png"] = key_frame(SKILL[14], True, "4k")
files["spk7.png"] = key_frame(IDLE[0], False, "7k")
files["spk7d.png"] = key_frame(SKILL[14], True, "7k")
files["mania-key1.png"] = files["spk4.png"]
files["mania-key2.png"] = files["spk4.png"]
files["mania-key1D.png"] = files["spk4d.png"]
files["mania-key2D.png"] = files["spk4d.png"]
for i in (1, 2):
    files[f"mania-note{i}.png"] = notes[i - 1]
    files[f"mania-note{i}H.png"] = heads[i - 1]
    files[f"mania-note{i}L.png"] = hold_body()
    files[f"mania-note{i}T.png"] = hold_tail()
for c in range(4):
    files[f"sp-note-{c + 1}.png"] = notes[c]
    files[f"sp-noteh-{c + 1}.png"] = heads[c]
    files[f"sp-notel-{c + 1}.png"] = hold_body()
    files[f"sp-notet-{c + 1}.png"] = hold_tail()
files["mania-hit300g.png"] = hitburst_icon("奇迹", "奇迹", GOLD, ratio=1.0)
files["mania-hit300.png"] = hitburst_icon("精准", "精准", (238, 226, 190), ratio=0.85)
files["mania-hit200.png"] = hitburst_icon("灵巧", "灵巧", (198, 206, 214), ratio=0.68)
files["mania-hit100.png"] = hitburst_icon("迅捷", "迅捷", (150, 160, 172), ratio=0.5)
files["mania-hit50.png"] = hitburst_icon("远见", "远见", (108, 118, 130), ratio=0.34)
files["mania-hit0.png"] = miss_icon()
for i in range(10):
    files[f"score-{i}.png"] = digit(str(i))
files["score-x.png"] = digit("x")
files["score-dot.png"] = digit(".")
files["score-percent.png"] = digit("%")

for n, im in files.items():
    stem = n[:-4]
    im.save(os.path.join(SKIN, stem + "@2x.png"), optimize=True)
    im.resize((max(1, im.width // 2), max(1, im.height // 2)), Image.LANCZOS).save(
        os.path.join(SKIN, n), optimize=True)

INI = """[General]
Name: STRONGHOLD PROTOCOL 4K
Author: DeepSeek
Version: 2.5
AnimationFramerate: 30
CursorCentre: 1
CursorExpand: 0
CursorRotate: 0
CursorTrailRotate: 0
HitCircleOverlayAboveNumber: 1
LayeredHitSounds: 1
AllowSliderBallTint: 0
SpinnerFrequencyModulate: 1
HitCircleOverlap: 0

[Fonts]
ComboPrefix: score
ComboOverlap: -2

[Mania]
HitPosition: 420
LightPosition: 420
ScorePosition: 386
ComboPosition: 258
ColourColumnLine: 216,166,66,70
ColumnLineWidth: 2,2,2,2,2,2,2,2,2,2
SpecialStyle: 0
Colour1: 20,23,27,110
Colour2: 16,18,22,110
Colour3: 16,18,22,110
Colour4: 20,23,27,110
Colour5: 16,18,22,110
Colour6: 20,23,27,110
Colour7: 16,18,22,110
Colour8: 20,23,27,110
Colour9: 16,18,22,110
Colour10: 20,23,27,110

[Mania]
Keys: 4
HitPosition: 420
LightPosition: 420
ScorePosition: 386
ComboPosition: 258
ColourColumnLine: 216,166,66,70
ColumnLineWidth: 2,2,2,2,2,2,2,2,2,2
SpecialStyle: 0
Colour1: 20,23,27,110
Colour2: 16,18,22,110
Colour3: 16,18,22,110
Colour4: 20,23,27,110
Colour5: 16,18,22,110
Colour6: 20,23,27,110
Colour7: 16,18,22,110
Colour8: 20,23,27,110
Colour9: 16,18,22,110
Colour10: 20,23,27,110
ColumnWidth: 100,100,100,100
ColumnSpacing: 0,0,0,0
KeyImage0: spk4
KeyImage0D: spk4d
KeyImage1: spk4
KeyImage1D: spk4d
KeyImage2: spk4
KeyImage2D: spk4d
KeyImage3: spk4
KeyImage3D: spk4d

[Mania]
Keys: 5
HitPosition: 420
LightPosition: 420
ScorePosition: 386
ComboPosition: 258
ColourColumnLine: 216,166,66,70
ColumnLineWidth: 2,2,2,2,2,2,2,2,2,2
SpecialStyle: 0
Colour1: 20,23,27,110
Colour2: 16,18,22,110
Colour3: 16,18,22,110
Colour4: 20,23,27,110
Colour5: 16,18,22,110
Colour6: 20,23,27,110
Colour7: 16,18,22,110
Colour8: 20,23,27,110
Colour9: 16,18,22,110
Colour10: 20,23,27,110
ColumnWidth: 88,88,88,88,88
ColumnSpacing: 0,0,0,0,0
KeyImage0: spk4
KeyImage0D: spk4d
KeyImage1: spk4
KeyImage1D: spk4d
KeyImage2: spk4
KeyImage2D: spk4d
KeyImage3: spk4
KeyImage3D: spk4d
KeyImage4: spk4
KeyImage4D: spk4d

[Mania]
Keys: 6
HitPosition: 420
LightPosition: 420
ScorePosition: 386
ComboPosition: 258
ColourColumnLine: 216,166,66,70
ColumnLineWidth: 2,2,2,2,2,2,2,2,2,2
SpecialStyle: 0
Colour1: 20,23,27,110
Colour2: 16,18,22,110
Colour3: 16,18,22,110
Colour4: 20,23,27,110
Colour5: 16,18,22,110
Colour6: 20,23,27,110
Colour7: 16,18,22,110
Colour8: 20,23,27,110
Colour9: 16,18,22,110
Colour10: 20,23,27,110
ColumnWidth: 74,74,74,74,74,74
ColumnSpacing: 0,0,0,0,0,0
KeyImage0: spk4
KeyImage0D: spk4d
KeyImage1: spk4
KeyImage1D: spk4d
KeyImage2: spk4
KeyImage2D: spk4d
KeyImage3: spk4
KeyImage3D: spk4d
KeyImage4: spk4
KeyImage4D: spk4d
KeyImage5: spk4
KeyImage5D: spk4d

[Mania]
Keys: 7
HitPosition: 420
LightPosition: 420
ScorePosition: 386
ComboPosition: 258
ColourColumnLine: 216,166,66,70
ColumnLineWidth: 2,2,2,2,2,2,2,2,2,2
SpecialStyle: 0
Colour1: 20,23,27,110
Colour2: 16,18,22,110
Colour3: 16,18,22,110
Colour4: 20,23,27,110
Colour5: 16,18,22,110
Colour6: 20,23,27,110
Colour7: 16,18,22,110
Colour8: 20,23,27,110
Colour9: 16,18,22,110
Colour10: 20,23,27,110
ColumnWidth: 63,63,63,63,63,63,63
ColumnSpacing: 0,0,0,0,0,0,0
KeyImage0: spk7
KeyImage0D: spk7d
KeyImage1: spk7
KeyImage1D: spk7d
KeyImage2: spk7
KeyImage2D: spk7d
KeyImage3: spk7
KeyImage3D: spk7d
KeyImage4: spk7
KeyImage4D: spk7d
KeyImage5: spk7
KeyImage5D: spk7d
KeyImage6: spk7
KeyImage6D: spk7d

[Mania]
Keys: 8
HitPosition: 420
LightPosition: 420
ScorePosition: 386
ComboPosition: 258
ColourColumnLine: 216,166,66,70
ColumnLineWidth: 2,2,2,2,2,2,2,2,2,2
SpecialStyle: 0
Colour1: 20,23,27,110
Colour2: 16,18,22,110
Colour3: 16,18,22,110
Colour4: 20,23,27,110
Colour5: 16,18,22,110
Colour6: 20,23,27,110
Colour7: 16,18,22,110
Colour8: 20,23,27,110
Colour9: 16,18,22,110
Colour10: 20,23,27,110
ColumnWidth: 55,55,55,55,55,55,55,55
ColumnSpacing: 0,0,0,0,0,0,0,0
KeyImage0: spk4
KeyImage0D: spk4d
KeyImage1: spk4
KeyImage1D: spk4d
KeyImage2: spk4
KeyImage2D: spk4d
KeyImage3: spk4
KeyImage3D: spk4d
KeyImage4: spk4
KeyImage4D: spk4d
KeyImage5: spk4
KeyImage5D: spk4d
KeyImage6: spk4
KeyImage6D: spk4d
KeyImage7: spk4
KeyImage7D: spk4d

[Mania]
Keys: 9
HitPosition: 420
LightPosition: 420
ScorePosition: 386
ComboPosition: 258
ColourColumnLine: 216,166,66,70
ColumnLineWidth: 2,2,2,2,2,2,2,2,2,2
SpecialStyle: 0
Colour1: 20,23,27,110
Colour2: 16,18,22,110
Colour3: 16,18,22,110
Colour4: 20,23,27,110
Colour5: 16,18,22,110
Colour6: 20,23,27,110
Colour7: 16,18,22,110
Colour8: 20,23,27,110
Colour9: 16,18,22,110
Colour10: 20,23,27,110
ColumnWidth: 49,49,49,49,49,49,49,49,49
ColumnSpacing: 0,0,0,0,0,0,0,0,0
KeyImage0: spk4
KeyImage0D: spk4d
KeyImage1: spk4
KeyImage1D: spk4d
KeyImage2: spk4
KeyImage2D: spk4d
KeyImage3: spk4
KeyImage3D: spk4d
KeyImage4: spk4
KeyImage4D: spk4d
KeyImage5: spk4
KeyImage5D: spk4d
KeyImage6: spk4
KeyImage6D: spk4d
KeyImage7: spk4
KeyImage7D: spk4d
KeyImage8: spk4
KeyImage8D: spk4d

[Mania]
Keys: 10
HitPosition: 420
LightPosition: 420
ScorePosition: 386
ComboPosition: 258
ColourColumnLine: 216,166,66,70
ColumnLineWidth: 2,2,2,2,2,2,2,2,2,2
SpecialStyle: 0
Colour1: 20,23,27,110
Colour2: 16,18,22,110
Colour3: 16,18,22,110
Colour4: 20,23,27,110
Colour5: 16,18,22,110
Colour6: 20,23,27,110
Colour7: 16,18,22,110
Colour8: 20,23,27,110
Colour9: 16,18,22,110
Colour10: 20,23,27,110
ColumnWidth: 44,44,44,44,44,44,44,44,44,44
ColumnSpacing: 0,0,0,0,0,0,0,0,0,0
KeyImage0: spk4
KeyImage0D: spk4d
KeyImage1: spk4
KeyImage1D: spk4d
KeyImage2: spk4
KeyImage2D: spk4d
KeyImage3: spk4
KeyImage3D: spk4d
KeyImage4: spk4
KeyImage4D: spk4d
KeyImage5: spk4
KeyImage5D: spk4d
KeyImage6: spk4
KeyImage6D: spk4d
KeyImage7: spk4
KeyImage7D: spk4d
KeyImage8: spk4
KeyImage8D: spk4d
KeyImage9: spk4
KeyImage9D: spk4d

[Mania]
Keys: 12
HitPosition: 420
LightPosition: 420
ScorePosition: 386
ComboPosition: 258
ColourColumnLine: 216,166,66,70
ColumnLineWidth: 2,2,2,2,2,2,2,2,2,2
SpecialStyle: 0
Colour1: 20,23,27,110
Colour2: 16,18,22,110
Colour3: 16,18,22,110
Colour4: 20,23,27,110
Colour5: 16,18,22,110
Colour6: 20,23,27,110
Colour7: 16,18,22,110
Colour8: 20,23,27,110
Colour9: 16,18,22,110
Colour10: 20,23,27,110
ColumnWidth: 37,37,37,37,37,37,37,37,37,37,37,37
ColumnSpacing: 0,0,0,0,0,0,0,0,0,0,0,0
KeyImage0: spk4
KeyImage0D: spk4d
KeyImage1: spk4
KeyImage1D: spk4d
KeyImage2: spk4
KeyImage2D: spk4d
KeyImage3: spk4
KeyImage3D: spk4d
KeyImage4: spk4
KeyImage4D: spk4d
KeyImage5: spk4
KeyImage5D: spk4d
KeyImage6: spk4
KeyImage6D: spk4d
KeyImage7: spk4
KeyImage7D: spk4d
KeyImage8: spk4
KeyImage8D: spk4d
KeyImage9: spk4
KeyImage9D: spk4d
KeyImage10: spk4
KeyImage10D: spk4d
KeyImage11: spk4
KeyImage11D: spk4d

[Mania]
Keys: 14
HitPosition: 420
LightPosition: 420
ScorePosition: 386
ComboPosition: 258
ColourColumnLine: 216,166,66,70
ColumnLineWidth: 2,2,2,2,2,2,2,2,2,2
SpecialStyle: 0
Colour1: 20,23,27,110
Colour2: 16,18,22,110
Colour3: 16,18,22,110
Colour4: 20,23,27,110
Colour5: 16,18,22,110
Colour6: 20,23,27,110
Colour7: 16,18,22,110
Colour8: 20,23,27,110
Colour9: 16,18,22,110
Colour10: 20,23,27,110
ColumnWidth: 31,31,31,31,31,31,31,31,31,31,31,31,31,31
ColumnSpacing: 0,0,0,0,0,0,0,0,0,0,0,0,0,0
KeyImage0: spk4
KeyImage0D: spk4d
KeyImage1: spk4
KeyImage1D: spk4d
KeyImage2: spk4
KeyImage2D: spk4d
KeyImage3: spk4
KeyImage3D: spk4d
KeyImage4: spk4
KeyImage4D: spk4d
KeyImage5: spk4
KeyImage5D: spk4d
KeyImage6: spk4
KeyImage6D: spk4d
KeyImage7: spk4
KeyImage7D: spk4d
KeyImage8: spk4
KeyImage8D: spk4d
KeyImage9: spk4
KeyImage9D: spk4d
KeyImage10: spk4
KeyImage10D: spk4d
KeyImage11: spk4
KeyImage11D: spk4d
KeyImage12: spk4
KeyImage12D: spk4d
KeyImage13: spk4
KeyImage13D: spk4d

[Mania]
Keys: 16
HitPosition: 420
LightPosition: 420
ScorePosition: 386
ComboPosition: 258
ColourColumnLine: 216,166,66,70
ColumnLineWidth: 2,2,2,2,2,2,2,2,2,2
SpecialStyle: 0
Colour1: 20,23,27,110
Colour2: 16,18,22,110
Colour3: 16,18,22,110
Colour4: 20,23,27,110
Colour5: 16,18,22,110
Colour6: 20,23,27,110
Colour7: 16,18,22,110
Colour8: 20,23,27,110
Colour9: 16,18,22,110
Colour10: 20,23,27,110
ColumnWidth: 27,27,27,27,27,27,27,27,27,27,27,27,27,27,27,27
ColumnSpacing: 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
KeyImage0: spk4
KeyImage0D: spk4d
KeyImage1: spk4
KeyImage1D: spk4d
KeyImage2: spk4
KeyImage2D: spk4d
KeyImage3: spk4
KeyImage3D: spk4d
KeyImage4: spk4
KeyImage4D: spk4d
KeyImage5: spk4
KeyImage5D: spk4d
KeyImage6: spk4
KeyImage6D: spk4d
KeyImage7: spk4
KeyImage7D: spk4d
KeyImage8: spk4
KeyImage8D: spk4d
KeyImage9: spk4
KeyImage9D: spk4d
KeyImage10: spk4
KeyImage10D: spk4d
KeyImage11: spk4
KeyImage11D: spk4d
KeyImage12: spk4
KeyImage12D: spk4d
KeyImage13: spk4
KeyImage13D: spk4d
KeyImage14: spk4
KeyImage14D: spk4d
KeyImage15: spk4
KeyImage15D: spk4d

"""
# skin.ini 由用户自己维护，构建时不再覆盖
if not os.path.exists(os.path.join(SKIN, "skin.ini")):
    with open(os.path.join(SKIN, "skin.ini"), "w", encoding="utf-8-sig") as fh:
        fh.write(INI)

# ---------------- preview ----------------
PW, PH = 1280, 960
HIT = 840
prev = Image.new("RGBA", (PW, PH), (14, 15, 18, 255))
d = ImageDraw.Draw(prev)
prev.alpha_composite(files["mania-stage-left.png"], (0, 0))
prev.alpha_composite(files["mania-stage-right.png"], (PW - 192, 0))
x0 = 160
for i in range(4):
    d.rectangle((x0 + i * 200, 0, x0 + (i + 1) * 200 - 1, PH),
                fill=(20, 23, 27, 200) if i % 2 == 0 else (16, 18, 22, 200))
    d.line([(x0 + i * 200, 0), (x0 + i * 200, PH)], fill=(216, 166, 66, 70), width=2)
lanes = ["sp-note-1.png", "sp-note-2.png", "sp-note-3.png", "sp-note-4.png"]
for i, y in ((0, 200), (1, 56), (1, 184), (2, 104)):
    prev.alpha_composite(files[lanes[i]], (x0 + i * 200, y))
hx = x0 + 3 * 200
hold = Image.new("RGBA", (200, 408), (0, 0, 0, 0))
for yy in range(0, 408, 48):
    hold.alpha_composite(files["sp-notel-4.png"], (0, yy))
prev.alpha_composite(hold, (hx, 88))
prev.alpha_composite(files["sp-noteh-4.png"], (hx, 492))
for i, k in enumerate(["mania-key1.png", "mania-key2.png", "mania-key2D.png", "mania-key1.png"]):
    _k = files[k]
    _ks = _k.resize((_k.width, int(_k.height * 0.52)), Image.LANCZOS)
    prev.alpha_composite(_ks, (x0 + i * 200, HIT - _ks.height))
prev.alpha_composite(files["mania-stage-hint.png"], (int(PW / 2 - px(STAGE_W) / 2), HIT - px(HINT_H) // 2))
prev.alpha_composite(files["mania-hit300g.png"], (x0 + 100 - 96, HIT - 112 - 68))
for i, ch in enumerate("128"):
    prev.alpha_composite(files[f"score-{ch}.png"], (x0 + 400 - 108 + i * 72, 458))
prev.convert("RGB").save(os.path.join(OUT, "preview.png"))

osk = os.path.join(OUT, "4K-Defense-Protocol.osk")
if os.path.exists(osk):
    os.remove(osk)
ship = set(files) | {"skin.ini"}
with zipfile.ZipFile(osk, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(ship):
        p = os.path.join(SKIN, fn)
        if os.path.exists(p):
            z.write(p, fn)
print("ok", len(files), "files; osk", round(os.path.getsize(osk) / 1048576, 2), "MB")


README = """STRONGHOLD PROTOCOL —— v7（支持 4~16K）
================================

安装：把文件夹放进 osu!/Skins，或双击 4K-Defense-Protocol.osk。

按键 = 暴躁铁皮（分 4K / 7K 两套）
---------------------------------
按键槽的特点是：**宽度=列宽，高度固定**。所以同样一张图，4K（列宽 100）是方的，
7K（列宽 63）就会瘦高。现在按列宽分别补偿：
  spk4.png / spk4d.png  4K 用（内容预拉伸成 93x162，渲染回来约 84x84）
  spk7.png / spk7d.png  7K 用（内容 100x110，渲染回来约 63x63）
skin.ini 里 4K 段用 KeyImage0~3 指 spk4，7K 段用 KeyImage0~6 指 spk7；
其它键数回落到 mania-key1/2（= 4K 版）。

侧栏（参考 UI1 / UI2 重做）
--------------------------
mania-stage-left/right：96 x 480，直角、细青绿边、顶部黄黑警戒带、
青色 LEVEL 块 + 大号罗马数字、竖排 STRONGHOLD PROTOCOL 字标、
卫戍协议中文标、菜单式细条、底部 SP-01/02。

多键数支持
----------
通用 [Mania] 段（判定线/连击/判定戳位置、列线色、10 列轨道色）
+ 4/5/6/7/8/9/10/12/14/16K 各自的 ColumnWidth，总宽控制在 440~480。

其它
----
判定线只有「不屈」；连击在它下方（ComboPosition 258）。
判定戳：青绿+灰双色环、图标居中、文字在下；MISS 是青绿粗框 + 「区」。
音符卡：青绿描边 + 深灰渐变 + 竖纹 + 立绘 + 文本框内嵌缎带（只有「砾」）。
"""
with open(os.path.join(SKIN, "README.txt"), "w", encoding="utf-8-sig") as fh:
    fh.write(README)

osk = os.path.join(OUT, "4K-Defense-Protocol.osk")
if os.path.exists(osk):
    os.remove(osk)
ship = set(files) | {n[:-4] + "@2x.png" for n in files} | {"README.txt", "skin.ini"}
with zipfile.ZipFile(osk, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(ship):
        p = os.path.join(SKIN, fn)
        if os.path.exists(p):
            z.write(p, fn)
print("packed", len(ship))
