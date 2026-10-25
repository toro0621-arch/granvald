"""BGM を、そのままでは音声ファイルとして再生・複製できない形（.dat）に変換する／元に戻す。

OpenTracks（旧 DOVA-SYNDROME）の利用規約は「エンドユーザーが容易に音源ファイルにアクセス、複製が可能な状態での利用」を禁止している。
このリポジトリは公開で GitHub Pages から配信しているので、mp3 をそのまま置かず、バイト列を鍵で混ぜた .dat を置き、
ゲーム側（index.html の loadBgm）で元に戻して再生する。

使い方:
  python3 tools/pack_bgm.py pack  <入力.mp3> <名前>   → assets/bgm/<名前>.dat を作る
  python3 tools/pack_bgm.py unpack <名前> <出力.mp3>   → .dat から mp3 に戻す（音量調整などの作業用。戻したmp3はコミットしない）
曲を足すときは、先に ffmpeg で −16 LUFS・128kbps にそろえてから pack する（CLAUDE.md 参照）。
"""
import sys

KEY = b'granvald-bgm-2026'


def scramble(data: bytes) -> bytes:
    k = KEY
    return bytes(b ^ k[i % len(k)] ^ ((i * 31 + 7) & 255) for i, b in enumerate(data))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'pack':
        src, name = sys.argv[2], sys.argv[3]
        out = f'assets/bgm/{name}.dat'
        open(out, 'wb').write(scramble(open(src, 'rb').read()))
        print(out)
    elif cmd == 'unpack':
        name, dst = sys.argv[2], sys.argv[3]
        open(dst, 'wb').write(scramble(open(f'assets/bgm/{name}.dat', 'rb').read()))
        print(dst)
