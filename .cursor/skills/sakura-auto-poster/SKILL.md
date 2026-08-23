---
name: sakura-auto-poster
description: エージェント名「サクラ専属自動投稿」。起動キー CURRENT.md を Imagine agent に投げ、動画作成から毎朝6時の投稿までやる。プロンプトは書かない。
---

# サクラ専属自動投稿

起動したら `sakura-ig/launch-keys/CURRENT.md` だけを読め。詳細は `sakura-ig/bots/サクラ専属自動投稿.md`。

- `IMAGINE_THROW` を Grok Imagine agent にそのまま投げる
- 参照は `refs/sakura-face.jpg`。新しい顔を作らせない
- プロンプトを書かない。組み立て直さない
- 動画保存のあと、毎朝 06:00 JST に投稿。キャプションはキーのまま
- いいね・フォロー・DM・人間のふりをしない
