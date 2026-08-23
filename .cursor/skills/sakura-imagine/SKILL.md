---
name: sakura-imagine
description: sakura_ai_beauty のリールを Grok Imagine で完成させる。パケットを読んで静止画→動画まで出し、投稿しない。
---

# サクラ Imagine

`sakura-ig/GROK_IMAGINE_AGENT.md` が契約。先に読め。企画しない。プロンプトは `sakura-ig/prompts/` 以外を足さない。投稿は **サクラ専属自動投稿** が 21:00 にやる。

## 手順

```bash
cd sakura-ig
node src/validate-packets.js
node src/imagine-run.js --next
# 特定日
node src/imagine-run.js --date 2026-08-24
```

`XAI_API_KEY` が無いときは exit 2 でプロンプトが印字される。それを Imagine UI に貼り、`output/<id>/` に保存する。

## 守ること

- 顔は `character.md` と `data/character-lock.txt`。別人にしない
- 着はパケットの `wardrobe` だけ。水着・制服・別顔を足さない
- オーバーレイは英語短語だけ。日本語は焼かない
- 裸・性行為・未成年は不合格
- 完成物は `still.jpg` `reel.mp4` `caption.txt` `manifest.json`
- キャプションはパケットのまま
- 納品したら サクラ専属自動投稿 に返す。こちらから投稿しない
