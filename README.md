# granvald

機甲戦線グランヴァルド — スパロボ風のターン制SRPG。`index.html` をブラウザで開けば遊べます。

## クレジット
BGM はすべて OpenTracks（旧 DOVA-SYNDROME、https://opentracks.com/ ）のフリー素材です。
- タイトル〜物語の場面：「作戦会議２」 Tomoki — `assets/bgm/story.dat`
- 村が襲われている場面：（曲名未確認） — `assets/bgm/crisis.dat`
- 味方フェイズ：「Interception」 まんぼう二等兵 — `assets/bgm/player.dat`
- 敵フェイズ：「Deckrail」 — `assets/bgm/enemy.dat`

どれも音量をそろえるために再エンコードしています。
OpenTracks の規約で「音源ファイルを容易にアクセス・複製できる状態での利用」が禁止されているため、mp3 はそのまま置かず、`tools/pack_bgm.py` で変換した `.dat` を置いてゲーム内で元に戻して再生しています（ローカルで `index.html` を直接開いた場合は BGM が鳴りません。ローカルで鳴らすときは `python3 -m http.server` などで開いてください）。
