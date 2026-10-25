"""ファンタジー風の地形タイル（docs/ref/fantasy-tiles.jpg）から、戦闘画面の足場タイル（assets/sprites/tile_*.png）を切り抜く。
シートの背景はマゼンタ一色なので、マゼンタに近い色を透明にする（JPEG のにじみも消す）。
マップ用のタイル（村・町・城・砦・森・山）は tools/build_map.py が同じシートから直接使う。
使い方: python3 tools/fantasy_tiles.py
"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SRC = 'docs/ref/fantasy-tiles.jpg'
OUT = 'assets/sprites/'
# 下段「戦闘画面用足場」(x0, y0, x1, y1)
FOOT = {
    'plain': (0, 668, 207, 846), 'forest': (209, 630, 419, 846), 'mountain': (422, 632, 631, 846),
    'sea': (633, 667, 843, 846), 'city': (845, 631, 1056, 846), 'base': (1058, 652, 1264, 846),
}
# 上段・中段のマップ用タイル（build_map.py が使う）
MAPTILE = {
    'village': [(0, 40, 207, 255), (208, 41, 419, 255), (421, 41, 631, 255)],
    'town': [(0, 297, 207, 526), (209, 297, 419, 525)],
    'castle': (632, 41, 948, 336), 'fort': (950, 40, 1264, 335),
    'forest': [(421, 375, 632, 572), (632, 375, 843, 572)],
    'mountain': [(845, 375, 1056, 572), (1057, 375, 1264, 572)],
}


def magenta_alpha(rgb):
    """マゼンタらしさ（赤と青が強く緑が弱い）から透明度を決める。ふちのにじみは半透明にして色も戻す"""
    a = rgb.astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = np.clip((np.minimum(r, b) - g - 60) / 90, 0, 1)  # 1 = マゼンタ
    m = ndi.grey_dilation(m, size=2) * (m > 0.02) + m * (m <= 0.02)
    alpha = 1 - m
    # 輪郭のにじみからマゼンタ成分を引く
    out = a.copy()
    k = np.clip(m, 0, .9)[..., None]
    mag = np.array([255, 0, 255], float)
    out = np.clip((out - mag * k) / np.maximum(1 - k, .1), 0, 255)
    lab, n = ndi.label(alpha > .5)
    if n > 1:
        sizes = ndi.sum(np.ones_like(alpha), lab, range(1, n + 1))
        keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= sizes.max() * .05])
        alpha = alpha * keep
    return np.dstack([out, alpha * 255]).astype(np.uint8)


if __name__ == '__main__':
    src = np.asarray(Image.open(SRC).convert('RGB'))
    for key, (x0, y0, x1, y1) in FOOT.items():
        im = Image.fromarray(magenta_alpha(src[y0:y1, x0:x1]), 'RGBA')
        im = im.crop(im.getbbox())
        im.save(f'{OUT}tile_{key}.png', optimize=True)
        print(f'{OUT}tile_{key}.png', im.size)
