# 一度だけ。以降は inbox に画像を置くだけ。

Naomi が Grokbot に話しかけるのは初回の Automation 登録（または `--watch` 起動）だけ。
ジョブが来るたびに指示しない。

デフォルトは **fal MiniMax H3 Max API**（数秒、A100 不要）。
https://fal.ai/tools/minimax-h3-max のログインなしページは手試し専用（1日5本・5秒）。
オマージュは 10 秒なので無人実行は公式 API だけ。HTML を叩くな。

## 初回（人間が1回）

1. シェルに `FAL_KEY` と `XAI_API_KEY`（どちらも Git 禁止）
2. Cursor → Automations → 新規。スケジュール **15分ごと**。プロンプトは下をそのまま。

```
skill h3-i2v-grokbot を読む。
inbox を1件だけ処理して終了する（空なら idle で終わる。待たない。質問しない）。
python minimaxh3/grokbot/run_i2v.py
投稿するな。R2V/Wan/Hailuo/10Eros/完全版ノート/loca.lt は使うな。
空のときは「idle」とだけ書いて終わる。
```

常時PCがあるなら Automation の代わりにこれでもよい（これも一度だけ）:

```bash
python minimaxh3/grokbot/run_i2v.py --watch
```

Colab Comfy I2VA に戻すときだけ:

```bash
python minimaxh3/grokbot/run_i2v.py --backend colab
```

（その場合は Colab Pro + `google-colab-cli`。終わったらスクリプトが `colab stop` する）

## 以降（全自動）

動画エージェントは Drive の `minimax-h3-comfyui/inbox/` に **jpg を置くだけ**。
job.json は無くてよい。監視がフォルダを作る。

完成: `minimax-h3-comfyui/output/{id}.mp4`

投稿は人間。リンクはプロフィール。
