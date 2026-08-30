---
name: h3-i2v-grokbot
description: Unattended MiniMax H3 I2VA: Drive inbox, Grok Imagine 2.0, Colab CLI start, download mp4, stop runtime. Use when Grokbot should generate the homage video or another agent drops a job.
---

# H3 I2VA Grokbot

完全再現は **I2VA**（1枚→10秒）。R2V でも Hailuo Max でもない。アフィURLはプロンプトにも Git にも入れない。

## 役割

| 誰 | やること |
|---|---|
| 動画エージェント | `drop_job.py` で inbox に下書き画像 + job.json |
| Grokbot | Imagine 2.0 で画質上げ → Colab A100 起動 → 生成 → mp4 取得 → ランタイム停止 |
| 人間 | Shorts 投稿。リンクはプロフィール。Grokbot は投稿しない |

## Drive（固定）

`MyDrive/minimax-h3-comfyui/`

```
inbox/     動画エージェントが置く（status=ready）
queued/    Imagine 済み（status=queued）
running/   Colab 実行中
done/      完了。output/{id}.mp4
failed/
input/     Comfy 用 Picture 1
output/    完成 mp4
```

環境変数 `H3_DRIVE_ROOT` で上書き。キーは `XAI_API_KEY` のみ。ファイルに書かない。

## Grokbot 手順（毎回これだけ）

1. この skill を読む。アフィURLを探さない。
2. Drive の `inbox/*/job.json` で `status=ready` を1件取る。無ければ終了。
3. Linux/macOS（Cursor Cloud 可）。Windows では Colab CLI は動かない → WSL か Cloud。
4. `pip install google-colab-cli` 済みで、一度 `colab new` してログインできること。
5. 実行:

```bash
export H3_DRIVE_ROOT="$HOME/Google Drive/minimax-h3-comfyui"
export XAI_API_KEY="…"
python minimaxh3/grokbot/run_i2v.py --drive "$H3_DRIVE_ROOT"
```

6. mp4 は `done/{id}/` と `output/{id}.mp4`。ローカルにもコピーされる。
7. スクリプトが `colab stop` する。失敗したら `colab stop -s h3-i2v`。
8. 投稿しない。

Drive がローカルに無い（Cloud + MCP だけ）とき:

1. Drive MCP で inbox の `job.json` と `source.jpg` をワークスペースへ落とす
2. `--drive` をそのローカルミラーにする
3. 生成後の `picture1.jpg` / `job.json` / mp4 を同じ Drive フォルダへ戻す
4. Colab の `colab drivemount` は `MyDrive/minimax-h3-comfyui` を見る。本番ファイルは必ずそのパスへ置く

## 動画エージェントが置くもの

```bash
python minimaxh3/grokbot/drop_job.py --image /path/to/draft.jpg --slug coconala
```

`prompt` を空にすると公式 10-shot（パーカー・ココナラ・広告）が使われる。独自プロンプトは `validate_motion_ad_prompt` を通す。`稼げる` / `px.a8.net` は拒否。

下書き画像は Imagine 2.0 が品質を上げる。人物・パーカー・デスクを変える指示を Imagine プロンプトに書かない。

## やってはいけないこと

- セル1〜10の完全版ノートを無人実行する（Drive 許可ダイアログで止まる）
- loca.lt / Comfy UI を開く
- R2V・Wan・H3 Max
- ランタイムを付けっぱなし（`--keep-runtime` はデバッグだけ）
- 元デモ動画の R2V
- Threads / Shorts への自動投稿

## テスト

```bash
python3 -m pytest colab/test_h3_i2v_job.py colab/test_h3_i2v_phone.py colab/test_h3_motion_graphics.py -q
```
