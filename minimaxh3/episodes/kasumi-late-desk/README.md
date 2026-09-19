# 霞東フロア（`kasumi-late-desk`）

25 秒。朝に遅刻した成人 OL が、上司に見つからず自席へつく架空ゲームの予告。
借りるのは三人称カメラ・通路・覗き・失敗カードの文法だけ。定時退社シミュレーターの固有名は使わない。

通路 3.0 秒 → 覗き 5.0 秒 → 同僚（字幕のみ・自席完了）6.0 秒 → かばんメニュー 2.2 秒 → 着席 4.8 秒 → ミッション失敗「隣の席に座った」→ 免責。

準備・やらないこと・15 秒 LoRA を入れない理由は `PREP.md`。

## ワンクリック

1. このブランチが GitHub にあること（`episode.json` と `stills/`）。inbox には置かない。
2. Colab ノート `minimax_h3_episode_bot.ipynb` を開き、`EPISODE = "kasumi-late-desk"`。マージ前は `BRANCH` をこの PR ブランチにする。Run all。
3. または Grokbot に `minimaxh3/GROKBOT.md` の「霞東フロア」ブロックを貼る。

GPU なし確認:

```bash
cd minimaxh3
python h3_episode.py check   episodes/kasumi-late-desk
python h3_episode.py stills  episodes/kasumi-late-desk --out /tmp/ep/kasumi-late-desk
python h3_episode.py dry-run episodes/kasumi-late-desk --out /tmp/ep/kasumi-late-desk
```
