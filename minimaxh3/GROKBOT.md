# Grokbot：H3 I2V 完全再現

スマホでセルを押す必要はない。動画エージェントが inbox に置き、Grokbot が Imagine 2.0 → Colab A100 → mp4 → ランタイム停止までやる。

詳しい手順は `.cursor/skills/h3-i2v-grokbot/SKILL.md`。

## いちどだけ

1. Colab Pro（A100）
2. Linux / macOS / WSL / Cursor Cloud（Windows の `colab` CLI は非対応）
3. `pip install google-colab-cli` のあと、一度 `colab new` で Google ログイン
4. シェルに `XAI_API_KEY`（Git 禁止）
5. Google Drive に `minimax-h3-comfyui`（モデルは初回だけ約42GB）

## 毎回

```bash
# 動画エージェント
python minimaxh3/grokbot/drop_job.py --image draft.jpg --slug coconala

# Grokbot
python minimaxh3/grokbot/run_i2v.py --drive "$H3_DRIVE_ROOT"
```

完成: `minimax-h3-comfyui/output/{id}.mp4`

投稿は人間。リンクはプロフィール。画面上は「広告」。
