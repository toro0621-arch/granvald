"""グラウヴォルフ（第2話のボス）の絵を切り抜く。元はユーザーが用意した絵で、背景はマゼンタ一色。
- docs/ref/graywolf-big.jpg      → assets/sprites/graywolf.png（戦闘用・ステータス用の大きい絵）
- docs/ref/graywolf-sprites.jpg  → 4列×2行のドット絵。上段：正面・背面・左・右、下段：待機・歩行・攻撃（攻撃は鉈が右へはみ出すので2マス分）
使い方: python3 tools/graywolf.py
"""
import numpy as np
from PIL import Image
from fantasy_tiles import magenta_alpha

OUT = 'assets/sprites/'


def cut(src, box=None):
    a = np.asarray(Image.open(src).convert('RGB'))
    if box:
        x0, y0, x1, y1 = box
        a = a[y0:y1, x0:x1]
    # 画像のふちに黒い線が入っていることがあるので、まわり6px は捨てる
    a = a[6:-6, 6:-6]
    im = Image.fromarray(magenta_alpha(a), 'RGBA')
    return im.crop(im.getbbox())


if __name__ == '__main__':
    big = cut('docs/ref/graywolf-big.jpg')
    big.save(OUT + 'graywolf.png', optimize=True)
    print('graywolf.png', big.size)
    W, H = 1408, 768
    cw, ch = W // 4, H // 2
    frames = {'down': (0, 0, 1), 'up': (1, 0, 1), 'left': (2, 0, 1), 'right': (3, 0, 1),
              'idle': (0, 1, 1), 'walk': (1, 1, 1), 'attack': (2, 1, 2)}
    for name, (c, r, span) in frames.items():
        im = cut('docs/ref/graywolf-sprites.jpg', (c * cw, r * ch, (c + span) * cw, (r + 1) * ch))
        # マップ用は小さいドット絵として使うので、高さ 180px にそろえる（ほかの機体の待機の絵と同じくらい）
        k = 180 / im.height
        im = im.resize((max(1, round(im.width * k)), 180), Image.LANCZOS)
        im.save(f'{OUT}graywolf_{name}.png', optimize=True)
        print(f'graywolf_{name}.png', im.size)
