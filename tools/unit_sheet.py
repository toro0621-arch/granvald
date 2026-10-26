"""ゼクトの資料（docs/ref/zekt-v2-sprites.png）と同じ形式の機体の資料から、機体の絵を切り抜く。
資料はどれも同じ並び（戦闘用の大きい絵、4方向、待機・歩行・攻撃）なので、パネルの位置は共通。
大きい絵は cutout_hq.py の cut_outline、ドット絵は extract_sprites.py の cut（ゼクトと同じ設定）で抜き、
足元の薄い水色の影は zekt_cannon.py の drop_shadow で消す。4方向は、決まった幅で4つに分けて抜く。
使い方: python3 tools/unit_sheet.py            （下の SHEETS を全部）
        python3 tools/unit_sheet.py lance      （1機だけ）
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, 'tools')
import extract_sprites as ex
import cutout_hq as hq
from zekt_cannon import drop_shadow

OUT = 'assets/sprites/'
# 機体の名前（assets/sprites/<名前>.png）→ 資料
SHEETS = {
    'lance': 'docs/ref/zekt-lance-sprites.png',        # ゼクト・ランス（レオ。第3話から）
    'eisenwacht': 'docs/ref/eisenwacht-sprites.png',   # アイゼンヴァハト（ディートリヒ。第3話のボス）
    'acker': 'docs/ref/acker-sprites.png',             # アッカー（農民兵の作業機）
}
BIG = (318, 140, 752, 556)
# 4方向のパネルの中の4体（正面・背面・左・右）。資料ごとに少しずれるので広めに取る（ex.cut は一番大きい塊だけ残す）
DIRS = {'down': (772, 190, 897, 428), 'up': (897, 190, 1020, 428), 'left': (1020, 190, 1116, 428), 'right': (1116, 190, 1204, 428)}
ANIM = {'idle': (32, 656, 366, 896), 'walk': (382, 656, 691, 896), 'attack': (708, 660, 1196, 896)}


def dot(img, box):
    return drop_shadow(ex.cut(img, box, tol=24, robust_bg=True, pocket_min=600, pocket_dark=0.35))


def run(name, src):
    img = np.asarray(Image.open(src).convert('RGB'))
    big = drop_shadow(hq.cut_outline(img, BIG))
    big.save(f'{OUT}{name}.png', optimize=True)
    print(f'{name}.png', big.size)
    for k, box in DIRS.items():
        im = dot(img, box)
        im.save(f'{OUT}{name}_{k}.png', optimize=True)
        print(f'{name}_{k}.png', im.size)
    for k, box in ANIM.items():
        im = dot(img, box)
        im.save(f'{OUT}{name}_{k}.png', optimize=True)
        print(f'{name}_{k}.png', im.size)


if __name__ == '__main__':
    for name, src in SHEETS.items():
        if len(sys.argv) > 1 and name not in sys.argv[1:]:
            continue
        run(name, src)
