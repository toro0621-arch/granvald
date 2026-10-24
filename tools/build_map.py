"""第1話のマップ背景 assets/stage1_map.png を作る。
地形データ（MAP / ROAD）は index.html から読み、森・山・市街・城・基地の見た目は
docs/ref/sprites-and-tiles.png の「マップ全体のイメージ」から切り出して貼る。
海と平地は設定画の色で生成する（設定画の海にはマス目の線が入っていて切り出せないため）。
使い方: python3 tools/build_map.py   （numpy, scipy, Pillow が必要）
"""
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

CELL = 64
SRC = 'docs/ref/sprites-and-tiles.png'
html = open('index.html', encoding='utf-8').read()
def grid(name):
    body = re.search(r'const ' + name + r'=\[(.*?)\];', html, re.S).group(1)
    return re.findall(r'"([^"]+)"', body)
MAP, ROAD = grid('MAP'), grid('ROAD')
ROWS, COLS = len(MAP), len(MAP[0])
W, H = COLS * CELL, ROWS * CELL
rng = np.random.default_rng(7)
ref = Image.open(SRC).convert('RGB')

# 設定画「マップ全体のイメージ（例：第1話）」から切り出す場所 (x0, y0, x1, y1)
PATCH = {
    'F': [(1099, 512, 1135, 548), (1462, 635, 1498, 671), (1051, 635, 1087, 671), (1423, 626, 1459, 662)],
    'M': [(1055, 505, 1105, 555), (1440, 540, 1495, 595), (1080, 915, 1135, 970), (1460, 895, 1515, 950)],
    'C': [(1195, 842, 1231, 878), (1330, 854, 1366, 890), (1231, 833, 1267, 869), (1340, 820, 1376, 856), (1380, 850, 1416, 886)],
}
# 複数マスにまたがる建物：帝国の城（E）と味方基地（B）
BLOCK = {'E': (1240, 500, 1322, 556), 'B': (1248, 858, 1324, 934)}

def noise(shape, scale, seed):
    r = np.random.default_rng(seed).random((shape[0] // scale + 2, shape[1] // scale + 2))
    return np.asarray(Image.fromarray((r * 255).astype(np.uint8)).resize((shape[1] + 2 * scale, shape[0] + 2 * scale), Image.BICUBIC))[scale:scale + shape[0], scale:scale + shape[1]] / 255

def pixel_texture(base, dark, light, density, seed, px=2, blot=.3):
    """2px 単位のドット感がある地面テクスチャ"""
    h, w = H // px, W // px
    r = np.random.default_rng(seed).random((h, w))
    n = noise((h, w), 6, seed + 1)
    out = np.empty((h, w, 3))
    out[:] = base
    out[(r < density) | (n < blot)] = dark
    out[(r > 1 - density * .7) & (n > .45)] = light
    return np.asarray(Image.fromarray(out.astype(np.uint8)).resize((W, H), Image.NEAREST)).astype(float)

grass = pixel_texture((112, 140, 42), (92, 114, 32), (146, 166, 84), .1, 1, blot=.12)
water = pixel_texture((4, 72, 162), (0, 60, 146), (22, 98, 186), .06, 2, blot=.08)
# 海のさざ波（横に短い明るい線）
wimg = Image.fromarray(water.astype(np.uint8)); d = ImageDraw.Draw(wimg)
for _ in range(COLS * ROWS * 9):
    x, y = rng.integers(0, W), rng.integers(0, H)
    d.rectangle([x, y, x + int(rng.integers(6, 14)), y + 1], fill=(70, 140, 210))
    if rng.random() < .25: d.rectangle([x + 4, y - 2, x + 7, y - 1], fill=(150, 200, 240))
water = np.asarray(wimg).astype(float)

canvas = Image.fromarray(grass.astype(np.uint8)).convert('RGBA')
FE = 8  # 隣のマスへにじませる幅（継ぎ目を目立たなくする）
def clean_lines(im):
    """設定画に入っている薄いマス目の線（周りより明るい1〜2pxの縦横線）を消す"""
    a = np.asarray(im).astype(float)
    for axis in (0, 1):
        b = a if axis == 1 else a.transpose(1, 0, 2)
        lum = b.mean(2)
        for j in range(2, b.shape[1] - 2):
            nb = (lum[:, j - 2] + lum[:, j + 2]) / 2
            diff = lum[:, j] - nb
            # 線は列のほぼ全体で明るい。絵の一部が明るいだけの列は触らない
            if np.median(diff) > 14 and (diff > 6).mean() > .8:
                b[:, j] = (b[:, j - 2] + b[:, j + 2]) / 2
        a = b if axis == 1 else b.transpose(1, 0, 2)
    return Image.fromarray(a.astype(np.uint8))

def feather_mask(size):
    m = Image.new('L', (size, size), 0); ImageDraw.Draw(m).rectangle([FE // 2, FE // 2, size - FE // 2, size - FE // 2], fill=255)
    return m.filter(ImageFilter.GaussianBlur(FE / 2.5))
MASK = feather_mask(CELL + 2 * FE)

# 道路
dr = ImageDraw.Draw(canvas)
def is_road(x, y):
    return 0 <= x < COLS and 0 <= y < ROWS and (ROAD[y][x] == '#' or MAP[y][x] in 'BE')
for y in range(ROWS):
    for x in range(COLS):
        if ROAD[y][x] != '#': continue
        X, Y, w = x * CELL, y * CELL, CELL * .36
        m = (CELL - w) / 2
        parts = [(X + m, Y + m, X + m + w, Y + m + w)]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if is_road(x + dx, y + dy):
                parts.append((X + (CELL / 2 if dx > 0 else 0 if dx < 0 else m), Y + (CELL / 2 if dy > 0 else 0 if dy < 0 else m),
                              X + (CELL if dx > 0 else CELL / 2 if dx < 0 else m + w), Y + (CELL if dy > 0 else CELL / 2 if dy < 0 else m + w)))
        for p in parts:
            dr.rectangle([p[0] - 2, p[1] - 2, p[2] + 2, p[3] + 2], fill=(150, 148, 136))
        for p in parts:
            dr.rectangle(p, fill=(88, 86, 82))
        horiz = is_road(x - 1, y) or is_road(x + 1, y)
        for i in range(2):
            if horiz: dr.rectangle([X + CELL * (.1 + i * .5), Y + CELL / 2 - 1, X + CELL * (.34 + i * .5), Y + CELL / 2 + 1], fill=(225, 222, 200))
            else: dr.rectangle([X + CELL / 2 - 1, Y + CELL * (.1 + i * .5), X + CELL / 2 + 1, Y + CELL * (.34 + i * .5)], fill=(225, 222, 200))

# 森・山・市街・基地を設定画から貼る（山は少し大きめに貼って重ねる）
order = sorted(((y, x) for y in range(ROWS) for x in range(COLS)), key=lambda p: (MAP[p[0]][p[1]] == 'M', p))
for y, x in order:
    t = MAP[y][x]
    if t not in PATCH: continue
    box = PATCH[t][rng.integers(len(PATCH[t]))]
    size = CELL + 2 * FE + (10 if t == 'M' else 0)
    im = clean_lines(ref.crop(box)).resize((size, size), Image.LANCZOS)
    if rng.random() < .5 and t != 'B': im = im.transpose(Image.FLIP_LEFT_RIGHT)
    mask = MASK if t != 'M' else feather_mask(size)
    off = (size - CELL) // 2
    canvas.paste(im, (x * CELL - off, y * CELL - off), mask)

# 城と基地（2×2 マス）
for t, box in BLOCK.items():
    xs = [x for y in range(ROWS) for x in range(COLS) if MAP[y][x] == t]
    ys = [y for y in range(ROWS) for x in range(COLS) if MAP[y][x] == t]
    if not xs: continue
    bw, bh = (max(xs) - min(xs) + 1) * CELL, (max(ys) - min(ys) + 1) * CELL
    im = ref.crop(box).resize((bw, bh), Image.LANCZOS)
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle([2, 2, im.width - 2, im.height - 2], 6, fill=255)
    canvas.paste(im, (min(xs) * CELL, min(ys) * CELL), m.filter(ImageFilter.GaussianBlur(2)))

# 海：マスの境界をノイズで少し崩して自然な海岸線にする
cellw = np.array([[1.0 if c == 'W' else 0.0 for c in row] for row in MAP])
wm = np.asarray(Image.fromarray((cellw * 255).astype(np.uint8)).resize((W, H), Image.NEAREST)) / 255
wm = ndi.gaussian_filter(wm, 12) + (noise((H, W), 14, 5) - .5) * .75 + (noise((H, W), 3, 6) - .5) * .12
# 盤面の外周は地形どおり（にじませない）
sea = wm > .5
land_dist = ndi.distance_transform_edt(sea)
arr = np.asarray(canvas).astype(float)
arr[..., :3][sea] = water[sea]
shallow = sea & (land_dist < 9)
k = np.clip(1 - land_dist / 9, 0, 1)[..., None] * .6
arr[..., :3] = np.where(shallow[..., None], arr[..., :3] * (1 - k) + np.array([40, 160, 210]) * k, arr[..., :3])
fn = noise((H, W), 2, 9)
foam = sea & ((land_dist < 2.5) | ((land_dist < 5) & (fn > .62)))
arr[..., :3][foam] = (228, 242, 255)
# 陸側の海岸に岩場（茶色の縁）
ld = ndi.distance_transform_edt(~sea)
rock = (~sea) & (ld < 4) & (noise((H, W), 2, 11) > .25)
arr[..., :3][rock] = arr[..., :3][rock] * .35 + np.array([120, 92, 60]) * .65
Image.fromarray(arr[..., :3].astype(np.uint8)).save('assets/stage1_map.png', optimize=True)
print('assets/stage1_map.png', W, H)
