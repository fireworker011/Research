# 霞東フロア あさ（`kasumi-late-desk-adult`）

霞東リライトの**別スラッグ**。本体 `kasumi-late-desk` は触らない。
既存エロ動画（③ / STORY / Qwen）とも**別チャット**。続きは `HANDOVER.md` を新規チャットに貼る。
約 45 秒。朝に遅刻した成人が、四択の□口説くを三回選んで自席へつく架空ゲームの予告。
全員全裸。青木・黒木はふたなり。口は「コピー です」。失敗は「隣の席に座った」。
03 は 01 から chain。スチールは着地。Combat は 06 だけ（trigger 空）。
UNet は Eros Max FL2VA INT8（エロレーン専用）。霞東本体は stock のまま。

理想台本は `SCRIPT.md`。問題と対策は `PREP.md`。引き継ぎは `HANDOVER.md`。

## ワンクリック

1. このブランチが GitHub にあること（`episode.json` と `stills/`）。inbox には置かない。
2. Colab ノート `minimax_h3_episode_bot.ipynb` を開き Run all。このブランチの既定は `EPISODE = "kasumi-late-desk-adult"` / `BRANCH = "cursor/h3-kasumi-adult-0402"`。霞東本体に戻すな。
3. Drive は `episodes/kasumi-late-desk-adult/` だけ。bootstrap は GitHub から `episode.json` を取り直す。スチールは上書きしない。霞東の 5カット raw は reuse するな。

GPU なし確認:

```bash
cd minimaxh3
python h3_episode.py check   episodes/kasumi-late-desk-adult
python h3_episode.py stills  episodes/kasumi-late-desk-adult --out /tmp/ep/kasumi-late-desk-adult
```
