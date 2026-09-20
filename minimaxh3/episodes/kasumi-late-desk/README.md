# 霞東フロア（`kasumi-late-desk`）

約 50 秒。朝に遅刻した成人 OL が、四択コマンドを△で抜けて自席へつく架空ゲームの予告。
本線は警備トート → 課長ファイル → 同僚マグ。口は「コピー です」。失敗は「隣の席に座った」。
しゃがみは横向き。首と胴が同じ方向。03 は 01 から chain。スチールは着地（last_frame）。格闘の着地は命中の瞬間。窓は末尾 6 秒。名札は無地。実時間。

理想台本（四択の中身とビジネス最適ルート）は `SCRIPT.md`。問題と対策は `PREP.md`。

## ワンクリック

1. このブランチが GitHub にあること（`episode.json` と `stills/`）。inbox には置かない。
2. Colab ノート `minimax_h3_episode_bot.ipynb` を開き、`EPISODE = "kasumi-late-desk"`。マージ前は `BRANCH` をこの PR ブランチにする。Run all。
3. または Grokbot に `minimaxh3/GROKBOT.md` の「霞東フロア」ブロックを貼る。

初回パックは 5 ビート ≈ 24.7 秒（カバー・覗き・会話・かばん・着席）。Drive にその `episode.json` が残ると 12 ビートは走らない。Run all はブランチから `episode.json` を取り直す。スチールと既存 raw は残し、新しいビート ID だけ描く。

GPU なし確認:

```bash
cd minimaxh3
python h3_episode.py check   episodes/kasumi-late-desk
python h3_episode.py stills  episodes/kasumi-late-desk --out /tmp/ep/kasumi-late-desk
python h3_episode.py dry-run episodes/kasumi-late-desk --out /tmp/ep/kasumi-late-desk
```
