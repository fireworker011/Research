# 霞東フロア あさ（`kasumi-late-desk-adult`）

霞東リライトの**別スラッグ**。本体 `kasumi-late-desk` は触らない。
既存エロ動画（③ / STORY / Qwen）とも**別チャット**。続きは `HANDOVER.md`。
約 45 秒。同僚□ベロチュー → 警備△横スク打倒＋じゅぼ口内 → 課長△敗北＋正常位。失敗は「正常位で動けない」。
バトルは参考約12秒の半分（5秒）。GPU は T2V。カメラ既定は横スク `side2d`（`action3d` に切替可）。プリセット既定は `balance`。Combat は 06 と 10 だけ。
UNet は Eros Max。本体は stock。

理想台本は `SCRIPT.md`。問題と対策は `PREP.md`。引き継ぎは `HANDOVER.md`。

## ワンクリック

1. このブランチが GitHub にあること。inbox には置かない。
2. Colab ノートの既定は `EPISODE = "kasumi-late-desk-adult"` / `BRANCH = "cursor/h3-kasumi-adult-0402"`。Run all。
3. Drive は `episodes/kasumi-late-desk-adult/` だけ。スチールは上書きしない。霞東の 5カット raw は reuse するな。

```bash
cd minimaxh3
python h3_episode.py check   episodes/kasumi-late-desk-adult
python h3_episode.py stills  episodes/kasumi-late-desk-adult --out /tmp/ep/kasumi-late-desk-adult
```
