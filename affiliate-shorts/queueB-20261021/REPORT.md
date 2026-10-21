# queueB 2026-10-21 結果

対象: kane-07, kane-08, kane-09, kane-10, nemuri-03, nemuri-04, nemuri-05。
投稿はしていない。mp4 は無い。QC の5項目は、絵が無いので実施していない。

台本の行（`lines/<id>.md`）とシーン表は入力にある。シーン表が指す本編の絵と、いらすとやの PNG は、このリポジトリに無い。作業ツリー（`claude/setup-colab-comfyui-Eb9Lh`）に `affiliate-shorts/` は無く、`git fetch origin` のあと全オブジェクトを名前で探しても、下のファイルは無かった。

リポジトリ内で見つかったもの（今回の本編ではない）:

- `origin/cursor/pr-endcards-6041` の `affiliate-shorts/v2/endcards/previews/`（money-receipt, money-stamp, money-ticker, sleep-breath, sleep-curtain, sleep-moon）。PR 用の最後2秒はここにある。本編が無いので付けていない。
- `origin/cursor/kane-v2-shorts-3575` の `affiliate-shorts/v2/kane/07`〜`10` は台本テキストだけ。`video_noaudio.mp4` は 01〜03 のみ。Remotion は `Stamp01` `Split02` `Ticket03` のみ。`Fold07` `Scale08` `Ledger09` `Night10` は無い。
- `origin/cursor/nemuri-tana-sleep-shorts-16b3` の `affiliate-shorts/v2/sleep/03`〜`05` は台本テキストだけ。無音の縦動画は 01 と 02 のみ。Remotion は `sleep01` と `sleep02` のみ。
- `origin/cursor/rebuild-phase-a-scenes-4321` の `body_clean.mp4` は kane-01〜03、nemuri-01〜02、konkatsu、pet。今回の7本は無い。

| id | 結果 | 書き出した尺 | 台本の合計（本編+PR） | QC |
|---|---|---|---|---|
| kane-07 | SKIPPED | なし | 30.0秒（28.0+2.0） | `kane-07/qc.md` |
| kane-08 | SKIPPED | なし | 33.0秒（31.0+2.0） | `kane-08/qc.md` |
| kane-09 | SKIPPED | なし | 52.0秒（50.0+2.0） | `kane-09/qc.md` |
| kane-10 | SKIPPED | なし | 29.0秒（27.0+2.0） | `kane-10/qc.md` |
| nemuri-03 | SKIPPED | なし | 32.0秒（30.0+2.0） | `nemuri-03/qc.md` |
| nemuri-04 | SKIPPED | なし | 36.0秒（34.0+2.0） | `nemuri-04/qc.md` |
| nemuri-05 | SKIPPED | なし | 21.0秒（19.0+2.0） | `nemuri-05/qc.md` |

台本の合計は `lines/<id>.md` の尺。書き出した動画の秒数ではない。
