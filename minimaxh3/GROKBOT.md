# 一度だけ。以降は inbox に画像を置くだけ。

Naomi が Grokbot に話しかけるのは初回の Automation 登録（または `--watch` 起動）だけ。
ジョブが来るたびに指示しない。

**PC が無いときの最善手はスマホ Colab + fal。A100 も 42GB モデルも不要。**

https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_i2v_phone.ipynb

1. 左の鍵に `FAL_KEY`（任意で `XAI_API_KEY`）
2. CPU のまま全セル実行
3. 写真は Drive `minimax-h3-comfyui/input/`（または inbox/）

無料の fal ページ（1日5本・5秒）は使わない。オマージュは 10 秒の公式 API。

## Cursor があるとき（無人）

デフォルトは **fal MiniMax H3 Max API**。

```
skill h3-i2v-grokbot を読む。
inbox を1件だけ処理して終了する（空なら idle で終わる。待たない。質問しない）。
python minimaxh3/grokbot/run_i2v.py
投稿するな。R2V/Wan/Hailuo/10Eros/完全版ノート/loca.lt は使うな。
空のときは「idle」とだけ書いて終わる。
```

Comfy 公式重みに戻すときだけ `--backend colab`（A100 が要る）。
