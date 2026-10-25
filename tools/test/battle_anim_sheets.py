import json, os, sys, glob
from PIL import Image, ImageDraw, ImageFont
D = sys.argv[1]; R = sys.argv[2]
folder = f'{D}/bd_r{R}'
labels = dict(json.load(open(f'{folder}/labels.json')))
try:
    font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 13)
except Exception:
    font = ImageFont.load_default()
rows = []
for n in sorted(labels):
    fs = sorted(glob.glob(f'{folder}/{str(n).zfill(3)}_*.jpg'))
    if not fs: continue
    ims = [Image.open(f) for f in fs]
    tw = 200; th = int(ims[0].height * tw / ims[0].width)
    row = Image.new('RGB', (tw * 7 + 6 * 4, th + 18), (40, 40, 40))
    ImageDraw.Draw(row).text((4, 1), f'{n}: {labels[n]}', fill=(255, 255, 0), font=font)
    for i, im in enumerate(ims[:7]):
        row.paste(im.resize((tw, th)), (i * (tw + 4), 18))
    rows.append(row)
per = 12
for k in range(0, len(rows), per):
    part = rows[k:k + per]
    c = Image.new('RGB', (part[0].width, sum(r.height + 4 for r in part)), (0, 0, 0))
    y = 0
    for r in part:
        c.paste(r, (0, y)); y += r.height + 4
    c.save(f'{D}/bds_r{R}_{k // per:02d}.jpg', quality=80)
print(len(rows), 'rows ->', (len(rows) + per - 1) // per, 'sheets')
