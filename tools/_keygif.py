# -*- coding: utf-8 -*-
"""GIF -> 透明帧（扫描线 flood fill 抠白底）。"""
import numpy as np
from PIL import Image, ImageSequence, ImageFilter


def key_frame(rgb, bg=(242, 242, 242), tol=16):
    a = np.asarray(rgb.convert("RGB")).astype(np.int16)
    dist = np.abs(a - np.array(bg, dtype=np.int16)).max(axis=2)
    cand = dist < tol
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
                row = cand[ny, xl:xr + 1] & ~filled[ny, xl:xr + 1]
                idx = np.flatnonzero(row)
                for i in idx:
                    stack.append((ny, xl + int(i)))
    alpha = np.where(filled, 0, 255).astype(np.uint8)
    out = rgb.convert("RGBA")
    out.putalpha(Image.fromarray(alpha, "L").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6)))
    return out


def load_frames(path):
    im = Image.open(path)
    return [f.convert("RGBA") for f in ImageSequence.Iterator(im)]
