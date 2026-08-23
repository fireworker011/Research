---
name: genre-video-agents
description: Grok Botに作るジャンル動画エージェント9体。「これだけ読んで」でそのジャンルの動画パケットを生成する。投稿はしない。
---

# ジャンル動画エージェント

Grok Bot に今作るのは `affiliate-engine/docs/grok-bots/CREATE.md` の9体。
各体の本文は `affiliate-engine/docs/grok-bots/agents/`。データ源は `affiliate-engine/data/genre_video_packets.json`。

人間が「これだけ読んで」と言ったら、そのファイルだけを読む。他ジャンルを開かない。

## 生成

```bash
cd affiliate-engine
node src/genre-video-gen.js --self-test
node src/genre-video-gen.js --genre ペット
node src/genre-video-gen.js --genre ペット --id pet_20260801_02 --write
```

レシピ追加後は `node src/genre-video-gen.js --write-agents` でエージェントファイルを再生成する。
型は `data/video_kata.json` の6つだけ。新造するな。

## やってはいけない

- 投稿する
- リンクキーごとにボットを増やす
- 実験中のペットで after_experiment レシピを出す
- 数字を発明する
- URL を説明文に書く
