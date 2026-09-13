# Grok 用：このエロ動画レーンの GitHub プロンプト

独立 H3 レーン。Naomiichi。質問しない。
版 `h3-20260913-anal-12`。枝 `cursor/h3-anal-stories-f112`。

**全文はこれを開け:** [`h3-lora-studio/dump/G_h3_prompts.txt`](dump/G_h3_prompts.txt)

HQ dump（`G_hq_boot` / `hq-instruct` / `G_hq_admin`）は触るな。Threads の schedule を戻すな。

再生成:

```bash
python h3-lora-studio/scripts/dump_grok_prompts.py --write
python h3-lora-studio/scripts/dump_grok_prompts.py --check
```

## 何が載るか

Colab ③が H3 に渡す文の **GitHub 上の出所**。実行時に `prepare_story_clip` がロックを足す。
ロック定数も GitHub（`colab/h3_lora_studio.py`）にあるので全文ダンプに入れる。
