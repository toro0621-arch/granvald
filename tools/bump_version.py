"""公開版の版番号を上げる。コミットの前に実行する：python3 tools/bump_version.py
index.html の APP_VER と version.txt を、今の日時（版番号）にそろえる。
ゲームは起動時に version.txt をキャッシュなしで読み、自分の APP_VER と違えば（＝スマホのブラウザが古い index.html を
キャッシュから出していれば）、?v=版番号 を付けたURLで開き直す（GitHub Pages は index.html を最大10分キャッシュさせるため）。
"""
import re, time
v = time.strftime('%Y%m%d%H%M%S')
p = 'index.html'
s = open(p, encoding='utf-8').read()
s, n = re.subn(r"const APP_VER='[^']*';", f"const APP_VER='{v}';", s)
assert n == 1
open(p, 'w', encoding='utf-8').write(s)
open('version.txt', 'w').write(v + '\n')
print(v)
