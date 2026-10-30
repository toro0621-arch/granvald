# granvald

機甲戦線グランヴァルド — スパロボ風のターン制SRPG。`index.html` をブラウザで開けば遊べます。

## クレジット
BGM はすべて OpenTracks（旧 DOVA-SYNDROME、https://opentracks.com/ ）のフリー素材です。
- タイトル〜物語の場面：「作戦会議２」 Tomoki — `assets/bgm/story.dat`
- 村が襲われている場面：「戦闘準備」 — `assets/bgm/crisis.dat`
- 味方フェイズ：「Sword in the Void」 — `assets/bgm/player.dat`
- 敵フェイズ：「Deckrail」 — `assets/bgm/enemy.dat`
- 第5話、ディートリヒの最期：（曲名を確認中） — `assets/bgm/farewell.dat`
- 第5話、戦闘後の野営地から最後まで：「Radix」 — `assets/bgm/radix.dat`
- 第6話、宮殿の大広間の場面：「山岳を目指して」 — `assets/bgm/palace.dat`
- リディアたちの場面（第6話の後宮の庭）：「ロバンチェ」 — `assets/bgm/lidia.dat`

どれも音量をそろえるために再エンコードしています。
OpenTracks の規約で「音源ファイルを容易にアクセス・複製できる状態での利用」が禁止されているため、mp3 はそのまま置かず、`tools/pack_bgm.py` で変換した `.dat` を置いてゲーム内で元に戻して再生しています（ローカルで `index.html` を直接開いた場合は BGM が鳴りません。ローカルで鳴らすときは `python3 -m http.server` などで開いてください）。

## ライセンス

種類によって分かれています（詳しくは [LICENSE](LICENSE)）。
- プログラム（`index.html` のコード、`tools/`）：MIT License
- 画像・設定・ストーリー・キャラクター：© toro0621-arch、無断使用・転載禁止
- BGM：OpenTracks の利用規約に従います（上の「クレジット」）
