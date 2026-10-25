"""カラドリウスの射撃の構え（docs/ref/caladrius-guns.jpg：ライフル版・マシンガン版）を切り抜く。
元の絵は本当の透過ではなく、透過を表す市松模様（白と灰色）が描き込まれているので、
・市松模様（色味のない明るい画素）と台座（青みのある白）を、外側からつながっている分だけ抜く（羽根飾りは暗い輪郭線で囲まれているので残る）
・銃口の火（ゲーム側で描く）と床の薬莢を消す
・いちばん大きい塊だけ残す
使い方: python3 tools/caladrius_guns.py   → assets/sprites/caladrius_rifle.png, caladrius_mg.png
"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SRC = 'docs/ref/caladrius-guns.jpg'
# (出力名, 範囲, 銃口の火を消す x の開始, 羽根飾りの範囲（どれも範囲内の座標）)
PANELS = [('caladrius_rifle', (0, 60, 632, 760), 590, (195, 15, 335, 130)), ('caladrius_mg', (632, 60, 1264, 760), 505, (135, 15, 275, 130))]


# 市松模様のマス目（元の絵全体の座標）：1マス約17.2×17.15画素、左上の基準は (13, 68)。灰色のマスは (列+行) が奇数
CX, CY, PX, PY = 13, 68, 17.194, 17.15


def cut(a, flash_x, plume):
    a = a.astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = a.mean(-1)
    neutral = (np.abs(r - g) < 10) & (np.abs(g - b) < 10) & (lum > 175)
    base = (b > r + 6) & (lum > 185)                     # 台座の青みのある白
    bgl = neutral | base
    lab, _ = ndi.label(bgl)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(edge))
    fg = ~bg
    # 羽根飾り：白・灰色で市松模様と見分けられないので、羽根の範囲（plume）の中で、
    # 青みのある灰色の輪郭線をつないで閉じ、その内側を羽根として残す
    px0, py0, px1, py1 = plume
    sub = np.zeros_like(fg); sub[py0:py1, px0:px1] = True
    line = sub & (((lum < 185) & ~neutral) | ((b - r >= 8) & (lum < 235)) | (lum < 150))
    closed = ndi.binary_closing(line, structure=np.ones((5, 5)), iterations=1)
    inside = ndi.binary_fill_holes(closed) & sub
    fg |= inside
    # 銃口の火：銃身の先より右の、明るく暖かい色（と、そのまわりの白っぽい光）
    fx = np.zeros_like(fg); fx[:, flash_x:] = True
    fg &= ~(fx & (((lum > 150) & (r - b > 25)) | (lum > 215)))
    # 薬莢・火の粉などのかけらを消し、いちばん大きい塊だけ残す
    lab2, n = ndi.label(fg)
    if n > 1:
        sizes = ndi.sum(fg, lab2, range(1, n + 1))
        fg = lab2 == (int(np.argmax(sizes)) + 1)
    alpha = fg.astype(np.uint8) * 255
    out = Image.fromarray(np.dstack([a.astype(np.uint8), alpha]), 'RGBA')
    return out.crop(out.getbbox())


if __name__ == '__main__':
    src = np.asarray(Image.open(SRC).convert('RGB'))
    for name, (x0, y0, x1, y1), fx, pl in PANELS:
        im = cut(src[y0:y1, x0:x1], fx, pl)
        im.save(f'assets/sprites/{name}.png', optimize=True)
        print(name, im.size)
