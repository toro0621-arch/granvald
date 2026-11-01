"""ステージのマップ背景（assets/stage1_map.png など）を作る。
地形データ（MAP / ROAD）は index.html から読み、森・山・市街・城・基地の見た目は
docs/ref/fantasy-tiles.jpg（ファンタジー風の地形タイル）から切り出して貼る。
海と平地は設定画の色で生成する（設定画の海にはマス目の線が入っていて切り出せないため）。
使い方: python3 tools/build_map.py [ステージ] [出力先]   （numpy, scipy, Pillow が必要）
  python3 tools/build_map.py S1 assets/stage1_map.png      … 鋼の目覚め（省略時）
  python3 tools/build_map.py E1 assets/stage_e1_map.png    … 帝国編 第1話「国境の村」
  python3 tools/build_map.py E2 assets/stage_e2_map.png    … 帝国編 第2話「狼の巣」（砦（E）は丸太の柵の砦、坑道の入口（K）は docs/ref/tile-mine.jpg）
  python3 tools/build_map.py E5 assets/stage_e5_map.png    … 帝国編 第5話「城館の夜」（夜のマップ：全体を暗い青に沈め、城と城下の家々に明かりを足す）
  python3 tools/build_map.py E8 assets/stage_e8_map.png    … 帝国編 第8話「夜明けの印」（新月の夜。第5話と同じく暗くして、倉庫と倉庫街に明かり）
  python3 tools/build_map.py E3 assets/stage_e3_map.png    … 帝国編 第3話「末席の男爵」（川（R）は水、渡しの浅瀬（S）は砂利の川底と目印の杭）
  python3 tools/build_map.py E7 assets/stage_e7_map.png    … 帝国編 第7話「兵站局の判」（夕方。塀（X）・崩れた塀（H）・門（G）・倉庫の建物（D）・大倉庫（B）・木箱と樽（M）は絵を描く）
  第8話は城壁（X）・城門（G）・橋（Q）・穀物倉庫（B）を描く。塀の内側（外から塀を越えずに行けないマス）の地面は土。
"""
import re
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

CELL = 64
SRC = 'docs/ref/sprites-and-tiles.png'
html = open('index.html', encoding='utf-8').read()
def grid(name):
    body = re.search(r'const ' + name + r'=\[(.*?)\];', html, re.S).group(1)
    return re.findall(r'"([^"]+)"', body)
STAGE = sys.argv[1] if len(sys.argv) > 1 else 'S1'
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else 'assets/stage1_map.png'
MAP, ROAD = grid('MAP_' + STAGE), grid('ROAD_' + STAGE)
ROWS, COLS = len(MAP), len(MAP[0])
W, H = COLS * CELL, ROWS * CELL
rng = np.random.default_rng(7)

# 森・山・市街・城・基地は、ファンタジー風の地形タイル（docs/ref/fantasy-tiles.jpg、範囲は tools/fantasy_tiles.py の MAPTILE）から貼る。
# 市街（C）は、帝国編の辺境では「村」、沿岸都市連合の港町では「町」
sys.path.insert(0, 'tools')
from fantasy_tiles import MAPTILE
ref = Image.open('docs/ref/fantasy-tiles.jpg').convert('RGB')
def inset(b, m=4):
    return (b[0] + m, b[1] + m, b[2] - m, b[3] - m)
PATCH = {'F': [inset(b) for b in MAPTILE['forest']], 'M': [inset(b) for b in MAPTILE['mountain']],
         'C': [inset(b) for b in (MAPTILE['village'] if STAGE.startswith('E') else MAPTILE['town'])]}
# 複数マスにまたがる建物：帝国の城（E）と味方基地（B＝砦）。第2話（E2）の E は盗賊の根城なので、城ではなく丸太の柵の砦の絵
BLOCK = {'E': inset(MAPTILE['fort'] if STAGE == 'E2' else MAPTILE['castle']), 'B': inset(MAPTILE['fort'])}
# 坑道の入口（K）：地形は山と同じ。絵は別ファイル（ユーザーが描いたタイル。今の山のタイルと同じ絵柄）
MINE = Image.open('docs/ref/tile-mine.jpg').convert('RGB')

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

# 草地の色は、ファンタジー風の地形タイルの草地（中央値 (91, 138, 47)）に合わせる（継ぎ目を目立たなくする）
grass = pixel_texture((91, 138, 47), (74, 116, 38), (116, 160, 66), .1, 1, blot=.12)
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

# 塀の内側（盤のふちから塀・門・建物を通らずに行けないマス）の地面は、踏み固めた土
SOLID = 'XDBGH'
outside = np.zeros((ROWS, COLS), bool)
st = [(x, y) for y in range(ROWS) for x in range(COLS) if (x in (0, COLS - 1) or y in (0, ROWS - 1)) and MAP[y][x] not in SOLID]
for x, y in st: outside[y, x] = True
while st:
    x, y = st.pop()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS and not outside[ny, nx] and MAP[ny][nx] not in SOLID:
            outside[ny, nx] = True; st.append((nx, ny))
inside = np.array([[(not outside[y, x]) and MAP[y][x] not in 'X' for x in range(COLS)] for y in range(ROWS)])
if inside.any() and STAGE == 'E7':
    dirt = pixel_texture((128, 112, 84), (108, 94, 70), (150, 134, 102), .14, 31, blot=.25)
    m = np.asarray(Image.fromarray((inside * 255).astype(np.uint8)).resize((W, H), Image.NEAREST)).astype(float) / 255
    m = ndi.gaussian_filter(m, 3)[..., None]
    a = np.asarray(canvas).astype(float); a[..., :3] = a[..., :3] * (1 - m) + dirt * m
    canvas = Image.fromarray(a.astype(np.uint8))

# 道路
dr = ImageDraw.Draw(canvas)
def is_road(x, y):
    # 道は建物（基地・城・市街）の手前までつなげる
    return 0 <= x < COLS and 0 <= y < ROWS and (ROAD[y][x] == '#' or MAP[y][x] in 'BEC')
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
        # 道はファンタジーの世界に合わせて土の道（白線のある舗装道路にしない）
        for p in parts:
            dr.rectangle([p[0] - 2, p[1] - 2, p[2] + 2, p[3] + 2], fill=(84, 112, 40))
        for p in parts:
            dr.rectangle(p, fill=(158, 128, 82))
        # 轍（わだち）と小石
        for _ in range(10):
            px_, py_ = X + rng.integers(int(m), int(m + w)), Y + rng.integers(int(m), int(m + w))
            dr.rectangle([px_, py_, px_ + 1, py_ + 1], fill=(126, 100, 62) if rng.random() < .6 else (190, 166, 120))

# 森・山・市街・基地を設定画から貼る（山は少し大きめに貼って重ねる）
order = sorted(((y, x) for y in range(ROWS) for x in range(COLS)), key=lambda p: (MAP[p[0]][p[1]] in 'MK', p))
for y, x in order:
    t = MAP[y][x]
    if t == 'K':
        # 坑道の入口の絵は横長なので、横幅をマスに合わせ、上下は草地のまま（ふちはにじませる）
        size = CELL + 2 * FE + 10
        hh = round(size * MINE.height / MINE.width)
        im = MINE.resize((size, hh), Image.LANCZOS)
        m = Image.new('L', (size, hh), 0); ImageDraw.Draw(m).rectangle([FE // 2, FE // 2, size - FE // 2, hh - FE // 2], fill=255)
        off = (size - CELL) // 2
        canvas.paste(im, (x * CELL - off, y * CELL + CELL - hh + FE // 2), m.filter(ImageFilter.GaussianBlur(FE / 2.5)))
        continue
    if t not in PATCH: continue
    if t == 'M' and STAGE == 'E7': continue  # 第7話の資材の山は木箱と樽（あとで描く）
    box = PATCH[t][rng.integers(len(PATCH[t]))]
    size = CELL + 2 * FE + (10 if t == 'M' else 0)
    im = ref.crop(box).resize((size, size), Image.LANCZOS)
    if rng.random() < .5 and t != 'B': im = im.transpose(Image.FLIP_LEFT_RIGHT)
    mask = MASK if t != 'M' else feather_mask(size)
    off = (size - CELL) // 2
    canvas.paste(im, (x * CELL - off, y * CELL - off), mask)

# 城と基地（2×2 マス）
for t, box in BLOCK.items():
    if t == 'B' and STAGE in ('E7', 'E8'): continue  # 倉庫はあとで屋根を描く
    xs = [x for y in range(ROWS) for x in range(COLS) if MAP[y][x] == t]
    ys = [y for y in range(ROWS) for x in range(COLS) if MAP[y][x] == t]
    if not xs: continue
    bw, bh = (max(xs) - min(xs) + 1) * CELL, (max(ys) - min(ys) + 1) * CELL
    im = ref.crop(box).resize((bw, bh), Image.LANCZOS)
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle([2, 2, im.width - 2, im.height - 2], 6, fill=255)
    canvas.paste(im, (min(xs) * CELL, min(ys) * CELL), m.filter(ImageFilter.GaussianBlur(2)))

# 海：マスの境界をノイズで少し崩して自然な海岸線にする
cellw = np.array([[1.0 if c in 'WRSQ' else 0.0 for c in row] for row in MAP])
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
# 渡しの浅瀬（S）：水を浅く明るくし、川底の砂利と目印の木の杭を描く
img = Image.fromarray(arr[..., :3].astype(np.uint8))
fd = ImageDraw.Draw(img)
for y in range(ROWS):
    for x in range(COLS):
        if MAP[y][x] != 'S': continue
        X, Y = x * CELL, y * CELL
        a = np.asarray(img).astype(float)
        cell = a[Y:Y + CELL, X - 6:X + CELL + 6]
        m = np.zeros(cell.shape[:2]); m[4:-4, 6:-6] = 1; m = ndi.gaussian_filter(m, 4)[..., None]
        sand = pixel_texture((150, 150, 120), (120, 124, 100), (186, 186, 160), .12, 20 + x, blot=.2)[Y:Y + CELL, X - 6:X + CELL + 6]
        ford = cell * .3 + sand * .7
        a[Y:Y + CELL, X - 6:X + CELL + 6] = cell * (1 - m) + ford * m
        img = Image.fromarray(a.astype(np.uint8)); fd = ImageDraw.Draw(img)
        # 小石
        for _ in range(26):
            px_, py_ = X + int(rng.integers(6, CELL - 8)), Y + int(rng.integers(6, CELL - 8))
            fd.ellipse([px_, py_, px_ + 3, py_ + 2], fill=(200, 196, 170) if rng.random() < .5 else (96, 100, 88))
        # 目印の杭（両側に一列ずつ）
        for sx in (8, CELL - 12):
            for k in range(3):
                py_ = Y + 8 + k * 19
                fd.rectangle([X + sx, py_, X + sx + 4, py_ + 10], fill=(88, 60, 34))
                fd.rectangle([X + sx, py_, X + sx + 4, py_ + 2], fill=(140, 104, 64))
                fd.line([X + sx - 2, py_ + 11, X + sx + 6, py_ + 11], fill=(230, 240, 250))
# ---- 塀・門・建物・橋・木箱（第7話・第8話。設定画にないので、ここで描く） ----
def cells(chars): return [(x, y) for y in range(ROWS) for x in range(COLS) if MAP[y][x] in chars]
def at(x, y): return MAP[y][x] if 0 <= x < COLS and 0 <= y < ROWS else '.'
sd = ImageDraw.Draw(img)
STONE, STONE_D, STONE_L, MORTAR = (132, 126, 116), (78, 74, 70), (176, 170, 158), (96, 92, 86)
def stone_block(x0, y0, x1, y1, seed, brick=10):
    """上から見た石積み（れんが目地と、ふちの明暗）"""
    x0, y0, x1, y1 = map(int, (x0, y0, x1, y1))
    sd.rectangle([x0, y0 + 3, x1, y1 + 3], fill=(40, 40, 44))  # 影
    sd.rectangle([x0, y0, x1, y1], fill=STONE)
    r = np.random.default_rng(seed)
    for yy in range(y0, y1, brick // 2 + 2):
        off = (yy // (brick // 2 + 2)) % 2 * brick // 2
        sd.line([x0, yy, x1, yy], fill=MORTAR)
        for xx in range(x0 - off, x1, brick):
            if xx > x0: sd.line([xx, yy, xx, min(yy + brick // 2 + 2, y1)], fill=MORTAR)
            if r.random() < .25:
                sd.rectangle([max(xx + 1, x0), yy + 1, min(xx + brick - 1, x1), min(yy + brick // 2 + 1, y1)], fill=(118, 112, 104) if r.random() < .5 else (146, 140, 128))
    sd.line([x0, y0, x1, y0], fill=STONE_L, width=2); sd.line([x0, y1, x1, y1], fill=STONE_D, width=2)
    sd.line([x0, y0, x0, y1], fill=STONE_L); sd.line([x1, y0, x1, y1], fill=STONE_D)

WALLISH = 'XHG'
def components(ch):
    seen = set(); out = []
    for c in cells(ch):
        if c in seen: continue
        st_ = [c]; comp = []; seen.add(c)
        while st_:
            x, y = st_.pop(); comp.append((x, y))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if at(*n) == ch and n not in seen: seen.add(n); st_.append(n)
        out.append(comp)
    return out
def crate(x, y, s_):
    sd.rectangle([x + 2, y + 3, x + s_ + 2, y + s_ + 3], fill=(40, 34, 30))
    sd.rectangle([x, y, x + s_, y + s_], fill=(156, 114, 64), outline=(70, 46, 24))
    sd.line([x, y, x + s_, y + s_], fill=(110, 76, 40), width=2); sd.line([x + s_, y, x, y + s_], fill=(110, 76, 40), width=2)
    sd.rectangle([x, y, x + s_, y + s_], outline=(70, 46, 24), width=2)
def barrel(x, y, rr, col=(124, 82, 46)):
    sd.ellipse([x - rr + 2, y - rr + 3, x + rr + 2, y + rr + 3], fill=(40, 34, 30))
    sd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col, outline=(56, 36, 20), width=2)
    sd.ellipse([x - rr + 4, y - rr + 4, x + rr - 4, y + rr - 4], outline=(70, 70, 70), width=2)

# 塀・門・倉庫・橋の絵：ユーザーが描いたタイルの資料（docs/ref/e78-tiles-a.jpg。背景はマゼンタ）から切り抜く。
# 斜め上から見た絵なので、マスの下のふちにそろえて貼り、上へはみ出してよい（山と同じ）。下の行のものほど後から貼る
sys.path.insert(0, 'tools')
from fantasy_tiles import magenta_alpha
SHEET = np.asarray(Image.open('docs/ref/e78-tiles-a.jpg').convert('RGB'))
def piece(box):
    x0, y0, x1, y1 = box
    return Image.fromarray(magenta_alpha(SHEET[y0:y1, x0:x1]), 'RGBA')
P_WALL = piece((0, 42, 205, 250))        # 都の城壁（胸壁つき、横）
P_GATE_CITY = piece((420, 42, 840, 250))  # 城門（塔が2つ）
P_BRIDGE = piece((1010, 55, 1262, 196))   # 石の橋（橋げたの上の部分。アーチは使わない）
P_GATE = piece((0, 298, 418, 525))       # 正門（石の門柱と木の扉）
P_TALL = piece((425, 298, 628, 845))     # 細長い倉庫（妻側から見た縦長の絵）
P_TALL2 = piece((636, 298, 840, 845))
P_GRANARY = piece((848, 298, 1262, 600))  # 赤い瓦の大きな倉庫（扉と麦袋）
P_BARN = piece((0, 568, 418, 845))       # 横長の古い倉庫（屋根に穴）
P_DOCK = piece((848, 588, 1262, 795))    # 荷揚げ場の石段と小舟
# 縦に通る塀は、横の塀の絵を90度回して使う（胸壁が横を向く）
P_WALL_V = P_WALL.rotate(-90, expand=True)
base = img.convert('RGBA')
draws = []  # (下のふちのy, 順番, 関数)
def put(im, x, y, w, h=None, bottom=None):
    h = h or round(im.height * w / im.width)
    im2 = im.resize((max(1, round(w)), max(1, round(h))), Image.LANCZOS)
    yy = (bottom - h) if bottom is not None else y
    base.alpha_composite(im2, (round(x), round(yy)))
def later(by, fn): draws.append((by, len(draws), fn))

wall_h = .62 if STAGE == 'E7' else .9   # 第7話は低い塀、第8話は都の高い城壁
for x, y in cells('X'):
    X, Y = x * CELL, y * CELL
    h_n = at(x - 1, y) in WALLISH or at(x + 1, y) in WALLISH
    v_n = at(x, y - 1) in WALLISH or at(x, y + 1) in WALLISH
    if v_n or not h_n:  # 縦の塀（角も）
        ww = CELL * (.9 if STAGE == 'E8' else .42)
        later(Y + CELL, lambda X=X, Y=Y, ww=ww: put(P_WALL_V, X + (CELL - ww) / 2 - (CELL * .05 if STAGE == 'E8' else 0), Y - 2, ww, CELL + 4))
    if h_n:  # 横の塀：となりの横の塀までつなぐ
        x0 = X if at(x - 1, y) in WALLISH else X + CELL * .29
        x1 = X + CELL if at(x + 1, y) in WALLISH else X + CELL * .71
        later(Y + CELL * .8, lambda x0=x0, x1=x1, Y=Y: put(P_WALL, x0, 0, x1 - x0, CELL * wall_h, bottom=Y + CELL * .8))
# 崩れた塀の穴：上下（または左右）に塀の切れはしが残り、まん中に石くずが散らばる
for x, y in cells('H'):
    X, Y = x * CELL, y * CELL; r = np.random.default_rng(50 + x + y)
    vert = at(x, y - 1) in WALLISH or at(x, y + 1) in WALLISH
    def rubble(X=X, Y=Y, r=r):
        d_ = ImageDraw.Draw(base)
        for _ in range(22):
            px_, py_ = X + int(r.integers(10, CELL - 14)), Y + int(r.integers(14, CELL - 16))
            s_ = int(r.integers(3, 9)); d_.rectangle([px_, py_, px_ + s_, py_ + s_ - 1], fill=(150, 144, 132) if r.random() < .5 else (102, 98, 92), outline=(60, 58, 56))
    if vert:
        ww = CELL * .42
        later(Y + CELL * .3, lambda X=X, Y=Y, ww=ww: put(P_WALL_V.crop((0, 0, P_WALL_V.width, P_WALL_V.height // 4)), X + (CELL - ww) / 2, Y - 2, ww, CELL * .22))
        later(Y + CELL, lambda X=X, Y=Y, ww=ww: put(P_WALL_V.crop((0, P_WALL_V.height * 3 // 4, P_WALL_V.width, P_WALL_V.height)), X + (CELL - ww) / 2, Y + CELL * .8, ww, CELL * .22))
    later(Y + CELL * .5, rubble)
# 門
for comp in components('G'):
    xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
    if STAGE == 'E8':  # 西の城壁の城門：塔の絵を、城壁のマスから右へ少しはみ出して貼る
        X, Y = min(xs) * CELL, max(ys) * CELL
        later(Y + CELL + 1, lambda X=X, Y=Y: put(P_GATE_CITY, X - CELL * .45, 0, CELL * 2.0, bottom=Y + CELL + 10))
    else:  # 第7話の正門（2マス）
        X0, X1, Y = min(xs) * CELL, (max(xs) + 1) * CELL, max(ys) * CELL
        later(Y + CELL * .8, lambda X0=X0, X1=X1, Y=Y: put(P_GATE, X0 - CELL * .25, 0, X1 - X0 + CELL * .5, bottom=Y + CELL * .86))
# 倉庫の建物（D）：横長は横長の倉庫、縦長は妻側から見た細長い倉庫
for i, comp in enumerate(components('D')):
    xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
    X0, X1, Y0, Y1 = min(xs) * CELL, (max(xs) + 1) * CELL, min(ys) * CELL, (max(ys) + 1) * CELL
    if X1 - X0 >= Y1 - Y0:
        im = P_BARN if i % 2 == 0 else P_BARN.transpose(Image.FLIP_LEFT_RIGHT)
        later(Y1, lambda im=im, X0=X0, X1=X1, Y1=Y1: put(im, X0 - 2, 0, X1 - X0 + 4, bottom=Y1 + 2))
    else:
        im = P_TALL if i % 2 == 0 else P_TALL2
        later(Y1, lambda im=im, X0=X0, X1=X1, Y1=Y1: put(im, X0 - 4, 0, X1 - X0 + 8, bottom=Y1 + 2))
# 大倉庫・穀物倉庫（B、2マス）
for comp in components('B'):
    xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
    X0, X1, Y1 = min(xs) * CELL, (max(xs) + 1) * CELL, (max(ys) + 1) * CELL
    later(Y1, lambda X0=X0, X1=X1, Y1=Y1: put(P_GRANARY, X0 - 4, 0, X1 - X0 + 8, bottom=Y1 + 2))
    if STAGE == 'E7':  # 入口の脇に、赤い印の爆薬の樽
        def bar(X0=X0, Y1=Y1):
            global sd
            sd = ImageDraw.Draw(base)
            for k, dx in enumerate((8, 22, 106, 120)): barrel(X0 + dx, Y1 + 8 + (k % 2) * 4, 7, (150, 40, 34))
        later(Y1 + 20, bar)
# 木箱と樽（第7話の資材の山）
if STAGE == 'E7':
    for x, y in cells('M'):
        X, Y = x * CELL, y * CELL
        def crates(X=X, Y=Y):
            global sd
            sd = ImageDraw.Draw(base)
            r = np.random.default_rng(700 + X + Y)
            crate(X + 6, Y + 8, 24); crate(X + 32, Y + 14, 22); crate(X + 14, Y + 34, 22)
            barrel(X + 46, Y + 46, 9); barrel(X + 12, Y + 22 + int(r.integers(26, 32)), 8)
            crate(X + 18, Y + 18, 18)
        later(Y + CELL, crates)
# 橋（Q）：橋げたの上の絵を90度回して、縦に渡す
for x, y in cells('Q'):
    X, Y = x * CELL, y * CELL
    vert = at(x - 1, y) in 'WR' or at(x + 1, y) in 'WR'
    im = P_BRIDGE.rotate(-90, expand=True) if vert else P_BRIDGE
    if vert: later(Y, lambda im=im, X=X, Y=Y: put(im, X + CELL * .1, Y - 8, CELL * .8, CELL + 16))
    else: later(Y, lambda im=im, X=X, Y=Y: put(im, X - 8, Y + CELL * .1, CELL + 16, CELL * .8))
# 第8話：北の運河の岸に、荷揚げ場の石段と小舟（飾り）
if STAGE == 'E8':
    later(CELL * 1.3, lambda: put(P_DOCK, CELL * 7.2, 0, CELL * 1.7, bottom=CELL * 1.35))
for _, _, fn in sorted(draws, key=lambda t: (t[0], t[1])): fn()
img = base.convert('RGB')
# 第7話は夕方：少し暗く、赤みのある光
if STAGE == 'E7':
    a = np.asarray(img).astype(float)
    a = a * np.array([1.0, .88, .74]) * .9 + np.array([18, 6, 0])
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

# 夜のマップ（第5話）：全体を暗い青に沈め、城（E）と城下の家々（C）の窓に暖かい明かりを足す
if STAGE in ('E5', 'E8'):  # 第8話も新月の夜（倉庫（B）と倉庫街（C）の窓に明かり）
    a = np.asarray(img).astype(float) / 255
    lum = a.mean(2, keepdims=True)
    a = (a * .32 + lum * .22) * np.array([.55, .66, 1.25])
    img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    glow = Image.new('RGB', img.size, (0, 0, 0)); gd = ImageDraw.Draw(glow)
    lights = []
    for y in range(ROWS):
        for x in range(COLS):
            if MAP[y][x] in 'CEB':
                for _ in range(5 if MAP[y][x] == 'C' else (4 if MAP[y][x] == 'B' else 7)):
                    lights.append((x * CELL + int(rng.integers(8, CELL - 8)), y * CELL + int(rng.integers(10, CELL - 8))))
    for px_, py_ in lights:
        gd.ellipse([px_ - 9, py_ - 9, px_ + 9, py_ + 9], fill=(120, 70, 20))
    glow = glow.filter(ImageFilter.GaussianBlur(6))
    img = Image.fromarray(np.clip(np.asarray(img).astype(int) + np.asarray(glow).astype(int), 0, 255).astype(np.uint8))
    d2 = ImageDraw.Draw(img)
    for px_, py_ in lights:
        d2.rectangle([px_ - 1, py_ - 2, px_ + 1, py_ + 1], fill=(255, 214, 120))
img.save(OUT_PATH, optimize=True)
print(OUT_PATH, W, H)
