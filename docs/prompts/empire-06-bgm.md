# 帝国編 第6話「鉄の護送」BGM の指示文（Suno 向け）

戦闘「峠の待ち伏せ」の曲。崖に挟まれた峠で護送車を守る、緊迫した戦い。途中で近衛が駆けつける。
Suno の「Custom」モードで、Style（曲の雰囲気）と Lyrics（曲の組み立て）に分けて入れる。歌なし（Instrumental をオン）。
アーティスト名や既存の作品名は入れない（Suno で弾かれるのと、似せないため）。

ゲームでは曲をくり返し流すので、終わりをフェードアウトさせず、頭につながる形にする。できた曲の切れ目はこちらで整える（−16 LUFS・128kbps にそろえ、`tools/pack_bgm.py` で `.dat` にする）。

---

## 味方フェイズ「峠の待ち伏せ」

### Style
```
orchestral battle theme, tactical RPG, heroic and tense, driving snare and taiko drums, staccato strings ostinato, bold brass melody, minor key with uplifting turns, 150 bpm, medieval fantasy war, mountain pass ambush, protecting a convoy, loopable, no fade out, instrumental
```

### Lyrics
```
[Instrumental]
[Intro: short drum roll and brass hit]
[Main Theme: strings ostinato, brass melody]
[Development: low strings and timpani, rising tension]
[Main Theme: full orchestra, heroic]
[Bridge: horns call, hope breaks through]
[Main Theme reprise]
[Ending: brass hit that leads back to the start, no fade out]
```

## 敵フェイズ「崖の上の影」

### Style
```
dark orchestral battle music, tactical RPG enemy phase, menacing and suspenseful, low brass stabs, pulsing cellos, war drums, dissonant high strings, minor key, 140 bpm, medieval fantasy, ambush from the cliffs, loopable, no fade out, instrumental
```

### Lyrics
```
[Instrumental]
[Intro: low drums and cellos pulse]
[Main Theme: menacing brass stabs over strings]
[Development: dissonant strings, closing in]
[Main Theme: heavier, full drums]
[Ending: sharp brass hit that leads back to the start, no fade out]
```

---

## メモ
- 今のゲームは、味方フェイズ・敵フェイズの曲がすべての話で共通（`bgm('player')` / `bgm('enemy')`）。話ごとに戦闘の曲を変えるには、`STAGES.<id>.music` に player / enemy を足せるようにする（小さな直し）。
- 曲の長さは2〜3分くらいがくり返しに向く。Suno で長くなりすぎたら、こちらで切る。
