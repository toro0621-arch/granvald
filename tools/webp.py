"""ゲームで使う絵（assets/ の png・jpg）から、軽い WebP を作る。ゲームは WebP を読み、読めなければ元の絵を読む。
絵を作り直したら（切り抜き・マップ・背景など）、最後にこれを実行する：python3 tools/webp.py
元の png・jpg も残す（ツールの出力と、WebP が読めないブラウザのため）。新しい絵の WebP だけ作り直す（--all で全部）。
"""
import glob, os, sys
from PIL import Image

ALL = '--all' in sys.argv
files = (glob.glob('assets/sprites/*.png') + glob.glob('assets/faces/*.png') + glob.glob('assets/bg/*.jpg')
         + glob.glob('assets/*.png') + glob.glob('assets/*.jpg'))
before = after = 0
for f in sorted(files):
    out = os.path.splitext(f)[0] + '.webp'
    before += os.path.getsize(f)
    if ALL or not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(f):
        im = Image.open(f)
        if f.endswith('.png'):
            im = im.convert('RGBA') if im.mode in ('RGBA', 'LA', 'P') else im.convert('RGB')
            # 透明な部分のふちが汚れないよう、透明度は劣化させない（alpha_quality=100）
            im.save(out, 'WEBP', quality=90, alpha_quality=100, method=6)
        else:
            im.convert('RGB').save(out, 'WEBP', quality=85, method=6)
    after += os.path.getsize(out)
print(f'{len(files)} files  {before/1e6:.1f}MB -> {after/1e6:.1f}MB')
