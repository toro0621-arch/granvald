# 第8話の会話の背景の手直し。元の絵は docs/ref/ にそのまま残し、直したものを assets/bg/ に書く
#  - 運河沿いの倉庫（夜）：台本は「新月の夜」なので、空の三日月を消す（まわりの夜空で埋める）
#  - 夜明けの版：夜の絵を明るくして、東の空に朝の色を足す（夜明けの絵は描いていない）
#  - 近衛の詰所：机の地図の隅の英語の文字（IMPERIAL CAPITAL CAPITAL）を消す
#  - 下町：そのまま
import cv2
import numpy as np
from PIL import Image

def inpaint(img, mask, r=6):
    return cv2.inpaint(img, mask, r, cv2.INPAINT_TELEA)

# 運河（夜）
a = cv2.imread('docs/ref/bg-canal-night.jpg')
m = np.zeros(a.shape[:2], np.uint8)
cv2.ellipse(m, (428, 80), (24, 26), 0, 0, 360, 255, -1)
a = inpaint(a, m, 9)
# 月のまわりのぼんやりした光も消す：空の上のほうの色を、まわりのなめらかな色にならす
sky = a[:300].astype(float)
sm = cv2.GaussianBlur(sky, (0, 0), 40)
ring = np.zeros(sky.shape[:2]); cv2.circle(ring, (428, 80), 75, 1, -1); ring = cv2.GaussianBlur(ring, (0, 0), 18)[..., None]
base = cv2.GaussianBlur(sky, (0, 0), 90)
sky = sky - (sm - base) * ring
a[:300] = np.clip(sky, 0, 255).astype(np.uint8)
cv2.imwrite('assets/bg/canal.jpg', a, [cv2.IMWRITE_JPEG_QUALITY, 85])
# 夜明け：全体を明るく暖かく、空の下のほうを朝焼けの色に
f = a.astype(float) / 255
h = f.shape[0]
f = np.clip(f * 1.6 + 0.05, 0, 1)
# 空（城壁より上）を、上は薄い青、地平線のあたりはだいだい色のグラデーションに寄せる
y = np.arange(h)[:, None, None] / h
top = np.array([0.80, 0.62, 0.45]); hor = np.array([0.45, 0.70, 1.0])  # BGR
grad = top + (hor - top) * np.clip((y - 0.02) / 0.28, 0, 1)
skyw = np.clip(1 - (y - 0.26) / 0.06, 0, 1) * np.clip(f.mean(2, keepdims=True) * 0 + 1, 0, 1)
# 空らしい暗く平らなところだけ塗る（建物の線は残す）
af = a.astype(float)
flat = ((af[..., 0] - af[..., 2] > 14) & (af.mean(2) < 135)).astype(np.float32); flat = cv2.morphologyEx(flat, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))  # 青みが強く暗い＝夜空（建物の壁は残す）
flat = cv2.GaussianBlur(cv2.morphologyEx(flat, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)), (0, 0), 2)[..., None]
f = f * (1 - 0.75 * skyw * flat) + grad * 0.75 * skyw * flat
f = f * np.array([0.93, 0.98, 1.06])
cv2.imwrite('assets/bg/canal_dawn.jpg', (np.clip(f, 0, 1) * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 85])

# 近衛の詰所：地図の隅の文字を消す（枠の中の暗い線＝文字だけを埋める）
b = cv2.imread('docs/ref/bg-konoe.jpg')
x0, y0, x1, y1 = 553, 996, 636, 1036
reg = b[y0:y1, x0:x1]
dark = (reg.mean(2) < 120).astype(np.uint8) * 255
m = np.zeros(b.shape[:2], np.uint8)
m[y0:y1, x0:x1] = cv2.dilate(dark, np.ones((3, 3), np.uint8))
b = inpaint(b, m, 4)
cv2.imwrite('assets/bg/konoe.jpg', b, [cv2.IMWRITE_JPEG_QUALITY, 85])

# 下町
Image.open('docs/ref/bg-slum.jpg').convert('RGB').save('assets/bg/slum.jpg', quality=85)
