# 機甲戦線グランヴァルド

スパロボ風のターン制SRPG（オリジナル作品）。現状は `index.html` 1ファイルで完結。ビルド不要、ブラウザで直接開けば動く。

## 方針
- 既存ゲームのROM・画像・音楽・セリフ・キャラクター・ロボットは使わない。参考にするのはゲームシステム（気力、精神コマンド、地形効果など）だけ。
- 機体はすべて Canvas の図形で描く（`drawMech`）。外部画像なし。
- スマホ縦画面が基準（幅400px前後）。

## コード構成（index.html の <script> 内、上から順）
| セクション | 内容 |
|---|---|
| DATA | `MAP`（10×12の地形文字列）、`TER`（地形：移動コスト c / 防御 d / 回避 e）、`SPIRITS`（精神コマンド）、`TPL`（機体・パイロット・武器テンプレート。武器は `W()` で定義） |
| STATE | グローバル状態。`mode` は title / idle / peek / select / moving / menu / target / busy |
| RULES | `hitRate` / `baseDmg` / `critRate` / `strike`（1回の攻撃を解決し、記録を返す） |
| MOVEMENT | `computeReach`（ダイクストラ法で移動範囲を求める）、`animateMove` |
| MECH DRAWING | `drawMech(ctx, unit, t)`：単位座標（-1〜1）で描画。kind は super / real / tank / jet / drone / heavy / wasp / boss |
| MAP RENDER | 地形はオフスクリーンにキャッシュし、`drawMap` を毎フレーム実行 |
| UI | 下部コンソール（`renderConsole`）、ボトムシート（武器・精神・予測・設定）、`dialog()`、`banner()` |
| COMBAT | `combat()`（攻撃 → 反撃 → 戦闘アニメ → 撃墜処理 → `checkEnd`） |
| BATTLE SCENE | `playBattle`：canvas で戦闘演出。敵が左、味方が右 |
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
