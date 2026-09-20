# 病棟出口（`hospital-exit-adult`）

霞東アダルトとは**別スラッグ**。同じ枝。③ / Qwen には足さない。
霞東の執務室スチールはここにコピーしない。
パンデミックで感染者だらけの架空病院から出る予告。敵は全裸の成人女性かふたなり。血は出ない。
ルートは ベロチュー回避 → 打倒じゅぼ → 正常位のまま出口。最後は**ミッション完了**（犯されながら脱出）。

バトルは参考クリップ約12秒の半分（trim 5秒）。カメラは引き、全身、水平トラック。
UNet は erotic + eros-max。Combat は 06 と 10 だけ。

理想台本は `SCRIPT.md`。問題は `PREP.md`。

## ワンクリック

1. このブランチが GitHub にあること。inbox には置かない。
2. Colab の `EPISODE = "hospital-exit-adult"`。`BRANCH = "cursor/h3-kasumi-adult-0402"`。霞東本体に戻すな。
3. Drive は `episodes/hospital-exit-adult/` と `models/erotic/` だけ。スチールは上書きしない。

```bash
cd minimaxh3
python h3_episode.py check   episodes/hospital-exit-adult
python h3_episode.py stills  episodes/hospital-exit-adult --out /tmp/ep/hospital-exit-adult
```
