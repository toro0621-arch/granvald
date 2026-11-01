# 顔グラ（assets/faces/*.png、128×128）を設定画から切り抜き直す。帝国編の全員分。
# どの人も同じ構図にそろえる：顔を左右のまん中に置き、頭のてっぺんの少し上から、あごが下から3割くらいのところに来る大きさ。
#   ht＝頭（髪・帽子）のてっぺんの y、ch＝あごの y、cx＝顔のまん中の x、w＝頭の幅、px＝パネルの左右（はみ出さない）
#   lim＝これより上は切らない（名前の札の下のふち）。札に頭がかかっているときは、札を塗らずに札の下から切る（塗ると髪が平らに欠けて見える）
#   paint＝札に頭がかかっていないときだけ、札をパネルの背景色で塗って、頭の上に余白をとる
#   box＝枠を直接決める（第1話の設定資料の小さい絵）
# 使い方：python3 tools/faces_all.py  （確かめ用の一覧を /tmp/faces_all.png に書く）
from PIL import Image, ImageDraw

R = 'docs/ref/'
F = {
 # 第1話の顔グラ
 'messenger': dict(s='empire-01-faces', ht=118, ch=415, cx=215, w=275, lim=162, px=(15, 500)),
 'villager':  dict(s='empire-01-faces', ht=125, ch=385, cx=730, w=315, lim=162, px=(520, 1005)),
 'elder':     dict(s='empire-01-faces', ht=160, ch=395, cx=1265, w=270, lim=162, px=(1025, 1515)),
 # 第1話の設定資料（小さい絵。パネルいっぱいに切る）
 'ernst':   dict(s='empire-01-sheet', box=(444, 155, 556, 267)),
 'bruno':   dict(s='empire-01-sheet', box=(964, 165, 1060, 261), paint=(956, 158, 1005, 177)),
 'otto':    dict(s='empire-01-sheet', box=(964, 295, 1060, 391), paint=(956, 290, 1001, 309)),
 'mattias': dict(s='empire-01-sheet', box=(1390, 133, 1503, 246)),
 'kasper':  dict(s='empire-01-sheet', box=(1197, 632, 1333, 768)),
 'clara':   dict(s='empire-01-sheet', box=(1354, 637, 1482, 765)),
 'boltz':   dict(s='empire-01-sheet', box=(855, 643, 970, 758)),
 # 第2話
 'leo':   dict(s='empire-02-faces', ht=145, ch=395, cx=240, w=280, lim=167, px=(20, 500)),
 'gert':  dict(s='empire-02-faces', ht=150, ch=430, cx=740, w=300, lim=167, px=(525, 1005)),
 'penal': dict(s='empire-02-faces', ht=150, ch=455, cx=1270, w=260, lim=167, px=(1030, 1515)),
 # 第3話
 'baron':    dict(s='empire-03-faces', ht=170, ch=380, cx=200, w=260, lim=168, px=(20, 380)),
 'dietrich': dict(s='empire-03-faces', ht=165, ch=305, cx=565, w=190, lim=168, px=(400, 755)),
 'johann':   dict(s='empire-03-faces', ht=150, ch=330, cx=935, w=195, lim=168, px=(780, 1135)),
 'peasant':  dict(s='empire-03-faces', ht=150, ch=365, cx=1300, w=215, lim=168, px=(1155, 1515)),
 # 第4話
 'nina':   dict(s='empire-04-faces', ht=110, ch=405, cx=390, w=350, lim=112, px=(24, 746), paint=(18, 100, 242, 174)),
 'supply': dict(s='empire-04-faces', ht=120, ch=345, cx=1140, w=280, lim=112, px=(784, 1511), paint=(778, 100, 997, 174)),
 # 第5話
 'wolf': dict(s='empire-05-faces', ht=145, ch=545, cx=500, w=405, lim=144, px=(30, 995), paint=(22, 130, 358, 228)),
 # 第6話
 'emperor':  dict(s='empire-06-faces-a', ht=130, ch=335, cx=200, w=270, lim=100, px=(20, 375), paint=(18, 98, 177, 167)),
 'marianne': dict(s='empire-06-faces-a', ht=160, ch=345, cx=565, w=225, lim=100, px=(400, 755), paint=(398, 98, 637, 167)),
 'lidia':    dict(s='empire-06-faces-a', ht=165, ch=335, cx=965, w=230, lim=100, px=(785, 1135), paint=(783, 98, 992, 167)),
 'werner':   dict(s='empire-06-faces-a', ht=145, ch=345, cx=1340, w=200, lim=166, px=(1160, 1515)),
 'felix':    dict(s='empire-06-faces-b', ht=170, ch=340, cx=200, w=275, lim=105, px=(20, 375), paint=(18, 103, 267, 171)),
 'guard':    dict(s='empire-06-faces-b', ht=165, ch=345, cx=570, w=210, lim=168, px=(400, 755)),
 'assassin': dict(s='empire-06-faces-b', ht=150, ch=360, cx=920, w=250, lim=168, px=(785, 1135)),
 'zarg':     dict(s='empire-06-faces-b', ht=150, ch=385, cx=1330, w=270, lim=168, px=(1160, 1515)),
 # 第7話
 'stahl':    dict(s='empire-07-faces', ht=145, ch=325, cx=265, w=210, lim=168, px=(20, 500)),
 'julius':   dict(s='empire-07-faces', ht=135, ch=380, cx=760, w=265, lim=168, px=(525, 1005)),
 'berthold': dict(s='empire-07-faces', ht=165, ch=360, cx=1265, w=250, lim=105, px=(1030, 1515), paint=(1028, 103, 1292, 170)),
 # 第8話（名前の札はパネルの下）
 'mb_captain':     dict(s='empire-08-faces', ht=125, ch=345, cx=200, w=260, lim=112, px=(20, 375)),
 'elsa':           dict(s='empire-08-faces', ht=135, ch=400, cx=590, w=280, lim=114, px=(404, 751)),
 'hans':           dict(s='empire-08-faces', ht=125, ch=435, cx=960, w=285, lim=125, px=(780, 1135)),
 'comrade_mother': dict(s='empire-08-faces', ht=150, ch=365, cx=1335, w=300, lim=112, px=(1160, 1515)),
}

def box_of(p):
    if 'box' in p: return p['box']
    S = max((p['ch'] - p['ht']) / 0.70, p['w'] / 0.80)
    x0, x1 = p['px']; S = min(S, x1 - x0)
    top = max(p['lim'], p['ht'] - 0.05 * S)
    left = min(max(p['cx'] - S / 2, x0), x1 - S)
    return tuple(round(v) for v in (left, top, left + S, top + S))

sheets = {}
def sheet(n):
    if n not in sheets: sheets[n] = Image.open(R + n + '.png').convert('RGB')
    return sheets[n]

# 前の切り抜きのままにする人（ユーザーの希望）。ここに書いた人はこのスクリプトで書き換えない（F の枠は参考に残す）
KEEP = {'bruno', 'otto', 'lidia', 'marianne', 'emperor', 'felix', 'guard', 'stahl'}

if __name__ == '__main__':
    out = []
    for n, p in F.items():
        if n in KEEP:
            out.append((n, Image.open(f'assets/faces/{n}.png').convert('RGB'))); continue
        im = sheet(p['s'])
        if 'paint' in p:  # 札だけをパネルの背景色で塗る（この人の頭にはかかっていない）
            im = im.copy(); L, T, Rr, B = p['paint']
            ImageDraw.Draw(im).rectangle(p['paint'], fill=im.getpixel((L + 10, B + 8)))  # 札の左下のすぐ下＝パネルの背景
        b = box_of(p)
        c = im.crop(b).resize((128, 128), Image.LANCZOS)
        c.save(f'assets/faces/{n}.png'); out.append((n, c)); print(n, b, b[2] - b[0])
    cols = 8; W = Image.new('RGB', (cols * 140, ((len(out) + cols - 1) // cols) * 150), '#333'); d = ImageDraw.Draw(W)
    for i, (n, c) in enumerate(out):
        x, y = (i % cols) * 140 + 6, (i // cols) * 150 + 4; W.paste(c, (x, y)); d.text((x, y + 130), n, fill='white')
    W.save('/tmp/faces_all.png')
