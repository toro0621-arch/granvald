# 機甲戦線グランヴァルド

スパロボ風のターン制SRPG（オリジナル作品）。現状は `index.html` 1ファイル＋BGM（`assets/bgm/`）。ビルド不要、ブラウザで直接開けば動く。

## 方針
- 既存ゲームのROM・画像・音楽・セリフ・キャラクター・ロボットは使わない。参考にするのはゲームシステム（気力、精神コマンド、地形効果など）だけ。
- 機体と地形の見た目は、ユーザーが用意した画像（`assets/sprites/`）を使う。画像の元は `docs/ref/` の設定画で、設定画どおりの見た目にすることが目標。
  - 設定画から切り抜くときは、背景・ラベル文字・枠線を取り除き、背景が透明なPNGにする。
  - 画像が読み込めないときだけ、Canvas の図形（`drawMech`）で代わりに描く。
  - 切り抜きは `python3 tools/extract_sprites.py`（切り抜く範囲はスクリプト内の `UNITS` / `TILES`）。機体は `grand.png`（戦闘用の大きい絵）、`grand_up/down/left/right.png`（背面／正面／左／右）、味方は `_idle/_walk/_attack`（待機／歩行／攻撃）、地形は `tile_*.png`（立体タイル）。
  - マップ背景 `assets/stage1_map.png` は `python3 tools/build_map.py` で作る（`MAP` を読み、設定画のマップから森・山・市街・城・基地を貼り、海と平地は設定画の色で生成）。`MAP` を変えたら作り直す。
- 機体デザインは既存作品に似せない。特に、頭部の V字アンテナや、ガンダム風の「二つ目＋マスク状の口元」の顔は使わない。グランヴァルドは一本角とバイザー型の目、シルフィードは後ろへ流れる耳型センサーとゴーグル型の目、カイザー・ネメシスは王冠状の角、を基本形にする。
- スマホ縦画面が基準（幅400px前後）。
- localStorage のキーは必ず `granvald-` で始める（GitHub Pages では toro0621-arch.github.io の他のページと保存領域を共有するため）。設定は `granvald-settings`、セーブデータは `granvald-save-*`。セーブデータの形式を変えたら `SAVE_VER` を上げる。
- BGMはユーザーが用意したフリー素材（`assets/bgm/`、クレジットは README）。2曲とも −16 LUFS に音量をそろえて 128kbps で再エンコード済み。曲を足すときも同じようにそろえる（iOS ではページ側の音量変更が効かないため）。
- 機体・地形のデザインと数値の元は `docs/ref/` の設定画。内容は `SETTING.md` にまとめてある。

## コード構成（index.html の <script> 内、上から順）
| セクション | 内容 |
|---|---|
| DATA | `MAP`（10×12の地形文字列）、`ROAD`（見た目だけの道路）、`TER`（地形：移動コスト c / 防御 d / 回避 e）、`SPIRITS`（精神コマンド）、`TPL`（機体・パイロット・武器テンプレート。武器は `W()` で定義） |
| STATE | グローバル状態。`mode` は title / idle / peek / select / moving / menu / target / busy |
| RULES | `hitRate` / `baseDmg` / `critRate` / `strike`（1回の攻撃を解決し、記録を返す） |
| MOVEMENT | `computeReach`（ダイクストラ法で移動範囲を求める）、`animateMove` |
| MECH DRAWING | `drawMech(ctx, unit, t)`：画像が読めないときの代わり。単位座標（-1〜1）で描画。kind は super / real / tank / jet / drone / heavy / wasp / boss |
| MAP RENDER | `SPR`（機体画像）、`TER_IMG`（地形タイル）、`STAGE_IMG`（マップ背景）を読み込む。`resize` で空いた高さに合わせてマス目の大きさを決める。地形はオフスクリーンにキャッシュし、`drawMap` を毎フレーム実行。ユニットは `u.dir`（up/down/left/right）の向きの絵で描く |
| BGM | `bgm('player' / 'enemy' / null)` でフェイズごとに曲を切り替え（フェードあり、曲の続きから再開）。音量は設定の `bgmVol`（OFF／小／中／大） |
| UI | 1画面に収まるレイアウト（スクロールなし）。下部コンソール（`renderConsole`、高さ固定）、移動後のコマンドはユニット横のポップアップ（`renderPop`）。敵をタップすると届くマスへ移動して戦闘予測（`attackFromSelect`）。ボトムシート（精神・予測（武器を切り替え）・設定）、`dialog()`、`banner()` |
| COMBAT | `combat()`（攻撃 → 反撃 → 戦闘アニメ → 撃墜処理 → `checkEnd`） |
| BATTLE SCENE | `playBattle`：canvas で戦闘演出。敵が左、味方が右。機体は大きい絵、足元にそのマスの地形タイル |
| SAVE / LOAD | localStorage の `granvald-save-1〜3`（手動）と `granvald-save-auto`（味方フェイズ開始時に `autoSave`）。`snapshot` で保存、`validSave` で中身を検査（`SAVE_VER` が違う・値がおかしい・JSONが壊れている → 壊れたデータ）、`restore` で `setup` 後に `ROSTER` の順で上書き。読み書きは `storeGet/storeSet/storeDel`（try/catch）。セーブできるのは `canSave()`（味方フェイズで誰も選んでいないとき）だけ。上書き・削除・ゲーム中のロードは `confirmSheet` で確認 |
| TURN FLOW | `endPlayerPhase`、`enemyAct`（AI：期待ダメージ＋撃墜ボーナス−反撃リスクで行動を評価）、`startOfPhase` |

## 計算式
- 命中 = 80 + (攻撃側の命中 − 防御側の回避) × 0.5 − (防御側の運動性 − 70) × 0.4 + 武器の命中補正 − 地形の回避補正 + 気力差 × 0.1
- ダメージ = 武器攻撃力 × (格闘 or 射撃 + 気力) / 200 − 装甲 × 0.5 × 防御側の気力 / 100 → 地形補正 → 熱血 ×2 / 鉄壁 ×0.25 / 防御 ×0.5 → 乱数 ±10%
- 気力：命中で攻撃側 +2・防御側 +1、撃墜で +5、回避で +1。上限 150
- 毎ターン：SP +5、EN +5。基地にいる場合は HP と EN が 10% 回復

## 今後の候補
- 第2話以降のステージ（MAP・配置・会話をステージデータとして切り出す）
- パイロットのレベルと経験値、機体改造、インターミッション画面
- 援護攻撃・援護防御、地形適応（A/B/C）、増援イベント
- ファイルが大きくなったら `src/` に分割し、Vite でビルドする
