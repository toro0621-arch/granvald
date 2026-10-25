"""docs/ref/sprites-and-tiles.png（設定画「ユニットグラフィック」「マップのマスグラフィック」）と
docs/ref/empire-01-sprites.png（帝国編 第1話のユニットグラフィック）、
docs/ref/zekt-v2-sprites.png（ゼクト改訂版）から機体と地形タイルを切り抜き、
背景を透明にして assets/sprites/ に保存する。絵そのものには手を加えない。
使い方: python3 tools/extract_sprites.py   （numpy, scipy, Pillow が必要）
"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SRC = 'docs/ref/sprites-and-tiles.png'
OUT = 'assets/sprites/'
# 切り抜く範囲 (x0, y0, x1, y1)。設定画のラベルとの対応：
#   big = 大きい全身の絵（戦闘シーン用）
#   down = 正面、up = 背面、left = 左、right = 右（マップ用）
#   idle = 待機、walk = 歩行、attack = 攻撃（味方のみ）
UNITS = {
    'grand':   {'big': (129, 90, 297, 253), 'down': (18, 256, 80, 314), 'up': (93, 257, 156, 312), 'left': (167, 256, 226, 316), 'right': (235, 256, 293, 317),
                'idle': (22, 346, 84, 409), 'walk': (105, 347, 183, 410), 'attack': (210, 347, 289, 409)},
    'sylph':   {'big': (439, 92, 579, 252), 'down': (325, 258, 381, 315), 'up': (394, 259, 450, 316), 'left': (469, 258, 514, 315), 'right': (530, 260, 576, 314),
                'idle': (329, 351, 380, 409), 'walk': (409, 349, 469, 409), 'attack': (494, 347, 574, 407)},
    'bulwark': {'big': (705, 108, 841, 229), 'down': (602, 258, 664, 314), 'up': (672, 258, 719, 312), 'left': (730, 259, 780, 311), 'right': (791, 258, 837, 309),
                'idle': (602, 352, 661, 405), 'walk': (674, 355, 732, 405), 'attack': (751, 357, 837, 406)},
    'raven':   {'big': (974, 96, 1099, 252), 'down': (865, 258, 918, 314), 'up': (928, 258, 984, 314), 'left': (987, 261, 1040, 312), 'right': (1043, 261, 1094, 313),
                'idle': (867, 351, 925, 407), 'walk': (935, 350, 999, 407), 'attack': (1016, 348, 1093, 405)},
    # 敵の上段のラベルは「正面」「背面」が欠けて「面」になっている
    # ゼクトは改訂版（docs/ref/zekt-v2-sprites.png、UNITS_ZEKT）を使うので、ここからは切り抜かない
    'golm':    {'big': (1225, 141, 1318, 245), 'down': (1229, 260, 1274, 309), 'up': (1275, 260, 1318, 309), 'left': (1228, 349, 1273, 398), 'right': (1276, 349, 1318, 397)},
    'vespa':   {'big': (1329, 140, 1417, 247), 'down': (1329, 260, 1375, 312), 'up': (1375, 258, 1416, 312), 'left': (1328, 346, 1374, 403), 'right': (1374, 346, 1416, 402)},
    'nemesis': {'big': (1428, 130, 1520, 249), 'down': (1431, 256, 1476, 312), 'up': (1477, 256, 1518, 312), 'left': (1428, 343, 1474, 402), 'right': (1476, 343, 1518, 402)},
}
# 帝国編 第1話のドット絵（docs/ref/empire-01-sprites.png）。歩行・攻撃は数コマ並んでいるので、分かりやすい1コマだけ。
# 攻撃エフェクト（剣の光、機銃の火、火花）がかからないコマ・範囲を選んでいる
SRC_E1 = 'docs/ref/empire-01-sprites.png'
UNITS_E1 = {
    # カラドリウスは改訂版（UNITS_CAL）を使う
    'truck':     {'big': (947, 170, 1202, 345), 'down': (1214, 203, 1286, 309), 'up': (1290, 203, 1363, 309), 'left': (1368, 203, 1435, 309), 'right': (1440, 203, 1508, 309),
                  'idle': (792, 402, 910, 498), 'walk': (937, 410, 1038, 486), 'attack': (1218, 430, 1298, 499)},
    'hound':     {'big': (30, 608, 285, 843), 'down': (300, 640, 409, 762), 'up': (412, 640, 529, 762), 'left': (532, 640, 640, 762), 'right': (644, 640, 746, 762),
                  'idle': (40, 875, 128, 962), 'walk': (155, 873, 247, 965), 'attack': (476, 858, 569, 957)},
    'golmkai':   {'big': (795, 630, 1038, 843), 'down': (1062, 643, 1172, 775), 'up': (1178, 643, 1292, 775), 'left': (1298, 643, 1402, 775), 'right': (1408, 643, 1500, 775),
                  'idle': (802, 875, 883, 968), 'walk': (915, 873, 987, 970), 'attack': (1248, 850, 1334, 958)},
}
# ゼクト（改訂版。docs/ref/zekt-v2-sprites.png）。攻撃はライフルの火を避けた範囲。
# 装甲の明るい部分が背景の水色に近いので、閉じた背景は大きいもの（脚の間など）だけ抜く
SRC_ZEKT = 'docs/ref/zekt-v2-sprites.png'
UNITS_ZEKT = {
    'zekt': {'big': (318, 125, 805, 539), 'down': (835, 195, 1000, 445), 'up': (1010, 195, 1185, 445), 'left': (1200, 195, 1340, 445), 'right': (1350, 195, 1495, 445),
             'idle': (90, 655, 295, 895), 'walk': (430, 655, 630, 895), 'attack': (770, 680, 980, 895)},
}
# カラドリウス（改訂版。docs/ref/caladrius-v2-sheet.png の下段のドット絵）。
# このシートには待機・歩行・攻撃しかないので、戦闘用の大きい絵と4方向は待機の絵で代用する（マップは向きを変えないので困らない）
SRC_CAL = 'docs/ref/caladrius-v2-sheet.png'
CAL_IDLE = (60, 745, 285, 928)
UNITS_CAL = {
    'caladrius': {'big': CAL_IDLE, 'down': CAL_IDLE, 'up': CAL_IDLE, 'left': CAL_IDLE, 'right': CAL_IDLE,
                  'idle': CAL_IDLE, 'walk': (330, 745, 560, 928), 'attack': (600, 770, 1185, 928)},
}
# マスグラフィックの立体タイル（左側の絵）
TILES = {
    'plain': (14, 544, 180, 698), 'forest': (352, 544, 513, 698), 'mountain': (672, 542, 856, 698),
    'sea': (14, 756, 180, 940), 'city': (352, 756, 513, 940), 'base': (672, 754, 856, 940),
}

def cut(img, box, tol=30, pockets=True, shadow=False, robust_bg=False, pocket_min=25):
    x0, y0, x1, y1 = box
    a = img[y0:y1, x0:x1].astype(int)
    # 背景はグラデーションなので、行ごとに左右端の中央値を背景色とみなす。
    # 絵が端にかかった行で値が狂わないよう、上下方向にも中央値でならす
    if robust_bg:
        # 行ごとの背景色：その行のうち、外周の背景色に近い画素の中央値（絵が左右両方の端にかかっていても狂わない）
        ref = np.median(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]), axis=0)
        near = np.sqrt(((a - ref) ** 2).sum(2)) < 45
        rowbg = np.array([np.median(a[y][near[y]], axis=0) if near[y].sum() >= 3 else ref for y in range(a.shape[0])])
    else:
        # 左右の端のうち、全体の背景色に近いほうを使う（絵が片側の端にかかっていても狂わない）
        left, right = np.median(a[:, :3], axis=1), np.median(a[:, -3:], axis=1)
        ref = np.median(np.concatenate([left, right]), axis=0)
        near_left = ((left - ref) ** 2).sum(1) <= ((right - ref) ** 2).sum(1)
        rowbg = np.where(near_left[:, None], left, right)
    rowbg = ndi.median_filter(rowbg, size=(15, 1), mode='nearest')[:, None, :]
    d = np.sqrt(((a - rowbg) ** 2).sum(2))
    bglike = d < tol
    if shadow:
        # 足元の影：背景と同じ色合いで暗いだけの部分も背景にする（白い羽根などは色合いが違うので残る）
        bn = rowbg / np.maximum(np.linalg.norm(rowbg, axis=2, keepdims=True), 1)
        an = a / np.maximum(np.linalg.norm(a, axis=2, keepdims=True), 1)
        ratio = np.linalg.norm(a, axis=2) / np.maximum(np.linalg.norm(rowbg, axis=2), 1)
        bglike |= ((an * bn).sum(2) > 0.996) & (ratio > 0.6) & (ratio < 1.1)
    lab, _ = ndi.label(bglike)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bgset = set(border)
    if pockets:
        # 腕と体のすき間など、閉じた背景（pocket_min 画素以上のもの）も背景にする
        sizes = ndi.sum(np.ones_like(d), lab, range(1, lab.max() + 1))
        bgset |= {i + 1 for i, s in enumerate(sizes) if s >= pocket_min}
    bg = np.isin(lab, list(bgset))
    # 外周に残る背景色のにじみを1px削る
    halo = ndi.binary_dilation(bg) & ((d < tol * 1.8) | (bglike & ~bg))
    fg = ~(bg | halo)
    # 枠線の切れ端（幅や高さが数pxの細いもの）を消す
    lab1, n1 = ndi.label(fg)
    for i, sl in enumerate(ndi.find_objects(lab1)):
        if min(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start) <= 4:
            fg[sl][lab1[sl] == i + 1] = False
    # ラベル文字などの小さなかけらを消し、いちばん大きい塊とその近くだけ残す
    lab2, n = ndi.label(ndi.binary_dilation(fg, iterations=1))
    if n > 1:
        sizes = ndi.sum(fg, lab2, range(1, n + 1))
        keep = [i + 1 for i, s in enumerate(sizes) if s >= sizes.max() * 0.1]
        fg &= np.isin(lab2, keep)
    rgba = np.dstack([a, (fg * 255)]).astype(np.uint8)
    out = Image.fromarray(rgba, 'RGBA')
    return out.crop(out.getbbox())

def pad(box, m=2):
    x0, y0, x1, y1 = box
    return (x0 - m, y0 - m, x1 + m, y1 + m)

if __name__ == '__main__':
    img = np.asarray(Image.open(SRC).convert('RGB'))
    for key, boxes in UNITS.items():
        for kind, box in boxes.items():
            name = f'{OUT}{key}.png' if kind == 'big' else f'{OUT}{key}_{kind}.png'
            im = cut(img, box if kind == 'big' else pad(box))
            im.save(name, optimize=True)
            print(name, im.size)
    img_e1 = np.asarray(Image.open(SRC_E1).convert('RGB'))
    for key, boxes in UNITS_E1.items():
        for kind, box in boxes.items():
            name = f'{OUT}{key}.png' if kind == 'big' else f'{OUT}{key}_{kind}.png'
            im = cut(img_e1, box, shadow=True, robust_bg=True)
            im.save(name, optimize=True)
            print(name, im.size)
    img_z = np.asarray(Image.open(SRC_ZEKT).convert('RGB'))
    for key, boxes in UNITS_ZEKT.items():
        for kind, box in boxes.items():
            name = f'{OUT}{key}.png' if kind == 'big' else f'{OUT}{key}_{kind}.png'
            im = cut(img_z, box, tol=24, robust_bg=True, pocket_min=1500)
            im.save(name, optimize=True)
            print(name, im.size)
    img_c = np.asarray(Image.open(SRC_CAL).convert('RGB')).copy()
    # 攻撃の絵の範囲にかかる「攻撃（剣）」の札を、すぐ下の背景色で塗りつぶしておく
    img_c[765:812, 585:705] = img_c[815:816, 585:705]
    for key, boxes in UNITS_CAL.items():
        for kind, box in boxes.items():
            name = f'{OUT}{key}.png' if kind == 'big' else f'{OUT}{key}_{kind}.png'
            im = cut(img_c, box, tol=24, robust_bg=True, pocket_min=400)
            im.save(name, optimize=True)
            print(name, im.size)
    for key, box in TILES.items():
        im = cut(img, box, tol=34, pockets=False)
        im.save(f'{OUT}tile_{key}.png', optimize=True)
        print(f'{OUT}tile_{key}.png', im.size)
