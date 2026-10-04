# H3 Studio（ノンアダルト。病棟・アダルト LoRA とは別）

このブランチの Colab はノンアダルトだけ。アダルトの LoRA スタジオと病棟ノートは置いていない。生成ノートは `h3-runner/minimax_h3_still.ipynb`。プランは `minimax_h3_studio_bot.ipynb`。

LoRA は1キー1ファイル。スピードは LightX2V の Turbo 8step（強さ 1.0、steps 9、video shift 6）。アクションは `Motion_Repair_V2.safetensors`（0.6）。コンバットは `H3_Combat_V2.safetensors`（格闘は 1.0 で Turbo 切、`prfight2`。fast に足すときは 0.7 でトリガーなし）。キャラスワップは `h3_character_swap_pro4500_1000.safetensors`。`combat_base_v2.safetensors` は別名なので登録しない。

`fast_motion` は最初の絵だけ。`join` は 6 秒と 9 秒を足して 15 秒以上。1本の 15 秒生成はしない。`affi_template` は run01〜03 の既存台本を指す。キャラは Hero、場所は place、シーンは `text_scene`。空欄は Look に出ない。

作成: 2026-09-30

病棟エンジンは改造していない。`episode.json` / `HANDOFF.md` / 病棟ノート / レイ脱出 / kasumi は開いていない。Hub の残り 8 スキルは置いていない。公式スキルは `.cursor/skills/h3-prompt-writing/` だけ（出典コミットは SKILL.md の `d21241f0a4b3acbb34c97dae47fa417b7065e438`）。

## 読んだもの

- `docs/affi-stock/stock.md` と `docs/affi-stock/h3_batch.json`。商品名は動画プロンプトに出さない。768P の 9:16 は 6 秒パートの `768x1344`。
- `.cursor/skills/h3-prompt-writing/SKILL.md`、`references/base-en.txt`、`references/ref-en.txt`。
- 既存 Colab 入口の形: `colab/h3_episode_colab_main.py` と `colab/_write_episode_nb.py`（ブランチ `cursor/h3-fast-fl2va-lora-6dc5`）。中身の病棟ルートは複製していない。
- Combat の実登録: 同じブランチの `LORA_FILES["combat"] = "H3_Combat_V2.safetensors"`。トリガーの実文は同ブランチの `colab/test_h3_episode.py` が固定している `prfight2` と `prfight2, prfin1`。`prfight1` はこのリポジトリに無い。

## 切り（盛り込み過ぎない）

- ジョブは 1 回に 1 つ。`two_pass` だけが A のあとに B を置く。同時オンはしない。
- 公式 Hailuo API は Combat / Swap / real の LoRA を読めない。`runtime=api` でこれら（`two_pass` を含む）が来たら止まる。`text_scene` と `orbit360` は LoRA が無いので api を通す。
- 本体は Comfy High-Mem。High-Mem がオフの Combat / Swap / real は止まる。VRAM の閾値はこのレーンでは測っていないので、数字は置いていない。
- Swap は Ref2VA。格闘の Combat は FL2VA で単体。fast_motion だけがスピード + アクション + コンバット（0.7、トリガーなし）を同じサンプラーに載せる。charswap と anime2real は他と混ぜない。
- 顔 / 衣装 / 全身はファイル `h3_character_swap_pro4500_1000.safetensors` の 1 本。プロンプトのロックだけが違う。
- 空欄の髪・色・人種・年齢・身長・体重・服・場所は Look に書かない。
- real 単体は `Anime2Realsim__H3.safetensors` 強さ 1.0。動画があれば Ref2VA、無ければ同じ絵を首尾にした FL2VA。
- swap のあとに real を掛けるときは `two_pass`。A は charswap 1.0、B は anime2real 1.0、B の Video 1 は A の mp4、B のプロンプトに `LumiReal`。同じサンプラーに重ねるときの charswap 0.5 は使わない（その指定はエラー文に残す）。
- orbit360 は FL2VA。同じ絵を首尾。LoRA ファイル名は未確定なので登録しない。
- Weapon / GunFu / Continuity は登録しない。
- Combat は再登録しない。キー `combat` は既存ファイル名のまま 1 つ。
- charswap と anime2real は `LORA_FILES` にファイル名だけ。URL は置かない。病棟ビートの extra には足さない。
- fast_motion だけ steps 9 と video shift 6 をプランに書く。4–5 秒のジョブに 12 step は書かない。
- 生成ボタンは人間。ノートも `h3_studio_colab_main.py` も Comfy を起動しない。`H3_STUDIO_GENERATE=1` は止まる。
- 負のプロンプト欄は無い。除外は本文の「画面に文字を出さない」文。
- 公式ガイドの 350–500 語には合わせない。頼んでいない動作や空欄を埋めて語数を稼がない。

## ジョブ

| ジョブ | タスク | LoRA | ロック |
|---|---|---|---|
| `fast_motion` | FL2VA（最初の絵） | speed 1.0。任意で action 0.6 と combat 0.7 | 6 秒は 768×1344、9 秒は 640×1152。格闘トリガーは付けない |
| `join` | ffmpeg | なし | 6 秒と 9 秒を足して 15 秒以上。実行しない |
| `affi_template` | 台本の参照 | なし | buy_before / daily_food / daily_camera。既存 fixtures |
| `combat_motion` | FL2VA | combat 1.0。Turbo は切る | 最初の絵と最後の絵。トリガー `prfight2`。`finish` で `prfight2, prfin1` |
| `swap_character` | Ref2VA | charswap 1.0。Turbo は切る | Video=動き、Picture=全身。Hero シート必須 |
| `swap_face` | Ref2VA | 同じファイル 1.0 | Picture は顔と髪。服は Video |
| `swap_outfit` | Ref2VA | 同じファイル 1.0 | Picture は服。顔は Video |
| `real` | 動画あり Ref2VA / なし FL2VA | anime2real 1.0 | 見た目は Picture |
| `orbit360` | FL2VA | なし | 同じ絵を首尾。他 LoRA は積まない |
| `two_pass` | A のあと B | パスごとに 1 系統 | B の Video 1 = `pass-a.mp4`。B は swap か real |
| `text_scene` | T2VA | なし | 文章だけ |

既定の1本は 5 秒（受け付けるのは 4 秒以上 5 秒以下）、`768x1344`（768P、9:16）、24fps。Combat と Swap で Turbo をオンにしてもプランではオフになる。

`h3_studio.py scenes` は `text_scene` を7本書く。公式 Hailuo の T2VA（`runtime=api`）。LoRA は空。Combat と charswap は切る。各本は1ショット、6秒、16:9、768P（`1344x768`。在庫の 9:16 と同じ二辺を入れ替えたもの）、24fps。action は英語1行で、日本語は「」だけ。3欄はエンジンが包む。sound は物理音だけ。配楽は `N/A`。ポスターは静止画で、この7本の動画にはしない。顔固定は後段の Ref2VA で、この7本には載せない。`generate` は false。並びは `hana-gate`、`host-live`、`hana-cart`、`hana-shelf`、`host-drop`、`hana-box`、`hana-exit`。

## フォーム

Hero と Enemy。項目は hair / color / race / age / height / weight / clothes / place。値が空ならその項目を Look に出さない。Enemy が全部空なら Enemy 行も出さない。

swap は Hero の絵（`hero_sheet`）が必須。Look が空でも絵があれば進む。

action は英語 1 行。日本語は入力の「」か `dialogue` の 1 つだけ。プロンプトでは公式の `<d>[Japanese] …</d>` に入れ、地の文には残さない。話者は画面外の (S1) で、唇は閉じたまま。

年齢の数字が 21 未満、または child / teen / 未成年の語があれば止まる。空の年齢は書かない。

入力に YouTube、Marvel、公式CM、オルビス、Furbo があれば止まる。商品名はプロンプトに書かない。

## ファイル

- `colab/h3_studio.py` と `minimaxh3/h3_studio.py` は同じバイト列。
- `colab/h3_studio_colab_main.py` がプラン JSON を書く。
- `colab/_write_studio_nb.py` が `minimax_h3_studio_bot.ipynb`（リポジトリ直下と `minimaxh3/`）を書く。
- `colab/test_h3_studio.py`
- ノートが取る helper は `colab/h3_studio.py` と `colab/h3_studio_colab_main.py` だけ。
- プランの置き場は Drive `minimax-h3-comfyui/studio/`。`episodes/` には書かない。

確認:

```bash
python3 -m pytest colab/test_h3_studio.py -q
```
