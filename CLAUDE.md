# 機甲戦線グランヴァルド

スパロボ風のターン制SRPG（オリジナル作品）。現状は `index.html` 1ファイル＋画像（`assets/sprites/`、マップ背景）＋BGM（`assets/bgm/`）。ビルド不要、ブラウザで直接開けば動く。
ステージは2つ：帝国編 第1話「辺境の火」（`e1`）と、沿岸都市連合の「鋼の目覚め」（`s1`）。タイトル画面で選ぶ。

## 方針
- 既存ゲームのROM・画像・音楽・セリフ・キャラクター・ロボットは使わない。参考にするのはゲームシステム（気力、精神コマンド、地形効果など）だけ。
- 機体と地形の見た目は、ユーザーが用意した画像（`assets/sprites/`）を使う。画像の元は `docs/ref/` の設定画で、設定画どおりの見た目にすることが目標。
  - 設定画から切り抜くときは、背景・ラベル文字・枠線を取り除き、背景が透明なPNGにする。
  - 画像が読み込めないときだけ、Canvas の図形（`drawMech`）で代わりに描く。
  - 切り抜きは `python3 tools/extract_sprites.py`（切り抜く範囲はスクリプト内の `UNITS` / `TILES`＝`sprites-and-tiles.png`、`UNITS_E1`＝`empire-01-sprites.png`、`UNITS_ZEKT`＝`zekt-v2-sprites.png`）。機体は `grand.png`（戦闘用の大きい絵）、`grand_up/down/left/right.png`（背面／正面／左／右）、`_idle/_walk/_attack`（待機／歩行／攻撃。グランヴァルドたち4機と、ゼクト・カラドリウス・整備車両・ハウンド・ゴルム改）、地形は `tile_*.png`（立体タイル）。歩行・攻撃は数コマのうち1コマを使い、攻撃エフェクトや足元の影は取り除く。
  - マップ背景はステージごとに `python3 tools/build_map.py <ステージ> <出力先>` で作る（`MAP_<ステージ>` / `ROAD_<ステージ>` を読み、設定画のマップから森・山・市街・城・基地を貼り、海と平地は設定画の色で生成）。`S1 assets/stage1_map.png`、`E1 assets/stage_e1_map.png`。マップを変えたら作り直す。
  - 別の機体の画像を使うときは TPL に `spr:'zekt'` のように書く（中隊と盗賊のゼクト・ゴルム）。`tint` で色を重ねられ、`spr:false` は画像なし（図形で描く）。待機・歩行・攻撃の絵がある機体は `SPR_EXTRA`。
- パイロットの顔グラは `assets/faces/<名前>.png`（128×128）。設定画（`empire-01-sheet.png`・`empire-01-faces.png`・`setting-sheet.png`）の人物画から切り抜いたもの。`FACE`（名前→ファイル名）で引き、戦闘画面・会話・ステータス画面に出す。新しいキャラは設定画から切り抜いて `FACE` に足す。
- マップ上のユニットは向きを変えない。いつも「通常時」（`_idle`）の絵、なければ正面（`_down`）で描く（ユーザーの希望）。
- 機体デザインは既存作品に似せない。特に、頭部の V字アンテナや、ガンダム風の「二つ目＋マスク状の口元」の顔は使わない。グランヴァルドは一本角とバイザー型の目、シルフィードは後ろへ流れる耳型センサーとゴーグル型の目、カイザー・ネメシスは王冠状の角、ゼクトは歩兵の鉄兜のようなつばのある丸い頭と固定式の赤い単眼（単眼をスリットの中で動かす形にしない。紫と黒の配色、裾の広がった脚にしない）、カラドリウスはくちばし状に突き出した額の装甲と後頭部へ流れる白い羽根状のアンテナ3枚（目はくちばしの付け根の金の単眼）、ハウンドは鉄格子で囲んだむき出しの操縦席と作業灯2つ、ゴルム改はゴルムの箱型の頭に額の一本の衝角、を基本形にする。
- スマホ縦画面が基準（幅400px前後）。
- localStorage のキーは必ず `granvald-` で始める（GitHub Pages では toro0621-arch.github.io の他のページと保存領域を共有するため）。設定は `granvald-settings`、セーブデータは `granvald-save-*`。セーブデータの形式を変えたら `SAVE_VER` を上げる。
- BGMはユーザーが用意したフリー素材（`assets/bgm/`、クレジットは README）。2曲とも −16 LUFS に音量をそろえて 128kbps で再エンコード済み。曲を足すときも同じようにそろえる（iOS ではページ側の音量変更が効かないため）。
- 機体・地形のデザインと数値の元は `docs/ref/` の設定画（帝国編第1話は `empire-01-sheet.png`／`-sprites.png`／`-heads.png`）。内容は `SETTING.md` にまとめてある。

## コード構成（index.html の <script> 内、上から順）
| セクション | 内容 |
|---|---|
| DATA | ステージごとの地形 `MAP_S1` / `MAP_E1`（10×12の地形文字列）と `ROAD_S1` / `ROAD_E1`（見た目だけの道路）。今のステージのものが `MAP` / `ROAD` に入る。`TER`（地形：移動コスト c / 防御 d / 回避 e）、`SPIRITS`（精神コマンド）、`TPL`（機体・パイロット・武器テンプレート。武器は `W()` で定義） |
| STATE | グローバル状態。`mode` は title / idle / peek / select / moving / menu / target / busy |
| STAGES | ステージデータ `STAGES.s1` / `STAGES.e1`：地形（map/road/bg）、初期配置（roster）、敗北条件の機体（leader）、会話（pre＝マップに入る前、start＝開始時、talks＝戦闘で1回だけ流れる会話、bossDown／allDown／lose／epilogue＝クリア後）、ボーナス（bonus）。`loadStage(id)` で切り替え、`setup()` で配置。会話イベントの済み・ボーナス達成は `flags` |
| RULES | `hitRate` / `baseDmg` / `critRate` / `strike`（1回の攻撃を解決し、記録を返す） |
| MOVEMENT | `computeReach`（ダイクストラ法で移動範囲を求める）、`animateMove` |
| MECH DRAWING | `drawMech(ctx, unit, t)`：画像が読めないとき・画像がない機体の代わり。単位座標（-1〜1）で描画。kind は super / real / tank / jet / drone / heavy / wasp / boss / knight（カラドリウス）/ truck（整備車両）/ hound（ハウンド） |
| MAP RENDER | `SPR`（機体画像。`spr` / `tint` / `SPR_EXTRA` に対応）、`TER_IMG`（地形タイル）、`STAGE_IMG`（今のステージのマップ背景、`stageImg` で読み込み）を読み込む。`resize` で空いた高さに合わせてマス目の大きさを決める。地形はオフスクリーンにキャッシュし、`drawMap` を毎フレーム実行。ユニットは `u.dir`（up/down/left/right）の向きの絵で描く |
| BGM | `bgm('player' / 'enemy' / null)` でフェイズごとに曲を切り替え（フェードあり、曲の続きから再開）。音量は設定の `bgmVol`（OFF／小／中／大） |
| UI | 1画面に収まるレイアウト（スクロールなし）。下部コンソール（`renderConsole`、高さ固定）、移動後のコマンドはユニット横のポップアップ（`renderPop`）。敵をタップすると届くマスへ移動して戦闘予測（`attackFromSelect`）。ボトムシート（精神・予測（武器を切り替え）・設定）、`dialog(lines, {solid})`（narr＝ナレーション、solid＝マップを隠す）、`banner()` |
| COMBAT | `combat()`（ステージの会話イベント → 攻撃 → 反撃 → 戦闘アニメ → 撃墜処理 → `checkBonus` → `checkEnd`）。`checkEnd` は leader の撃墜で敗北、ボス撃破か敵全滅で勝利（epilogue があればクリア後の会話） |
| BATTLE SCENE | `playBattle`：canvas で戦闘演出。敵が左、味方が右。機体は大きい絵、足元にそのマスの地形タイル |
| SAVE / LOAD | localStorage の `granvald-save-1〜3`（手動）と `granvald-save-auto`（味方フェイズ開始時に `autoSave`）。`snapshot` で保存（ステージ ID と `flags` も）、`validSave` で中身を検査（`SAVE_VER` が違う・値がおかしい・JSONが壊れている → 壊れたデータ）、`restore` で `loadStage` → `setup` 後に roster の順で上書き。読み書きは `storeGet/storeSet/storeDel`（try/catch）。セーブできるのは `canSave()`（味方フェイズで誰も選んでいないとき）だけ。上書き・削除・ゲーム中のロードは `confirmSheet` で確認 |
| TURN FLOW | `endPlayerPhase`、`enemyAct`（AI：期待ダメージ＋撃墜ボーナス−反撃リスクで行動を評価。leader を少し優先して狙う）、`startOfPhase` |
| TITLE / START | `renderStageList`（タイトルのステージ選択）、`startGame(id)`（戦闘前の会話 → マップ → 開始時の会話 → 味方フェイズ）、`toTitle` |

## 計算式
- 命中 = 80 + (攻撃側の命中 − 防御側の回避) × 0.5 − (防御側の運動性 − 70) × 0.4 + 武器の命中補正 − 地形の回避補正 + 気力差 × 0.1
- ダメージ = 武器攻撃力 × (格闘 or 射撃 + 気力) / 200 − 装甲 × 0.5 × 防御側の気力 / 100 → 地形補正 → 熱血 ×2 / 鉄壁 ×0.25 / 防御 ×0.5 → 乱数 ±10%
- 気力：命中で攻撃側 +2・防御側 +1、撃墜で +5、回避で +1。上限 150
- 毎ターン：SP +5、EN +5。基地にいる場合は HP と EN が 10% 回復

## 今後の候補
- 第2話以降のステージ（`STAGES` に追加する）
- パイロットのレベルと経験値、機体改造、インターミッション画面
- 援護攻撃・援護防御、地形適応（A/B/C）、増援イベント
- ファイルが大きくなったら `src/` に分割し、Vite でビルドする
