"""ゼクト・キャノン（第2話のクラーラ機）の絵を切り抜く。元は docs/ref/zekt-cannon-sprites.png（ゼクトの資料と同じ形式）。
戦闘用の大きい絵は cutout_hq.py の cut_outline（輪郭線の外の背景だけ抜く）、ドット絵は extract_sprites.py の cut（ゼクトと同じ設定）で抜く。
使い方: python3 tools/zekt_cannon.py
"""
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, 'tools')
import extract_sprites as ex
import cutout_hq as hq
from scipy import ndimage as ndi


def drop_shadow(im, frac=.15):
    """足元に残る薄い水色の影（明るく青みのある画素）を消す。下の方だけ、外の透明な部分とつながっている分を抜く"""
    a = np.asarray(im).astype(float).copy()
    rgb, al = a[..., :3], a[..., 3]
    lum = rgb.mean(-1)
    pale = (lum > 120) & (rgb[..., 2] - rgb[..., 0] > 8) & (al > 0)
    pale[: int(a.shape[0] * (1 - frac))] = False
    bg = al < 40
    lab, _ = ndi.label(pale | bg)
    ok = set(np.unique(lab[bg])) - {0}
    kill = pale & np.isin(lab, list(ok))
    a[..., 3][kill] = 0
    out = Image.fromarray(a.astype(np.uint8), 'RGBA')
    return out.crop(out.getbbox())

SRC = 'docs/ref/zekt-cannon-sprites.png'
OUT = 'assets/sprites/'
BIG = (318, 140, 752, 556)
BOXES = {'down': (776, 200, 906, 425), 'up': (900, 200, 1012, 425), 'left': (1012, 200, 1112, 425), 'right': (1118, 200, 1214, 425),
         'idle': (60, 655, 290, 895), 'walk': (400, 655, 640, 895), 'attack': (780, 665, 1112, 895)}

if __name__ == '__main__':
    img = np.asarray(Image.open(SRC).convert('RGB'))
    big = drop_shadow(hq.cut_outline(img, BIG))
    big.save(OUT + 'cannon.png', optimize=True)
    print('cannon.png', big.size)
    for kind, box in BOXES.items():
        im = drop_shadow(ex.cut(img, box, tol=24, robust_bg=True, pocket_min=600, pocket_dark=0.35))
        im.save(f'{OUT}cannon_{kind}.png', optimize=True)
        print(f'cannon_{kind}.png', im.size)
