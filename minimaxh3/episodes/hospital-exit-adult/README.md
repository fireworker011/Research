# 病棟出口（`hospital-exit-adult`）

霞東アダルトとは**別スラッグ**。同じ枝。③ / Qwen には足さない。
霞東の執務室スチールはここにコピーしない。
感染者だらけの架空病院から出る予告。敵は全裸の成人女性かふたなり。血は出ない。

**Colab 5 番の構成でミッションが完了するか失敗するかが分かれる。**
受け入れる＝接合のまま出口・完了。誘う＝院内で淫欲・失敗。回避＝一人で出口・完了。戦って勝つ＝倒して出口・完了。戦って負ける＝敗北H・失敗。
4 番 Combat は戦い構成＋ハイメモリのときだけ。受け入れる約 50 秒。誘う約 53 秒。回避／勝ち約 45 秒。負け約 48 秒。
れい 24cm。かな 20cm（⑧）。しの 24cm（出口の最後。極端に背が高い灰白の笑い顔。全裸ふたなり。寝間着は出さない）。みきは竿なし。セックスは誰がどの方向へ動くかを書く（体位名だけにしない）。

バトルは参考クリップ約12秒の半分（trim 5秒）。GPU は T2V。カメラ既定は横スク。UNet は erotic + eros-max。戦いの Combat は 06 と 10 だけ。

理想台本は `SCRIPT.md`。問題は `PREP.md`。

## ワンクリック

1. このブランチが GitHub にあること。inbox には置かない。
2. Colab の `EPISODE = "hospital-exit-adult"`。`BRANCH = "cursor/h3-kasumi-adult-0402"`。霞東本体に戻すな。
3. 5 番で構成を選ぶ。迷ったら ○受け入れる。
4. Drive は `episodes/hospital-exit-adult/` と `models/erotic/` だけ。スチールは上書きしない。

```bash
cd minimaxh3
python h3_episode.py check   episodes/hospital-exit-adult
python h3_episode.py stills  episodes/hospital-exit-adult --out /tmp/ep/hospital-exit-adult
```
