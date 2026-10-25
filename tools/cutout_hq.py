"""戦闘用・ステータス用の大きい機体の絵（assets/sprites/<機体>.png）を、きれいに切り抜き直す。

tools/extract_sprites.py と同じ設定画・同じ範囲を使い、背景の抜き方だけを丁寧にしたもの。
  1. 背景の色を「なめらかな面」として推定する（グラデーションや、パネルの明るさのむらに強い）
  2. extract_sprites.py の切り抜きを土台にして（白い装甲や羽根はそこで守られている）、
     そのふちに残る「背景色と黒い輪郭線が混ざった色」のにじみを、背景のそば数画素だけ抜く
  3. 足元の影（背景と同じ色合いで暗いだけの部分）を抜く（影が描かれている整備車両だけ）
  4. ラベル文字・枠線のかけら・細い線・1画素の毛羽を消す
  5. ふちを半画素だけなめらかにする（縮小表示したときにギザギザしない）
使い方: python3 tools/cutout_hq.py            （全機体）
        python3 tools/cutout_hq.py grand zekt （指定した機体だけ）
extract_sprites.py を実行し直すと大きい絵も上書きされるので、そのあとにこちらも実行する。
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, 'tools')
import extract_sprites as ex  # noqa: E402

OUT = 'assets/sprites/'
INK = np.array([22.0, 22.0, 30.0])  # 輪郭線のおおよその色

def smooth_bg(a, known, sigma):
    """known（背景と分かっている画素）の色から、絵の裏側も含めた背景の色の面を推定する（正規化畳み込み）"""
    w = ndi.gaussian_filter(known.astype(float), sigma)
    out = np.empty_like(a, dtype=float)
    for c in range(3):
        out[..., c] = ndi.gaussian_filter(a[..., c] * known, sigma) / np.maximum(w, 1e-6)
    ref = np.median(a[known], axis=0) if known.any() else np.median(a.reshape(-1, 3), axis=0)
    out[w < 1e-3] = ref
    return out

def border_connected(mask):
    lab, _ = ndi.label(mask)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    return np.isin(lab, list(edge)), lab

def old_mask(img, box, opts):
    """extract_sprites.py の cut() と同じ判定で、機体の画素（True）の配列を返す（切り取り前の大きさのまま）"""
    a = img[box[1]:box[3], box[0]:box[2]]
    im = ex.cut(img, box, **opts)
    # cut() は余白を切り落として返すので、元の範囲での位置を探して戻す
    full = np.zeros(a.shape[:2], bool)
    al = np.asarray(im)[..., 3] > 0
    rgb = np.asarray(im)[..., :3].astype(int)
    H, W = al.shape
    for oy in range(a.shape[0] - H + 1):
        for ox in range(a.shape[1] - W + 1):
            if (np.abs(a[oy:oy + H, ox:ox + W].astype(int) - rgb)[al].max(initial=0)) == 0:
                full[oy:oy + H, ox:ox + W] = al
                return full
    raise RuntimeError('位置が見つからない')

def cut_hq(img, box, old_opts, mix_tol=16, mix_max=0.75, halo_px=3, shadow=False):
    x0, y0, x1, y1 = box
    a = img[y0:y1, x0:x1].astype(float)
    h, w, _ = a.shape
    fg0 = old_mask(img, box, old_opts)          # これまでの切り抜き（白い装甲・羽根などは守られている）
    bg0 = ~fg0
    # --- 1. 背景の面を推定（これまで背景だった画素から）
    B = smooth_bg(a, bg0 & ndi.binary_erosion(bg0, iterations=1), max(h, w) / 14)
    # --- 2. 背景色と輪郭線の色が混ざった画素（ふちのにじみ）を、背景のすぐそば（halo_px 以内）だけ背景に戻す
    seg = INK[None, None, :] - B
    t = ((a - B) * seg).sum(2) / np.maximum((seg ** 2).sum(2), 1)
    proj = B + np.clip(t, 0, 1)[..., None] * seg
    off = np.sqrt(((a - proj) ** 2).sum(2))
    mix = (off < mix_tol) & (t > 0.03) & (t < mix_max)
    near = ndi.binary_dilation(bg0, iterations=halo_px)
    cand = mix & near & fg0
    bg = bg0.copy()
    for _ in range(halo_px):                     # 背景から順に1画素ずつ、つながっている分だけ広げる
        grow = cand & ndi.binary_dilation(bg) & ~bg
        if not grow.any():
            break
        bg |= grow
    # --- 3. 足元の影：背景と同じ色合いで暗いだけの部分（下の方だけ）。外の背景とつながっている分を抜く
    if shadow:
        Bn = B / np.maximum(np.linalg.norm(B, axis=2, keepdims=True), 1)
        an = a / np.maximum(np.linalg.norm(a, axis=2, keepdims=True), 1)
        ratio = np.linalg.norm(a, axis=2) / np.maximum(np.linalg.norm(B, axis=2), 1)
        sh = ((an * Bn).sum(2) > 0.96) & (ratio > 0.3) & (ratio < 0.98) & fg0
        sh[: int(h * 0.7)] = False
        lab, _ = ndi.label(sh | bg)
        ok = set(np.unique(lab[bg])) - {0}
        bg |= sh & np.isin(lab, list(ok))
    fg = ~bg
    # --- 4. かけら・細い線を消す
    lab1, _ = ndi.label(fg)
    for i, sl in enumerate(ndi.find_objects(lab1)):
        if sl is None:
            continue
        hh, ww = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if min(hh, ww) <= 4 or (max(hh, ww) >= 8 * min(hh, ww) and min(hh, ww) <= 7):
            fg[sl][lab1[sl] == i + 1] = False
    lab2, n = ndi.label(ndi.binary_dilation(fg, iterations=1))
    if n > 1:
        sizes = ndi.sum(fg, lab2, range(1, n + 1))
        keep = [i + 1 for i, s in enumerate(sizes) if s >= sizes.max() * 0.1]
        fg &= np.isin(lab2, keep)
    # 1画素だけ飛び出した毛羽を落とす
    nb = ndi.uniform_filter(fg.astype(float), 3) * 9
    fg &= ~(fg & (nb <= 2.5))
    # --- 5. ふちだけ少しなめらかに（外周の1画素を半透明に）
    alpha = fg.astype(float)
    edge = fg & ~ndi.binary_erosion(fg)
    soft = ndi.uniform_filter(fg.astype(float), 3)
    alpha[edge] = np.clip(soft[edge] * 1.3, 0.6, 1)
    rgba = np.dstack([a, alpha * 255]).round().astype(np.uint8)
    out = Image.fromarray(rgba, 'RGBA')
    return out.crop(out.getbbox())

def cut_matte(img, box, t0=12, t1=32, label_box=None):
    """背景が一色に近いなめらかな水色で、機体が暗い絵（カラドリウス）向けの抜き方。
    1. 背景の色の面を推定する
    2. 画素ごとに「背景との差」から透明度を決める（ふちは半透明）。白い羽根飾りは背景と明るさが近いが、
       背景は青みがある（青−赤 が約30）のに羽根は青みがないので、青みの差を大きめに数えて見分ける
    3. 半透明の画素から背景の色を差し引いて、ふちに水色が残らないようにする
    4. ラベル文字やかけらを消し、いちばん大きい塊だけ残す
    輪郭線に囲まれたすき間（腕と盾の間など）も、色で判定するので自然に抜ける"""
    x0, y0, x1, y1 = box
    a = img[y0:y1, x0:x1].astype(float)
    drop = np.zeros(a.shape[:2], bool)
    if label_box:
        # 札の四角と、そこから横に伸びるパネルの枠線（範囲の上端の数行）を捨てる
        lx0, ly0, lx1, ly1 = label_box
        drop[max(0, ly0 - y0):max(0, ly1 - y0), max(0, lx0 - x0):max(0, lx1 - x0)] = True
        drop[:6] = True
    def diff(a, B):
        rgb = np.sqrt(((a - B) ** 2).sum(-1))
        chroma = np.abs((a[..., 2] - a[..., 0]) - (B[..., 2] - B[..., 0]))
        return np.maximum(rgb, chroma * 1.6)
    ref = np.median(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]), axis=0)
    known = diff(a, ref[None, None, :]) < 10
    B = smooth_bg(a, known, max(a.shape[:2]) / 10)
    d = diff(a, B)
    alpha = np.clip((d - t0) / (t1 - t0), 0, 1)
    alpha[drop] = 0
    # 足元の薄い水色の影：背景と同じ青みで、少し暗いだけの画素（下の方だけ）を抜く
    H = a.shape[0]
    lum, Bl = a.mean(-1), B.mean(-1)
    chroma_like = np.abs((a[..., 2] - a[..., 0]) - (B[..., 2] - B[..., 0])) < 14
    shadow = chroma_like & (lum > Bl * .5) & (lum < Bl * 1.05)
    shadow[: int(H * .8)] = False
    alpha[shadow] = 0
    # いちばん大きい塊だけ残す（ラベルの札・パネルの枠線を消す）
    solid = alpha > .5
    lab, n = ndi.label(ndi.binary_dilation(solid, iterations=1))
    if n > 1:
        sizes = ndi.sum(solid, lab, range(1, n + 1))
        alpha *= lab == (int(np.argmax(sizes)) + 1)
    # 1画素だけの毛羽・孤立した半透明を消す
    alpha[ndi.uniform_filter((alpha > .5).astype(float), 3) * 9 <= 1.5] = 0
    # 背景色を差し引く（色の戻し）
    k = np.maximum(alpha, 1e-3)[..., None]
    F = np.clip((a - (1 - alpha)[..., None] * B) / k, 0, 255)
    F[alpha >= .999] = a[alpha >= .999]
    rgba = np.dstack([F, alpha * 255]).round().astype(np.uint8)
    out = Image.fromarray(rgba, 'RGBA')
    return out.crop(out.getbbox())

def cut_outline(img, box, label_box=None, tol=16, pocket_tol=8, pocket_min=60):
    """輪郭線がはっきりした大きい設定画（カラドリウスの正面の絵）向けの抜き方。
    色だけで透明度を決める cut_matte だと、装甲の明るいハイライトや足の甲が背景の水色に近くて半透明になるので、
    1. 背景に近い色の画素のうち、範囲のふちからつながっているものだけを背景にする（輪郭線の内側は残る）
    2. 輪郭線に囲まれた背景（腕と体のすき間、脚の間など）は、ほぼ背景の色そのもので、ある程度の広さがあるものだけ抜く
    3. 背景と接するふちの1〜2画素だけ、背景との差から半透明にして背景色を差し引く
    白い羽根飾りは、背景には青みがあり羽根にはないので、青みの差を大きめに数えて見分ける（cut_matte と同じ）"""
    x0, y0, x1, y1 = box
    a = img[y0:y1, x0:x1].astype(float)
    def diff(a, B):
        rgb = np.sqrt(((a - B) ** 2).sum(-1))
        chroma = np.abs((a[..., 2] - a[..., 0]) - (B[..., 2] - B[..., 0]))
        return np.maximum(rgb, chroma * 1.6)
    ref = np.median(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]), axis=0)
    known = diff(a, ref[None, None, :]) < 10
    B = smooth_bg(a, known, max(a.shape[:2]) / 10)
    d = diff(a, B)
    bgl = d < tol
    # パネルの枠線（あざやかな青。機体には使われていない色）も背景として扱う
    bgl |= (a[..., 2] - a[..., 0] > 90)
    if label_box:
        lx0, ly0, lx1, ly1 = label_box
        bgl[max(0, ly0 - y0):max(0, ly1 - y0), max(0, lx0 - x0):max(0, lx1 - x0)] = True
    lab, n = ndi.label(bgl)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    for i, sl in enumerate(ndi.find_objects(lab)):
        if sl is None or (i + 1) in border:
            continue
        m = lab[sl] == i + 1
        if m.sum() >= pocket_min and np.median(d[sl][m]) < pocket_tol:
            bg[sl] |= m
    # 足元の薄い水色の影：背景と同じ青みで少し暗いだけの画素（下の方だけ）。外の背景とつながっている分を抜く
    H = a.shape[0]
    lum, Bl = a.mean(-1), B.mean(-1)
    sh = (np.abs((a[..., 2] - a[..., 0]) - (B[..., 2] - B[..., 0])) < 24) & (lum > Bl * .5) & (lum < Bl * 1.2)
    sh[: int(H * .85)] = False
    lab3, _ = ndi.label(sh | bg)
    ok = set(np.unique(lab3[bg])) - {0}
    bg |= sh & np.isin(lab3, list(ok))
    fg = ~bg
    # 下のふちに残る枠線の細い横線（高さ1〜2画素）を消す
    lo = int(H * .95)
    fg[lo:] &= ndi.binary_opening(fg, structure=np.ones((4, 1)))[lo:]
    # いちばん大きい塊だけ残す（札・枠線・かけらを消す）
    lab2, n2 = ndi.label(ndi.binary_dilation(fg, iterations=1))
    if n2 > 1:
        sizes = ndi.sum(fg, lab2, range(1, n2 + 1))
        fg &= lab2 == (int(np.argmax(sizes)) + 1)
    # 1画素だけ飛び出した毛羽を落とす
    nb = ndi.uniform_filter(fg.astype(float), 3) * 9
    fg &= ~(fg & (nb <= 2.5))
    alpha = fg.astype(float)
    edge = fg & ndi.binary_dilation(~fg, iterations=2)
    alpha[edge] = np.clip((d[edge] - 6) / 34, 0.25, 1)
    k = np.maximum(alpha, 1e-3)[..., None]
    F = np.clip((a - (1 - alpha)[..., None] * B) / k, 0, 255)
    F[alpha >= .999] = a[alpha >= .999]
    rgba = np.dstack([F, alpha * 255]).round().astype(np.uint8)
    out = Image.fromarray(rgba, 'RGBA')
    return out.crop(out.getbbox())

def matte_jobs():
    """カラドリウスの全部の絵（戦闘用・4方向・待機・歩行・攻撃）。戦闘用の大きい絵だけ cut_outline、ほかは cut_matte で抜く"""
    j = []
    for k, b in ex.UNITS_CAL.items():
        for kind, box in b.items():
            name = f'{k}.png' if kind == 'big' else f'{k}_{kind}.png'
            # 攻撃の絵の範囲には「攻撃（剣）」の札がかかるので塗りつぶす
            if kind == 'big':
                # 大きい正面の設定画は輪郭線がはっきりしているので cut_outline で抜く（「正面」の札は消す）
                j.append((name, ex.SRC_CAL, box, {'outline': True, 'label_box': (20, 108, 130, 152)}))
                continue
            j.append((name, ex.SRC_CAL, box, {'label_box': (600, 770, 705, 790)} if kind == 'attack' else {}))
    return j

def jobs():
    """(機体名, 設定画, 範囲, オプション) の一覧。範囲は extract_sprites.py と同じ"""
    j = []
    for k, b in ex.UNITS.items():
        j.append((k, ex.SRC, b['big'], {'old_opts': {}}))
    for k, b in ex.UNITS_E1.items():
        # 足元に青い影が描かれているのは整備車両だけ。ほかの機体で影抜きをすると、背景に近い色の足先まで消えてしまう
        j.append((k, ex.SRC_E1, b['big'], {'old_opts': {'shadow': True, 'robust_bg': True}, 'shadow': k == 'truck'}))
    for k, b in ex.UNITS_ZEKT.items():
        j.append((k, ex.SRC_ZEKT, b['big'], {'old_opts': {'tol': 24, 'robust_bg': True, 'pocket_min': 1500}}))
    # カラドリウスは cut_matte（matte_jobs）で抜く
    return j

if __name__ == '__main__':
    only = set(sys.argv[1:])
    cache = {}
    for key, src, box, opt in jobs():
        if only and key not in only:
            continue
        if src not in cache:
            cache[src] = np.asarray(Image.open(src).convert('RGB'))
        im = cut_hq(cache[src], box, **opt)
        im.save(f'{OUT}{key}.png', optimize=True)
        print(f'{OUT}{key}.png', im.size)
    for name, src, box, opt in matte_jobs():
        if only and name.split('.')[0].split('_')[0] not in only:
            continue
        if src not in cache:
            cache[src] = np.asarray(Image.open(src).convert('RGB'))
        opt = dict(opt)
        im = cut_outline(cache[src], box, **{k: v for k, v in opt.items() if k != 'outline'}) if opt.get('outline') else cut_matte(cache[src], box, **opt)
        im.save(f'{OUT}{name}', optimize=True)
        print(f'{OUT}{name}', im.size)
