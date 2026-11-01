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
    'schutze': 'docs/ref/zekt-schutze-sprites.png',    # ゼクト・シュッツェ（ニーナ。第4話から）
    'ehre': 'docs/ref/zekt-ehre-sprites.png',          # ゼクト・エーレ（ヨハン。第4話のボス）
    'eisenwacht': 'docs/ref/eisenwacht-sprites.png',   # アイゼンヴァハト（ディートリヒ。第3話のボス）
    'acker': 'docs/ref/acker-sprites.png',             # アッカー（農民兵の作業機）
    'esta': 'docs/ref/esta-front-sprites.png',         # エスタ（暁の同盟仕様・前衛。第8話）
    'esta_mortar': 'docs/ref/esta-rear-sprites.png',   # エスタ（暁の同盟仕様・後衛＝迫撃砲。第8話）
    'esta_cap': 'docs/ref/esta-captain-sprites.png',   # エスタ（暁の同盟仕様・隊長機。第8話のボス）
}
# 資料ごとにパネルの位置が少し違うときの上書き（名前 → {'BIG':…, 'DIRS':…, 'ANIM':…}）
BOXES = {
    # エスタの資料は大きい絵のパネルが下のパネルの見出しに近いので、下を短めに取る
    'esta': {'BIG': (345, 140, 758, 532),
             'DIRS': {'down': (775, 190, 898, 430), 'up': (898, 190, 1025, 430), 'left': (1025, 190, 1112, 430), 'right': (1112, 190, 1198, 430)},
             'ANIM': {'idle': (78, 630, 393, 888), 'walk': (408, 630, 697, 888), 'attack': (712, 630, 1186, 888)}},
    # 後衛の資料は画像の大きさ（1222×1287）も並びも違う
    'esta_mortar': {'BIG': (250, 150, 592, 600),
             'DIRS': {'down': (607, 240, 722, 465), 'up': (722, 240, 845, 465), 'left': (842, 240, 920, 465), 'right': (920, 240, 988, 465)},
             'ANIM': {'idle': (30, 700, 322, 1085), 'walk': (334, 700, 617, 1085), 'attack': (634, 715, 982, 1085)}},
    # 隊長機の資料（1298×1212）
    'esta_cap': {'BIG': (275, 150, 640, 572),
             'DIRS': {'down': (660, 205, 770, 448), 'up': (770, 205, 886, 448), 'left': (886, 205, 956, 448), 'right': (956, 205, 1034, 448)},
             'ANIM': {'idle': (32, 685, 326, 1015), 'walk': (344, 685, 627, 1015), 'attack': (638, 685, 1028, 1015)}},
}
# 切り抜き後に残る背景を消す場所（切り抜き後の絵での座標。cutout_hq.clear_pockets）。範囲を変えたらマゼンタの上で確かめ直す
POCKETS = {
    # ゼクト・ランスの戦闘用の絵：右腕（槍の腕）と胴の間、左腕（盾の腕）と胴の間（2か所）、右腕と槍の隙間
    'lance': [(169, 182), (308, 192), (297, 148), (108, 172)],
    # ゼクト・シュッツェの待機の絵：右手とライフルと腰の間の隙間
    'schutze_idle': [(39, 136)],
    # アイゼンヴァハト：戦闘用の絵＝左腕（盾）と胴の間、攻撃＝両腕と胴の間、正面＝左腕と胴の間・右腕（槍）と足の間
    'eisenwacht': [(285, 166)],
    'eisenwacht_attack': [(177, 107), (169, 167), (173, 192)],
    'eisenwacht_down': [(88, 74), (23, 108), (18, 130)],
    # エスタ：戦闘用・歩行・正面・背面の絵の、腕と胴の間
    'esta': [(254, 181), (136, 184), (245, 157)],
    'esta_walk': [(90, 115), (77, 136), (150, 122), (167, 172)],
    'esta_down': [(92, 147), (85, 115), (38, 103), (29, 120)],
    'esta_up': [(22, 109), (74, 84), (79, 107)],
    # エスタ（砲）：歩行＝股の間、待機＝両腕と胴の間、正面＝両腕と胴の間
    'esta_mortar_walk': [(145, 243)],
    'esta_mortar_idle': [(96, 136), (167, 137), (74, 176), (174, 181)],
    'esta_mortar_down': [(40, 87), (24, 128), (87, 99), (94, 134)],
    # エスタ（隊長機）：戦闘用・待機・歩行・正面・背面の、両腕と胴の間
    'esta_cap': [(250, 166), (132, 180)],
    'esta_cap_idle': [(83, 124), (143, 122)],
    'esta_cap_walk': [(87, 169), (170, 122)],
    'esta_cap_down': [(78, 98), (28, 99), (22, 134), (84, 131)],
    'esta_cap_up': [(22, 129), (91, 136)],
}
# 絵ごとの判定のゆるさ（ドット絵は背景の残りが少し暗めなので、明るさの下限を下げる）
POCKET_OPTS = {'esta_cap_idle': {'pale_min': 140, 'sat_max': 70}, 'esta_cap_walk': {'pale_min': 140, 'sat_max': 70}, 'esta_cap_down': {'pale_min': 130, 'sat_max': 75}, 'esta_cap_up': {'pale_min': 130, 'sat_max': 75}, 'esta_mortar_walk': {'pale_min': 140, 'sat_max': 70}, 'esta_mortar_idle': {'pale_min': 140, 'sat_max': 70}, 'esta_mortar_down': {'pale_min': 130, 'sat_max': 75}, 'esta_walk': {'pale_min': 140, 'sat_max': 70}, 'esta_down': {'pale_min': 130, 'sat_max': 75}, 'esta_up': {'pale_min': 130, 'sat_max': 75}, 'schutze_idle': {'pale_min': 140, 'sat_max': 70}, 'eisenwacht_attack': {'pale_min': 140, 'sat_max': 70}, 'eisenwacht_down': {'pale_min': 130, 'sat_max': 75}}
# 別の絵にそろえる（名前 → {種類: 使う種類}）。ゼクト・ランスの待機は歩行の絵に統一（ユーザーの希望）
SAME = {'lance': {'idle': 'walk'}}
BIG = (318, 140, 752, 556)
# 4方向のパネルの中の4体（正面・背面・左・右）。資料ごとに少しずれるので広めに取る（ex.cut は一番大きい塊だけ残す）
DIRS = {'down': (772, 190, 897, 428), 'up': (897, 190, 1020, 428), 'left': (1020, 190, 1116, 428), 'right': (1116, 190, 1204, 428)}
ANIM = {'idle': (32, 656, 366, 896), 'walk': (382, 656, 691, 896), 'attack': (708, 660, 1196, 896)}


def dot(img, box):
    return drop_shadow(ex.cut(img, box, tol=24, robust_bg=True, pocket_min=600, pocket_dark=0.35))


def run(name, src):
    img = np.asarray(Image.open(src).convert('RGB'))
    o = BOXES.get(name, {})
    BIG, DIRS, ANIM = o.get('BIG', globals()['BIG']), o.get('DIRS', globals()['DIRS']), o.get('ANIM', globals()['ANIM'])
    big = drop_shadow(hq.cut_outline(img, BIG))
    if name in POCKETS:
        big = hq.clear_pockets(big, POCKETS[name])
    big.save(f'{OUT}{name}.png', optimize=True)
    print(f'{name}.png', big.size)
    for k, box in DIRS.items():
        im = dot(img, box)
        if f'{name}_{k}' in POCKETS:
            im = hq.clear_pockets(im, POCKETS[f'{name}_{k}'], **POCKET_OPTS.get(f'{name}_{k}', {}))
        im.save(f'{OUT}{name}_{k}.png', optimize=True)
        print(f'{name}_{k}.png', im.size)
    same = SAME.get(name, {})
    for k, box in ANIM.items():
        im = dot(img, ANIM[same[k]] if k in same else box)
        if f'{name}_{k}' in POCKETS:
            im = hq.clear_pockets(im, POCKETS[f'{name}_{k}'], **POCKET_OPTS.get(f'{name}_{k}', {}))
        im.save(f'{OUT}{name}_{k}.png', optimize=True)
        print(f'{name}_{k}.png', im.size)


if __name__ == '__main__':
    for name, src in SHEETS.items():
        if len(sys.argv) > 1 and name not in sys.argv[1:]:
            continue
        run(name, src)
