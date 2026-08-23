# サクラIG

ゴールはフォロワー増ではない。**リールが非フォロワーに届き、リンクタップが週15を超え、Fanvueの課金が判定できること。**

## 役割

| 誰 | やること |
|---|---|
| マネージャー（このセッション系） | `prompts/` の根幹だけを書く。型の残棄 |
| **サクラ専属自動投稿** | 毎日 05:00 JST に作成、**06:00 JST に投稿**。プロンプトは書かない |
| 人間 | 初回のバイオとリンク。インサイトの4数字を CSV に書く |

定時と投稿の指示書: `bots/サクラ専属自動投稿.md`  
スキル: `.cursor/skills/sakura-auto-poster/SKILL.md`

## 根幹プロンプト

映像の文はここだけが正本。

- `prompts/CORE.md`
- `prompts/lock.txt` `animate.txt` `negatives.txt`
- `prompts/wardrobe/`
- `prompts/types/`
- 日付の差分だけ `packets/sprint-01.json` の scene

組み立ては `node src/print-packet.js`。ボットはこれを Imagine に渡す。

## ゲート（8/23–9/5）

| ゲート | 数字 |
|---|---|
| 再生 | 1本でも ÷2468 ≥ 10（24,700） |
| 弱い | 14本すべて 2倍未満なら型を変える。本数は維持 |
| 導線 | リンクタップ 週15 |
| 成果 | タップが足りない週は Fanvue を語らない |

## テスト作成（投稿しない）

正本画像を `refs/sakura-face.jpg` に置いてから:

```bash
cd sakura-ig
node src/imagine-run.js --test
```

サクラ専属自動投稿への指示は `bots/TEST_NOW.md`。新しい顔を作らせない。

## 人間が1回だけ

1. `bio.md` をプロフィールに貼る。Fanvueリンクを1本
2. 任意で `refs/sakura-face.jpg`
3. 翌日から再生とタップを `data/reel_log.csv` に書く

## やらないこと

- マネージャーが投稿や cron を自分で回す
- ボットが `prompts/` を書き換える
- 人間を装うDM
- Threadsエンジンへの接続
- 水着・別顔への転換
