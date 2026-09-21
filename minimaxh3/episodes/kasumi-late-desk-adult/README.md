# 霞東フロア あさ（`kasumi-late-desk-adult`）

霞東リライトの**別スラッグ**。本体 `kasumi-late-desk` は触らない。
既存エロ動画（③ / STORY / Qwen）とも**別チャット**。続きは `HANDOVER.md`。
オフ約 55 秒・オン約 48 秒。Colab 4 番で話が分かれる。オフ=じゅぼ口内口移し（なな座位フェード）・後ろから接合中出し（青木完全フェード）・挿入開始から仰向けのまま腰（戦いなし）。オン=横スク戦い＋じゅぼ＋仰向け接合。失敗は「正常位で動けない」。
セックスは体位名ではなく、動く側を体位に合わせて書く（病棟と同じ）。
バトルは参考約12秒の半分（5秒）。GPU は T2V。カメラ既定は横スク `side2d`（`action3d` に切替可）。**冒頭から真横 PROFILE。床は左→右。** プリセット既定は `balance`。Combat は 06 と 10 だけ。
UNet は Eros Max。本体は stock。

理想台本は `SCRIPT.md`。問題と対策は `PREP.md`。引き継ぎは `HANDOVER.md`。

## ワンクリック

1. このブランチが GitHub にあること。inbox には置かない。
2. Colab ノートの話は「霞東フロア あさ（迷ったらこれ）」（スラッグ `kasumi-late-desk-adult`）。`BRANCH = "cursor/h3-kasumi-adult-0402"`。Run all。
3. Drive は `episodes/kasumi-late-desk-adult/` だけ。スチールは上書きしない。霞東の 5カット raw は reuse するな。

```bash
cd minimaxh3
python h3_episode.py check   episodes/kasumi-late-desk-adult
python h3_episode.py stills  episodes/kasumi-late-desk-adult --out /tmp/ep/kasumi-late-desk-adult
```
