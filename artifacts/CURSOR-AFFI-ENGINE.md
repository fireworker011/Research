# Cursor に貼る文（H3 Studio）

チャット履歴は正本にしない。先に `artifacts/COLAB-H3-STUDIO.md` を読む。正本はそこにあるファイルと `.cursor/skills/h3-prompt-writing/` だけ。Hub の残り 8 スキルは入れるな。生成は人間。病棟を開くな。`episode.json` / `HANDOFF.md` / 病棟ノート / レイ脱出 / kasumi は触るな。病棟エンジンは改造するな。

## レーン

H3 Studio。病棟の入口を改造せず、別ファイルにする。

- `colab/h3_studio.py` と `minimaxh3/h3_studio.py` は同じ中身
- `colab/h3_studio_colab_main.py`
- `colab/_write_studio_nb.py` が `minimax_h3_studio_bot.ipynb` を書く
- `colab/test_h3_studio.py`
- `python3 -m pytest colab/test_h3_studio.py -q`

`charswap` と `anime2real` は `LORA_FILES` にファイル名だけ登録する。病棟ビートの extra には足さない。`combat` は再登録しない。既存の 1 件は `H3_Combat_V2.safetensors`。

```text
"charswap": "h3_character_swap_pro4500_1000.safetensors"
"anime2real": "Anime2Realsim__H3.safetensors"
```

Weapon / GunFu / Continuity は足さない。orbit の LoRA ファイル名が未確定のうちは登録しない。URL は発明しない。

## ジョブ（1つずつ）

- `combat_motion`: FL2VA + combat 1.0。Turbo 切。High-Mem。トリガーは実ファイルの `prfight2`。決め（finish）は `prfight2, prfin1`。依頼文の `prfight1` はリポジトリに無いので使わない。
- `swap_character`: Ref2VA + charswap 1.0。Video が動き、Picture が全身。Hero シート必須。Turbo 切。
- `swap_face`: 同じ LoRA。Picture は顔と髪だけ。服は Video。
- `swap_outfit`: 同じ LoRA。Picture は服だけ。顔は Video。
- `real`: anime2real 1.0。動画があれば Ref2VA、無ければ同じ絵の FL2VA。
- `orbit360`: FL2VA。同じ絵を首尾。他の LoRA は積まない。
- `two_pass`: A の mp4 を B の Video 1 にする。同じサンプラーに両方の LoRA を積まない。swap のあと real なら A は charswap 1.0、B は anime2real 1.0、B のプロンプトに `LumiReal`。同じサンプラーに重ねるときの 0.5 は拒否する。
- `text_scene`: T2VA。LoRA なし。

`runtime=api` で Combat / Swap / real / two_pass が来たら止める。公式 Hailuo API はこの LoRA を読めない。本体は Comfy High-Mem。Swap は Ref2VA。Combat は FL2VA。同じ UNet に積まない。

## フォーム

Hero / Enemy。髪・色・人種・年齢・身長・体重・服・場所。空欄は Look に書かない。swap のとき Hero シート（絵）は必須。action は英語 1 本。日本語は「」で受け、プロンプトでは `<d>[Japanese] …</d>`。商品名はプロンプトに書かない。YouTube、Marvel、公式CM、オルビス、Furbo があれば止める。年齢の数字が 21 未満なら止める。

既定は 4–5 秒（既定値 5）、768P（`768x1344`）、24fps。Swap と Combat は Turbo を切る。

プロンプトの節は h3-prompt-writing の順だけ。FL2VA / T2VA は `integrated_multimodal_description`、`overall_soundscape`、`non_diegetic_music`。Ref2VA は `subject_definitions`、`summary`、`retention_analysis`、`detailed_description`、`overall_soundscape`、`non_diegetic_music`。空欄と頼んでいない動作で語数を埋めない。

生成ボタンは人間。このレーンはプランとプロンプトまで。Comfy は起動しない。ノートの出力先は Drive の `studio/`。`episodes/` には書かない。
