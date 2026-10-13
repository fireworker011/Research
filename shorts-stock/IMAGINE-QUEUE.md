# Imagine 待ち行列

使い順は婚活、美容、ペット。各ラインは日付の古い順、パックは 01 から。
2026-10-12 のペット 01–10 は Imagine 済みで結合済みなので、この待ち行列には入れない。
プロンプトは各 `IMAGINE.md` のショット用 text ブロックをそのまま写した。声のブロックはショットではないので入れていない。

未生成のパック 80 本、ショット 122 本。

「ファイル」は `finish.sh` が読むパス。`imagine/shot-01.mp4` から順に置く。
「保存名」は Grok Build がダウンロードして Drive に上げる名前。`<line>-<pack>-<shot>.mp4`。pack はフォルダ名、shot は `shot-01` のようにファイルの幹。
アプリの秒数が 6 秒刻みしか無いときは、6 秒で書き出し、同じ保存名のまま置く。`finish.sh` は各ファイルの頭から、ここに書いた秒だけを使う。声の長さに合わせて絵を切り直さない。
ショットの中で音楽とせりふは生成しない。声と BGM は `finish.sh` が後から乗せる。

## 一覧

| 順 | 保存名 | ファイル | 長さ | 動作 |
| --- | --- | --- | --- | --- |
| 1-1 | `konkatsu-01-profile-shot-01.mp4` | `shorts-stock/2026-10-12/konkatsu/01-profile/imagine/shot-01.mp4` | 2秒 | スマホの画面だけが止まっている |
| 1-2 | `konkatsu-01-profile-shot-02.mp4` | `shorts-stock/2026-10-12/konkatsu/01-profile/imagine/shot-02.mp4` | 4秒 | 指が1回スワイプする |
| 1-3 | `konkatsu-01-profile-shot-03.mp4` | `shorts-stock/2026-10-12/konkatsu/01-profile/imagine/shot-03.mp4` | 4秒 | 指が画面を伏せる |
| 2-1 | `konkatsu-02-notice-shot-01.mp4` | `shorts-stock/2026-10-12/konkatsu/02-notice/imagine/shot-01.mp4` | 2秒 | スマホの画面だけが止まっている |
| 2-2 | `konkatsu-02-notice-shot-02.mp4` | `shorts-stock/2026-10-12/konkatsu/02-notice/imagine/shot-02.mp4` | 4秒 | 指が1回スワイプする |
| 2-3 | `konkatsu-02-notice-shot-03.mp4` | `shorts-stock/2026-10-12/konkatsu/02-notice/imagine/shot-03.mp4` | 4秒 | 指が画面を伏せる |
| 3-1 | `konkatsu-03-talk-shot-01.mp4` | `shorts-stock/2026-10-12/konkatsu/03-talk/imagine/shot-01.mp4` | 2秒 | スマホの画面だけが止まっている |
| 3-2 | `konkatsu-03-talk-shot-02.mp4` | `shorts-stock/2026-10-12/konkatsu/03-talk/imagine/shot-02.mp4` | 4秒 | 指が1回スワイプする |
| 3-3 | `konkatsu-03-talk-shot-03.mp4` | `shorts-stock/2026-10-12/konkatsu/03-talk/imagine/shot-03.mp4` | 4秒 | 指が画面を伏せる |
| 4-1 | `konkatsu-04-age-shot-01.mp4` | `shorts-stock/2026-10-12/konkatsu/04-age/imagine/shot-01.mp4` | 2秒 | 手がスマホを持って止まる |
| 4-2 | `konkatsu-04-age-shot-02.mp4` | `shorts-stock/2026-10-12/konkatsu/04-age/imagine/shot-02.mp4` | 5秒 | 指が年齢のところで止まる |
| 4-3 | `konkatsu-04-age-shot-03.mp4` | `shorts-stock/2026-10-12/konkatsu/04-age/imagine/shot-03.mp4` | 5秒 | 指が画面を閉じる |
| 5-1 | `konkatsu-05-read-shot-01.mp4` | `shorts-stock/2026-10-12/konkatsu/05-read/imagine/shot-01.mp4` | 2秒 | 手がスマホを持って止まる |
| 5-2 | `konkatsu-05-read-shot-02.mp4` | `shorts-stock/2026-10-12/konkatsu/05-read/imagine/shot-02.mp4` | 5秒 | 指が既読のところで止まる |
| 5-3 | `konkatsu-05-read-shot-03.mp4` | `shorts-stock/2026-10-12/konkatsu/05-read/imagine/shot-03.mp4` | 5秒 | 指が画面を閉じる |
| 6-1 | `konkatsu-06-photo-shot-01.mp4` | `shorts-stock/2026-10-12/konkatsu/06-photo/imagine/shot-01.mp4` | 2秒 | 手がスマホを持って止まる |
| 6-2 | `konkatsu-06-photo-shot-02.mp4` | `shorts-stock/2026-10-12/konkatsu/06-photo/imagine/shot-02.mp4` | 5秒 | 指が写真のところで止まる |
| 6-3 | `konkatsu-06-photo-shot-03.mp4` | `shorts-stock/2026-10-12/konkatsu/06-photo/imagine/shot-03.mp4` | 5秒 | 指が画面を閉じる |
| 7-1 | `konkatsu-07-clip-shot-01.mp4` | `shorts-stock/2026-10-12/konkatsu/07-clip/imagine/shot-01.mp4` | 2秒 | 机の上の紙だけが止まっている |
| 7-2 | `konkatsu-07-clip-shot-02.mp4` | `shorts-stock/2026-10-12/konkatsu/07-clip/imagine/shot-02.mp4` | 4秒 | 手がクリップを1回指す |
| 7-3 | `konkatsu-07-clip-shot-03.mp4` | `shorts-stock/2026-10-12/konkatsu/07-clip/imagine/shot-03.mp4` | 4秒 | 手がペンを置く |
| 8-1 | `konkatsu-08-fold-shot-01.mp4` | `shorts-stock/2026-10-12/konkatsu/08-fold/imagine/shot-01.mp4` | 2秒 | 机の上の紙だけが止まっている |
| 8-2 | `konkatsu-08-fold-shot-02.mp4` | `shorts-stock/2026-10-12/konkatsu/08-fold/imagine/shot-02.mp4` | 4秒 | 手が折り目を1回指す |
| 8-3 | `konkatsu-08-fold-shot-03.mp4` | `shorts-stock/2026-10-12/konkatsu/08-fold/imagine/shot-03.mp4` | 4秒 | 手がペンを置く |
| 9-1 | `konkatsu-09-square-shot-01.mp4` | `shorts-stock/2026-10-12/konkatsu/09-square/imagine/shot-01.mp4` | 2秒 | 机の上の紙だけが止まっている |
| 9-2 | `konkatsu-09-square-shot-02.mp4` | `shorts-stock/2026-10-12/konkatsu/09-square/imagine/shot-02.mp4` | 4秒 | 手が無地の四角を1回指す |
| 9-3 | `konkatsu-09-square-shot-03.mp4` | `shorts-stock/2026-10-12/konkatsu/09-square/imagine/shot-03.mp4` | 4秒 | 手がペンを置く |
| 10-1 | `konkatsu-10-hole-shot-01.mp4` | `shorts-stock/2026-10-12/konkatsu/10-hole/imagine/shot-01.mp4` | 2秒 | 机の上の紙だけが止まっている |
| 10-2 | `konkatsu-10-hole-shot-02.mp4` | `shorts-stock/2026-10-12/konkatsu/10-hole/imagine/shot-02.mp4` | 4秒 | 手が穴を1回指す |
| 10-3 | `konkatsu-10-hole-shot-03.mp4` | `shorts-stock/2026-10-12/konkatsu/10-hole/imagine/shot-03.mp4` | 4秒 | 手がペンを置く |
| 11-1 | `konkatsu-01-thumb-off-shot-01.mp4` | `shorts-stock/2026-10-13/konkatsu/01-thumb-off/imagine/shot-01.mp4` | 5秒 | 親指がスマホの縁から1回離れる |
| 12-1 | `konkatsu-02-dim-shot-01.mp4` | `shorts-stock/2026-10-13/konkatsu/02-dim/imagine/shot-01.mp4` | 5秒 | 持ったスマホの画面が1回暗くなる |
| 13-1 | `konkatsu-03-flip-up-shot-01.mp4` | `shorts-stock/2026-10-13/konkatsu/03-flip-up/imagine/shot-01.mp4` | 5秒 | 伏せたスマホを1回表にする |
| 14-1 | `konkatsu-04-beside-shot-01.mp4` | `shorts-stock/2026-10-13/konkatsu/04-beside/imagine/shot-01.mp4` | 5秒 | スマホを無地のノートの横へ1回ずらす |
| 15-1 | `konkatsu-05-regrip-shot-01.mp4` | `shorts-stock/2026-10-13/konkatsu/05-regrip/imagine/shot-01.mp4` | 5秒 | 左手が入り、両手でスマホを1回持ち直す |
| 16-1 | `konkatsu-06-lamp-shot-01.mp4` | `shorts-stock/2026-10-13/konkatsu/06-lamp/imagine/shot-01.mp4` | 5秒 | スマホをランプの光の下へ1回滑らせる |
| 17-1 | `konkatsu-07-cable-shot-01.mp4` | `shorts-stock/2026-10-13/konkatsu/07-cable/imagine/shot-01.mp4` | 5秒 | 無地のケーブルをスマホから1回外す |
| 18-1 | `konkatsu-08-corner-shot-01.mp4` | `shorts-stock/2026-10-13/konkatsu/08-corner/imagine/shot-01.mp4` | 5秒 | 無地のケースの角を指で1回なぞる |
| 19-1 | `konkatsu-09-under-shot-01.mp4` | `shorts-stock/2026-10-13/konkatsu/09-under/imagine/shot-01.mp4` | 5秒 | スマホを無地のノートの下へ1回滑らせる |
| 20-1 | `konkatsu-10-set-dark-shot-01.mp4` | `shorts-stock/2026-10-13/konkatsu/10-set-dark/imagine/shot-01.mp4` | 5秒 | 画面が消えたスマホを机に1回置く |
| 21-1 | `konkatsu-01-palm-shot-01.mp4` | `shorts-stock/2026-10-14/konkatsu/01-palm/imagine/shot-01.mp4` | 5秒 | 手のひらを机に1回伏せる |
| 22-1 | `konkatsu-02-cuff-shot-01.mp4` | `shorts-stock/2026-10-14/konkatsu/02-cuff/imagine/shot-01.mp4` | 5秒 | グレーの袖口を1回直す |
| 23-1 | `konkatsu-03-push-shot-01.mp4` | `shorts-stock/2026-10-14/konkatsu/03-push/imagine/shot-01.mp4` | 5秒 | 机のスマホを奥へ1回押す |
| 24-1 | `konkatsu-04-pinch-shot-01.mp4` | `shorts-stock/2026-10-14/konkatsu/04-pinch/imagine/shot-01.mp4` | 5秒 | スマホの縁を2本の指で1回挟む |
| 25-1 | `konkatsu-05-spin-shot-01.mp4` | `shorts-stock/2026-10-14/konkatsu/05-spin/imagine/shot-01.mp4` | 5秒 | 机のスマホを1回回す |
| 26-1 | `konkatsu-06-hover-shot-01.mp4` | `shorts-stock/2026-10-14/konkatsu/06-hover/imagine/shot-01.mp4` | 5秒 | 人差し指が画面の上で1回止まり、触れない |
| 27-1 | `konkatsu-07-coaster-shot-01.mp4` | `shorts-stock/2026-10-14/konkatsu/07-coaster/imagine/shot-01.mp4` | 5秒 | 無地のコースターをスマホの下へ1回敷く |
| 28-1 | `konkatsu-08-left-shot-01.mp4` | `shorts-stock/2026-10-14/konkatsu/08-left/imagine/shot-01.mp4` | 5秒 | 左手を机に1回置く |
| 29-1 | `konkatsu-09-shade-shot-01.mp4` | `shorts-stock/2026-10-14/konkatsu/09-shade/imagine/shot-01.mp4` | 5秒 | ランプの傘を1回回す |
| 30-1 | `konkatsu-10-stand-shot-01.mp4` | `shorts-stock/2026-10-14/konkatsu/10-stand/imagine/shot-01.mp4` | 5秒 | 机のスマホを縁で1回立てる |
| 31-1 | `beauty-01-frost-slim-shot-01.mp4` | `shorts-stock/2026-10-12/beauty/01-frost-slim/imagine/shot-01.mp4` | 2秒 | すりガラスのポンプを持って止まる |
| 31-2 | `beauty-01-frost-slim-shot-02.mp4` | `shorts-stock/2026-10-12/beauty/01-frost-slim/imagine/shot-02.mp4` | 4秒 | 手の甲に1回つける |
| 31-3 | `beauty-01-frost-slim-shot-03.mp4` | `shorts-stock/2026-10-12/beauty/01-frost-slim/imagine/shot-03.mp4` | 2秒 | 細い瓶に持ち替える |
| 31-4 | `beauty-01-frost-slim-shot-04.mp4` | `shorts-stock/2026-10-12/beauty/01-frost-slim/imagine/shot-04.mp4` | 4秒 | 手の甲に1回つける |
| 32-1 | `beauty-02-dropper-pump-shot-01.mp4` | `shorts-stock/2026-10-12/beauty/02-dropper-pump/imagine/shot-01.mp4` | 2秒 | スポイト瓶を持って止まる |
| 32-2 | `beauty-02-dropper-pump-shot-02.mp4` | `shorts-stock/2026-10-12/beauty/02-dropper-pump/imagine/shot-02.mp4` | 4秒 | 手の甲に1回つける |
| 32-3 | `beauty-02-dropper-pump-shot-03.mp4` | `shorts-stock/2026-10-12/beauty/02-dropper-pump/imagine/shot-03.mp4` | 2秒 | 短いポンプに持ち替える |
| 32-4 | `beauty-02-dropper-pump-shot-04.mp4` | `shorts-stock/2026-10-12/beauty/02-dropper-pump/imagine/shot-04.mp4` | 4秒 | 手の甲に1回つける |
| 33-1 | `beauty-03-hand-shot-01.mp4` | `shorts-stock/2026-10-12/beauty/03-hand/imagine/shot-01.mp4` | 2秒 | 右手の甲の近い画で止まる |
| 33-2 | `beauty-03-hand-shot-02.mp4` | `shorts-stock/2026-10-12/beauty/03-hand/imagine/shot-02.mp4` | 5秒 | 右手の甲に1回だけ塗る |
| 33-3 | `beauty-03-hand-shot-03.mp4` | `shorts-stock/2026-10-12/beauty/03-hand/imagine/shot-03.mp4` | 5秒 | 塗る前と同じ画角で止まる |
| 34-1 | `beauty-04-forearm-shot-01.mp4` | `shorts-stock/2026-10-12/beauty/04-forearm/imagine/shot-01.mp4` | 2秒 | 前腕の近い画で止まる |
| 34-2 | `beauty-04-forearm-shot-02.mp4` | `shorts-stock/2026-10-12/beauty/04-forearm/imagine/shot-02.mp4` | 5秒 | 前腕に1回だけ塗る |
| 34-3 | `beauty-04-forearm-shot-03.mp4` | `shorts-stock/2026-10-12/beauty/04-forearm/imagine/shot-03.mp4` | 5秒 | 塗る前と同じ画角で止まる |
| 35-1 | `beauty-05-wrist-shot-01.mp4` | `shorts-stock/2026-10-12/beauty/05-wrist/imagine/shot-01.mp4` | 2秒 | 手首の近い画で止まる |
| 35-2 | `beauty-05-wrist-shot-02.mp4` | `shorts-stock/2026-10-12/beauty/05-wrist/imagine/shot-02.mp4` | 5秒 | 手首に1回だけ塗る |
| 35-3 | `beauty-05-wrist-shot-03.mp4` | `shorts-stock/2026-10-12/beauty/05-wrist/imagine/shot-03.mp4` | 5秒 | 塗る前と同じ画角で止まる |
| 36-1 | `beauty-06-other-hand-shot-01.mp4` | `shorts-stock/2026-10-12/beauty/06-other-hand/imagine/shot-01.mp4` | 2秒 | 左手の甲の近い画で止まる |
| 36-2 | `beauty-06-other-hand-shot-02.mp4` | `shorts-stock/2026-10-12/beauty/06-other-hand/imagine/shot-02.mp4` | 5秒 | 左手の甲に1回だけ塗る |
| 36-3 | `beauty-06-other-hand-shot-03.mp4` | `shorts-stock/2026-10-12/beauty/06-other-hand/imagine/shot-03.mp4` | 5秒 | 塗る前と同じ画角で止まる |
| 37-1 | `beauty-07-extra-bottle-shot-01.mp4` | `shorts-stock/2026-10-12/beauty/07-extra-bottle/imagine/shot-01.mp4` | 2秒 | もう1本のポンプを持って止まる |
| 37-2 | `beauty-07-extra-bottle-shot-02.mp4` | `shorts-stock/2026-10-12/beauty/07-extra-bottle/imagine/shot-02.mp4` | 5秒 | もう1本のポンプを机の外へ1回動かす |
| 37-3 | `beauty-07-extra-bottle-shot-03.mp4` | `shorts-stock/2026-10-12/beauty/07-extra-bottle/imagine/shot-03.mp4` | 5秒 | 残った1本だけが棚にある |
| 38-1 | `beauty-08-cotton-shot-01.mp4` | `shorts-stock/2026-10-12/beauty/08-cotton/imagine/shot-01.mp4` | 2秒 | コットンを持って止まる |
| 38-2 | `beauty-08-cotton-shot-02.mp4` | `shorts-stock/2026-10-12/beauty/08-cotton/imagine/shot-02.mp4` | 5秒 | コットンを机の外へ1回動かす |
| 38-3 | `beauty-08-cotton-shot-03.mp4` | `shorts-stock/2026-10-12/beauty/08-cotton/imagine/shot-03.mp4` | 5秒 | 残った1本だけが棚にある |
| 39-1 | `beauty-09-pouch-shot-01.mp4` | `shorts-stock/2026-10-12/beauty/09-pouch/imagine/shot-01.mp4` | 2秒 | パックの袋を持って止まる |
| 39-2 | `beauty-09-pouch-shot-02.mp4` | `shorts-stock/2026-10-12/beauty/09-pouch/imagine/shot-02.mp4` | 5秒 | パックの袋を机の外へ1回動かす |
| 39-3 | `beauty-09-pouch-shot-03.mp4` | `shorts-stock/2026-10-12/beauty/09-pouch/imagine/shot-03.mp4` | 5秒 | 残った1本だけが棚にある |
| 40-1 | `beauty-10-dish-shot-01.mp4` | `shorts-stock/2026-10-12/beauty/10-dish/imagine/shot-01.mp4` | 2秒 | 小皿を持って止まる |
| 40-2 | `beauty-10-dish-shot-02.mp4` | `shorts-stock/2026-10-12/beauty/10-dish/imagine/shot-02.mp4` | 5秒 | 小皿を机の外へ1回動かす |
| 40-3 | `beauty-10-dish-shot-03.mp4` | `shorts-stock/2026-10-12/beauty/10-dish/imagine/shot-03.mp4` | 5秒 | 残った1本だけが棚にある |
| 41-1 | `beauty-01-cap-shot-01.mp4` | `shorts-stock/2026-10-13/beauty/01-cap/imagine/shot-01.mp4` | 5秒 | 細い瓶の白いキャップを1回閉める |
| 42-1 | `beauty-02-pump-shot-01.mp4` | `shorts-stock/2026-10-13/beauty/02-pump/imagine/shot-01.mp4` | 5秒 | すりガラスのポンプの頭を1回押して戻す |
| 43-1 | `beauty-03-align-shot-01.mp4` | `shorts-stock/2026-10-13/beauty/03-align/imagine/shot-01.mp4` | 5秒 | 棚の2本を奥へ1回揃える |
| 44-1 | `beauty-04-lamp-shot-01.mp4` | `shorts-stock/2026-10-13/beauty/04-lamp/imagine/shot-01.mp4` | 5秒 | 小さなランプを瓶の横へ1回寄せる |
| 45-1 | `beauty-05-wipe-shot-01.mp4` | `shorts-stock/2026-10-13/beauty/05-wipe/imagine/shot-01.mp4` | 5秒 | 無地の布で棚の木を1回拭く |
| 46-1 | `beauty-06-turn-shot-01.mp4` | `shorts-stock/2026-10-13/beauty/06-turn/imagine/shot-01.mp4` | 5秒 | すりガラスの瓶を1回回す |
| 47-1 | `beauty-07-cap-down-shot-01.mp4` | `shorts-stock/2026-10-13/beauty/07-cap-down/imagine/shot-01.mp4` | 5秒 | 外してある白いキャップを棚に1回置く |
| 48-1 | `beauty-08-pinch-shot-01.mp4` | `shorts-stock/2026-10-13/beauty/08-pinch/imagine/shot-01.mp4` | 5秒 | 細い瓶の腹を2本の指で1回挟む |
| 49-1 | `beauty-09-shadow-shot-01.mp4` | `shorts-stock/2026-10-13/beauty/09-shadow/imagine/shot-01.mp4` | 5秒 | 手をランプと瓶の間で1回止めて影を落とす |
| 50-1 | `beauty-10-tilt-shot-01.mp4` | `shorts-stock/2026-10-13/beauty/10-tilt/imagine/shot-01.mp4` | 5秒 | すりガラスの瓶をランプの方へ1回傾けて止める |
| 51-1 | `beauty-01-return-shot-01.mp4` | `shorts-stock/2026-10-14/beauty/01-return/imagine/shot-01.mp4` | 5秒 | ずらしてあるすりガラスのポンプを元の位置へ1回戻す |
| 52-1 | `beauty-02-lift-cap-shot-01.mp4` | `shorts-stock/2026-10-14/beauty/02-lift-cap/imagine/shot-01.mp4` | 5秒 | 細い瓶の白いキャップを1回持ち上げて止める |
| 53-1 | `beauty-03-gap-shot-01.mp4` | `shorts-stock/2026-10-14/beauty/03-gap/imagine/shot-01.mp4` | 5秒 | 並んだ2本の間隔を1回あける |
| 54-1 | `beauty-04-lamp-back-shot-01.mp4` | `shorts-stock/2026-10-14/beauty/04-lamp-back/imagine/shot-01.mp4` | 5秒 | 瓶の横にあるランプを奥へ1回戻す |
| 55-1 | `beauty-05-cap-wipe-shot-01.mp4` | `shorts-stock/2026-10-14/beauty/05-cap-wipe/imagine/shot-01.mp4` | 5秒 | 無地の布で白いキャップの上面を1回拭く |
| 56-1 | `beauty-06-upright-shot-01.mp4` | `shorts-stock/2026-10-14/beauty/06-upright/imagine/shot-01.mp4` | 5秒 | 傾いている細い瓶を1回立てる |
| 57-1 | `beauty-07-palm-shot-01.mp4` | `shorts-stock/2026-10-14/beauty/07-palm/imagine/shot-01.mp4` | 5秒 | 手のひらを棚の木に1回置く |
| 58-1 | `beauty-08-swap-shot-01.mp4` | `shorts-stock/2026-10-14/beauty/08-swap/imagine/shot-01.mp4` | 5秒 | 棚の2本の位置を1回入れ替える |
| 59-1 | `beauty-09-nozzle-shot-01.mp4` | `shorts-stock/2026-10-14/beauty/09-nozzle/imagine/shot-01.mp4` | 5秒 | ポンプの口を横へ1回向ける |
| 60-1 | `beauty-10-fold-shot-01.mp4` | `shorts-stock/2026-10-14/beauty/10-fold/imagine/shot-01.mp4` | 5秒 | 瓶の横の無地の布を1回畳む |
| 61-1 | `pet-01-gray-blink-shot-01.mp4` | `shorts-stock/2026-10-13/pet/01-gray-blink/imagine/shot-01.mp4` | 5秒 | グレーのマンチカンがソファでまばたきを1回する |
| 62-1 | `pet-02-white-yawn-shot-01.mp4` | `shorts-stock/2026-10-13/pet/02-white-yawn/imagine/shot-01.mp4` | 5秒 | 白いスコティッシュフォールドがラグで欠伸を1回する |
| 63-1 | `pet-03-gray-lick-shot-01.mp4` | `shorts-stock/2026-10-13/pet/03-gray-lick/imagine/shot-01.mp4` | 5秒 | グレーのマンチカンがソファで前足を1回なめる |
| 64-1 | `pet-04-white-ear-shot-01.mp4` | `shorts-stock/2026-10-13/pet/04-white-ear/imagine/shot-01.mp4` | 5秒 | 白いスコティッシュフォールドがソファで耳を1回動かす |
| 65-1 | `pet-05-gray-paw-shot-01.mp4` | `shorts-stock/2026-10-13/pet/05-gray-paw/imagine/shot-01.mp4` | 5秒 | グレーのマンチカンがラグの上で前足を前へ1回伸ばす |
| 66-1 | `pet-06-white-tail-shot-01.mp4` | `shorts-stock/2026-10-13/pet/06-white-tail/imagine/shot-01.mp4` | 5秒 | 白いスコティッシュフォールドがラグでしっぽの先を1回振る |
| 67-1 | `pet-07-gray-loaf-shot-01.mp4` | `shorts-stock/2026-10-13/pet/07-gray-loaf/imagine/shot-01.mp4` | 5秒 | グレーのマンチカンがソファで両前足を腹の下にしまう |
| 68-1 | `pet-08-white-window-shot-01.mp4` | `shorts-stock/2026-10-13/pet/08-white-window/imagine/shot-01.mp4` | 5秒 | 白いスコティッシュフォールドがソファで窓の方へ顔を1回向ける |
| 69-1 | `pet-09-gray-sniff-shot-01.mp4` | `shorts-stock/2026-10-13/pet/09-gray-sniff/imagine/shot-01.mp4` | 5秒 | グレーのマンチカンがラグに鼻を1回近づける |
| 70-1 | `pet-10-white-chin-shot-01.mp4` | `shorts-stock/2026-10-13/pet/10-white-chin/imagine/shot-01.mp4` | 5秒 | 白いスコティッシュフォールドがラグであごを前足の上に乗せる |
| 71-1 | `pet-01-gray-paws-shot-01.mp4` | `shorts-stock/2026-10-14/pet/01-gray-paws/imagine/shot-01.mp4` | 5秒 | グレーのマンチカンがソファで自分の前足を1回見る |
| 72-1 | `pet-02-white-side-shot-01.mp4` | `shorts-stock/2026-10-14/pet/02-white-side/imagine/shot-01.mp4` | 5秒 | 白いスコティッシュフォールドがラグで顔を横へ1回向ける |
| 73-1 | `pet-03-gray-wrap-shot-01.mp4` | `shorts-stock/2026-10-14/pet/03-gray-wrap/imagine/shot-01.mp4` | 5秒 | グレーのマンチカンがラグでしっぽを体に1回巻く |
| 74-1 | `pet-04-white-stack-shot-01.mp4` | `shorts-stock/2026-10-14/pet/04-white-stack/imagine/shot-01.mp4` | 5秒 | 白いスコティッシュフォールドがソファで前足を1回重ねる |
| 75-1 | `pet-05-gray-lift-shot-01.mp4` | `shorts-stock/2026-10-14/pet/05-gray-lift/imagine/shot-01.mp4` | 5秒 | グレーのマンチカンがソファで顔を1回上げる |
| 76-1 | `pet-06-white-chest-shot-01.mp4` | `shorts-stock/2026-10-14/pet/06-white-chest/imagine/shot-01.mp4` | 5秒 | 白いスコティッシュフォールドがラグで胸を1回なめる |
| 77-1 | `pet-07-gray-tap-shot-01.mp4` | `shorts-stock/2026-10-14/pet/07-gray-tap/imagine/shot-01.mp4` | 5秒 | グレーのマンチカンがソファのクッションを前足で1回触る |
| 78-1 | `pet-08-white-paw-up-shot-01.mp4` | `shorts-stock/2026-10-14/pet/08-white-paw-up/imagine/shot-01.mp4` | 5秒 | 白いスコティッシュフォールドがソファで前足を1回上げて止める |
| 79-1 | `pet-09-gray-chin-shot-01.mp4` | `shorts-stock/2026-10-14/pet/09-gray-chin/imagine/shot-01.mp4` | 5秒 | グレーのマンチカンがラグであごをラグに1回つける |
| 80-1 | `pet-10-white-hide-shot-01.mp4` | `shorts-stock/2026-10-14/pet/10-white-hide/imagine/shot-01.mp4` | 5秒 | 白いスコティッシュフォールドがラグで前足を顔の前へ1回置く |

## プロンプト

## 婚活

### 1. `2026-10-12/konkatsu/01-profile`

絵の合計: 10秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: スマホの画面だけが止まっている

保存名: `konkatsu-01-profile-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/01-profile/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone with no logo. The screen is a soft blur with no letters, numbers, or pictures of a face.
The hand holds the phone flat, screen up. The screen reads as one blurred profile card, a blank rectangle where a portrait would be, no face and no letters.
One action: the hand holds the phone still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（4秒、2–6秒）

動作: 指が1回スワイプする

保存名: `konkatsu-01-profile-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/01-profile/imagine/shot-02.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal close-up, same night desk, same hand, same phone. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The screen still reads as one blurred profile card, a blank rectangle where a portrait would be, no face and no letters, with no letters.
One action: one finger swipes the screen once.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft finger swipe, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（4秒、6–10秒）

動作: 指が画面を伏せる

保存名: `konkatsu-01-profile-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/01-profile/imagine/shot-03.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal close-up, same night desk, same hand, same phone. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
One action: the hand turns the phone face down onto the desk.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft phone set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 2. `2026-10-12/konkatsu/02-notice`

絵の合計: 10秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: スマホの画面だけが止まっている

保存名: `konkatsu-02-notice-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/02-notice/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone with no logo. The screen is a soft blur with no letters, numbers, or pictures of a face.
The hand holds the phone flat, screen up. The screen reads as one blurred notification row, a small empty circle, no letters and no face.
One action: the hand holds the phone still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（4秒、2–6秒）

動作: 指が1回スワイプする

保存名: `konkatsu-02-notice-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/02-notice/imagine/shot-02.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal close-up, same night desk, same hand, same phone. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The screen still reads as one blurred notification row, a small empty circle, no letters and no face, with no letters.
One action: one finger swipes the screen once.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft finger swipe, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（4秒、6–10秒）

動作: 指が画面を伏せる

保存名: `konkatsu-02-notice-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/02-notice/imagine/shot-03.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal close-up, same night desk, same hand, same phone. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
One action: the hand turns the phone face down onto the desk.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft phone set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 3. `2026-10-12/konkatsu/03-talk`

絵の合計: 10秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: スマホの画面だけが止まっている

保存名: `konkatsu-03-talk-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/03-talk/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone with no logo. The screen is a soft blur with no letters, numbers, or pictures of a face.
The hand holds the phone flat, screen up. The screen reads as one blurred message thread of empty gray bubbles, no letters and no face.
One action: the hand holds the phone still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（4秒、2–6秒）

動作: 指が1回スワイプする

保存名: `konkatsu-03-talk-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/03-talk/imagine/shot-02.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal close-up, same night desk, same hand, same phone. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The screen still reads as one blurred message thread of empty gray bubbles, no letters and no face, with no letters.
One action: one finger swipes the screen once.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft finger swipe, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（4秒、6–10秒）

動作: 指が画面を伏せる

保存名: `konkatsu-03-talk-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/03-talk/imagine/shot-03.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal close-up, same night desk, same hand, same phone. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
One action: the hand turns the phone face down onto the desk.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft phone set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 4. `2026-10-12/konkatsu/04-age`

絵の合計: 12秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: 手がスマホを持って止まる

保存名: `konkatsu-04-age-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/04-age/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone with no logo. The screen is a soft blur with no letters, numbers, or pictures of a face.
The hand holds the phone and does not scroll.
One action: the hand holds the phone still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（5秒、2–7秒）

動作: 指が年齢のところで止まる

保存名: `konkatsu-04-age-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/04-age/imagine/shot-02.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night desk, same hand, same phone. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The screen is a soft blur. The finger stops on the top band of one blurred card. The band has no letters and no numbers.
One action: the finger stops on that one region.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft finger stop, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（5秒、7–12秒）

動作: 指が画面を閉じる

保存名: `konkatsu-04-age-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/04-age/imagine/shot-03.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night desk, same hand, same phone. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
One action: the finger closes the phone so the screen goes dark.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft click, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 5. `2026-10-12/konkatsu/05-read`

絵の合計: 12秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: 手がスマホを持って止まる

保存名: `konkatsu-05-read-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/05-read/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone with no logo. The screen is a soft blur with no letters, numbers, or pictures of a face.
The hand holds the phone and does not scroll.
One action: the hand holds the phone still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（5秒、2–7秒）

動作: 指が既読のところで止まる

保存名: `konkatsu-05-read-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/05-read/imagine/shot-02.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night desk, same hand, same phone. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The screen is a soft blur. The finger stops on one small empty circle. The circle has no glyph.
One action: the finger stops on that one region.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft finger stop, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（5秒、7–12秒）

動作: 指が画面を閉じる

保存名: `konkatsu-05-read-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/05-read/imagine/shot-03.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night desk, same hand, same phone. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
One action: the finger closes the phone so the screen goes dark.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft click, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 6. `2026-10-12/konkatsu/06-photo`

絵の合計: 12秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: 手がスマホを持って止まる

保存名: `konkatsu-06-photo-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/06-photo/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone with no logo. The screen is a soft blur with no letters, numbers, or pictures of a face.
The hand holds the phone and does not scroll.
One action: the hand holds the phone still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（5秒、2–7秒）

動作: 指が写真のところで止まる

保存名: `konkatsu-06-photo-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/06-photo/imagine/shot-02.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night desk, same hand, same phone. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The screen is a soft blur. The finger stops on one square color block. The block contains no face and no person.
One action: the finger stops on that one region.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft finger stop, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（5秒、7–12秒）

動作: 指が画面を閉じる

保存名: `konkatsu-06-photo-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/06-photo/imagine/shot-03.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night desk, same hand, same phone. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
One action: the finger closes the phone so the screen goes dark.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft click, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 7. `2026-10-12/konkatsu/07-clip`

絵の合計: 10秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: 机の上の紙だけが止まっている

保存名: `konkatsu-07-clip-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/07-clip/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal top-down view of a wooden desk at night, warm lamp. One blank sheet of paper. A single plain metal paperclip holds the top edge. No handwriting and no printed letters.
The hand is not in frame yet.
One action: the paper lies still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（4秒、2–6秒）

動作: 手がクリップを1回指す

保存名: `konkatsu-07-clip-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/07-clip/imagine/shot-02.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal top-down view, same desk, same paper. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A single plain metal paperclip holds the top edge. No letters.
One action: the index finger points at that mark.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（4秒、6–10秒）

動作: 手がペンを置く

保存名: `konkatsu-07-clip-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/07-clip/imagine/shot-03.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal top-down view, same desk, same paper. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain uncapped pen with no logo is in the hand.
One action: the hand sets the pen down on the desk beside the paper.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft pen set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 8. `2026-10-12/konkatsu/08-fold`

絵の合計: 10秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: 机の上の紙だけが止まっている

保存名: `konkatsu-08-fold-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/08-fold/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal top-down view of a wooden desk at night, warm lamp. One blank sheet of paper. One corner of the paper is folded over. The fold has no writing. No handwriting and no printed letters.
The hand is not in frame yet.
One action: the paper lies still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（4秒、2–6秒）

動作: 手が折り目を1回指す

保存名: `konkatsu-08-fold-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/08-fold/imagine/shot-02.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal top-down view, same desk, same paper. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
One corner of the paper is folded over. The fold has no writing. No letters.
One action: the index finger points at that mark.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（4秒、6–10秒）

動作: 手がペンを置く

保存名: `konkatsu-08-fold-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/08-fold/imagine/shot-03.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal top-down view, same desk, same paper. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain uncapped pen with no logo is in the hand.
One action: the hand sets the pen down on the desk beside the paper.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft pen set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 9. `2026-10-12/konkatsu/09-square`

絵の合計: 10秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: 机の上の紙だけが止まっている

保存名: `konkatsu-09-square-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/09-square/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal top-down view of a wooden desk at night, warm lamp. One blank sheet of paper. One small blank paper square sits in the center. The square has no writing. No handwriting and no printed letters.
The hand is not in frame yet.
One action: the paper lies still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（4秒、2–6秒）

動作: 手が無地の四角を1回指す

保存名: `konkatsu-09-square-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/09-square/imagine/shot-02.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal top-down view, same desk, same paper. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
One small blank paper square sits in the center. The square has no writing. No letters.
One action: the index finger points at that mark.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（4秒、6–10秒）

動作: 手がペンを置く

保存名: `konkatsu-09-square-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/09-square/imagine/shot-03.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal top-down view, same desk, same paper. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain uncapped pen with no logo is in the hand.
One action: the hand sets the pen down on the desk beside the paper.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft pen set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 10. `2026-10-12/konkatsu/10-hole`

絵の合計: 10秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: 机の上の紙だけが止まっている

保存名: `konkatsu-10-hole-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/10-hole/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal top-down view of a wooden desk at night, warm lamp. One blank sheet of paper. One round hole is punched on the left edge. No letters around the hole. No handwriting and no printed letters.
The hand is not in frame yet.
One action: the paper lies still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（4秒、2–6秒）

動作: 手が穴を1回指す

保存名: `konkatsu-10-hole-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/10-hole/imagine/shot-02.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal top-down view, same desk, same paper. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
One round hole is punched on the left edge. No letters around the hole. No letters.
One action: the index finger points at that mark.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（4秒、6–10秒）

動作: 手がペンを置く

保存名: `konkatsu-10-hole-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/konkatsu/10-hole/imagine/shot-03.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal top-down view, same desk, same paper. Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain uncapped pen with no logo is in the hand.
One action: the hand sets the pen down on the desk beside the paper.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft pen set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 11. `2026-10-13/konkatsu/01-thumb-off`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 親指がスマホの縁から1回離れる

保存名: `konkatsu-01-thumb-off-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/konkatsu/01-thumb-off/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The hand holds a plain black phone with no logo. The screen is a soft blur with no letters, numbers, or pictures of a face. The thumb rests on the bezel, not on a button.
One action: the thumb lifts off the bezel once. The finger does not swipe.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft thumb lift, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 12. `2026-10-13/konkatsu/02-dim`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 持ったスマホの画面が1回暗くなる

保存名: `konkatsu-02-dim-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/konkatsu/02-dim/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The hand holds a plain black phone with no logo and does not scroll. The screen is a soft bright blur with no letters, numbers, or pictures of a face.
One action: the screen dims once by itself. The fingers do not tap and do not stop on a region.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 13. `2026-10-13/konkatsu/03-flip-up`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 伏せたスマホを1回表にする

保存名: `konkatsu-03-flip-up-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/konkatsu/03-flip-up/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone with no logo lies face down on the wooden desk. The hand rests beside it.
One action: the hand turns the phone face up once. The screen becomes a soft blur with no letters, numbers, or pictures of a face.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft phone turn, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 14. `2026-10-13/konkatsu/04-beside`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: スマホを無地のノートの横へ1回ずらす

保存名: `konkatsu-04-beside-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/konkatsu/04-beside/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A blank notebook with no handwriting and no printed letters lies on the desk. A plain black phone with no logo sits apart from it. The screen is a soft blur with no letters, numbers, or pictures of a face.
One action: the hand slides the phone once so it rests beside the notebook.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft slide, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 15. `2026-10-13/konkatsu/05-regrip`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 左手が入り、両手でスマホを1回持ち直す

保存名: `konkatsu-05-regrip-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/konkatsu/05-regrip/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The right hand holds a plain black phone with no logo. The screen is a soft blur with no letters, numbers, or pictures of a face. The left hand is not in frame yet.
One action: the left hand enters and both hands regrip the phone once. The left hand matches: adult, short bare nails, no polish, no rings. No face.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft regrip, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 16. `2026-10-13/konkatsu/06-lamp`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: スマホをランプの光の下へ1回滑らせる

保存名: `konkatsu-06-lamp-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/konkatsu/06-lamp/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The plain black phone sits on the dimmer side of the desk. A warm lamp glows at the edge of the frame. The screen is a soft blur with no letters, numbers, or pictures of a face.
One action: the hand slides the phone once into the lamp light.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft slide, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 17. `2026-10-13/konkatsu/07-cable`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 無地のケーブルをスマホから1回外す

保存名: `konkatsu-07-cable-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/konkatsu/07-cable/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain dark cable with no logo is plugged into the bottom of a plain black phone. The screen is black, with no letters, numbers, or pictures of a face. The hand is near the plug.
One action: the hand unplugs the cable once.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft unplug, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 18. `2026-10-13/konkatsu/08-corner`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 無地のケースの角を指で1回なぞる

保存名: `konkatsu-08-corner-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/konkatsu/08-corner/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone in a plain dark case with no logo lies on the desk. The screen is a soft blur with no letters, numbers, or pictures of a face.
One action: one finger traces one corner of the case once. The finger does not touch the glass.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft trace, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 19. `2026-10-13/konkatsu/09-under`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: スマホを無地のノートの下へ1回滑らせる

保存名: `konkatsu-09-under-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/konkatsu/09-under/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A blank notebook with no handwriting and no printed letters lies above a plain black phone. The phone is still visible. The screen is a soft blur with no letters, numbers, or pictures of a face.
One action: the hand slides the phone once under the notebook until only the notebook shows.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft slide, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 20. `2026-10-13/konkatsu/10-set-dark`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 画面が消えたスマホを机に1回置く

保存名: `konkatsu-10-set-dark-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/konkatsu/10-set-dark/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The hand holds a plain black phone. The screen is already black, with no letters, numbers, or pictures of a face.
One action: the hand sets the already-dark phone flat on the desk once. The screen stays black.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 21. `2026-10-14/konkatsu/01-palm`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 手のひらを机に1回伏せる

保存名: `konkatsu-01-palm-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/konkatsu/01-palm/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The right hand is open above the wooden desk, palm toward the lamp. A plain black phone with no logo lies beside the hand. The screen is a soft blur with no letters, numbers, or a face.
One action: the hand turns palm-down onto the desk once and stays. The fingers do not tap the phone.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft palm on wood, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 22. `2026-10-14/konkatsu/02-cuff`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: グレーの袖口を1回直す

保存名: `konkatsu-02-cuff-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/konkatsu/02-cuff/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The right hand rests beside a plain black phone with no logo. The screen is a soft blur with no letters, numbers, or a face. The plain gray cuff is slightly folded.
One action: the same hand straightens the gray cuff once. The phone is not touched.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft cloth shift, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 23. `2026-10-14/konkatsu/03-push`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 机のスマホを奥へ1回押す

保存名: `konkatsu-03-push-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/konkatsu/03-push/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone with no logo lies flat on the wooden desk, closer to the camera. The screen is a soft blur with no letters, numbers, or a face. The right hand rests at the near edge of the phone. No notebook is in frame.
One action: the hand pushes the phone once farther from the camera, along the desk, and stops. The phone does not go under a notebook and does not slide under the lamp. The screen stays an unreadable blur.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft slide on wood, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 24. `2026-10-14/konkatsu/04-pinch`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: スマホの縁を2本の指で1回挟む

保存名: `konkatsu-04-pinch-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/konkatsu/04-pinch/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone with no logo lies flat on the desk. The screen is a soft blur with no letters, numbers, or a face.
One action: the thumb and index finger pinch the phone bezel once, then release. They do not tap the screen. The screen stays a blur.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft pinch, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 25. `2026-10-14/konkatsu/05-spin`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 机のスマホを1回回す

保存名: `konkatsu-05-spin-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/konkatsu/05-spin/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone with no logo lies flat on the desk. The screen is a soft blur with no letters, numbers, or a face.
One action: the hand rotates the phone once on the desk and stops. The screen stays an unreadable blur. No letters appear.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft turn on wood, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 26. `2026-10-14/konkatsu/06-hover`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 人差し指が画面の上で1回止まり、触れない

保存名: `konkatsu-06-hover-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/konkatsu/06-hover/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The right hand holds a plain black phone with no logo. The screen is a soft blur with no letters, numbers, or a face. The index finger is above the glass.
One action: the index finger stops once above the screen and does not touch the glass.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 27. `2026-10-14/konkatsu/07-coaster`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 無地のコースターをスマホの下へ1回敷く

保存名: `konkatsu-07-coaster-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/konkatsu/07-coaster/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone with no logo lies on the wooden desk. The screen is a soft blur with no letters, numbers, or a face. The right hand holds a plain round matte coaster with no letters and no logo.
One action: the hand slides the plain coaster under the phone once and stops. No letters appear on the coaster.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft slide, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 28. `2026-10-14/konkatsu/08-left`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 左手を机に1回置く

保存名: `konkatsu-08-left-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/konkatsu/08-left/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
The right hand already rests beside a plain black phone with no logo. The screen is a soft blur with no letters, numbers, or a face. The left hand is entering from the side, with short bare nails and no rings.
One action: the left hand rests flat on the desk once and stays. It does not take the phone and does not regrip it.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft hand on wood, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 29. `2026-10-14/konkatsu/09-shade`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: ランプの傘を1回回す

保存名: `konkatsu-09-shade-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/konkatsu/09-shade/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A small warm lamp stands on the desk. A plain black phone with no logo lies away from the lamp. The screen is a soft blur with no letters, numbers, or a face.
One action: the hand turns the lamp shade once. The lamp body does not slide. The phone stays where it is. The screen stays a blur.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft turn of the shade, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 30. `2026-10-14/konkatsu/10-stand`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 机のスマホを縁で1回立てる

保存名: `konkatsu-10-stand-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/konkatsu/10-stand/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, night desk, warm lamp.
Reference image REF-KON-HAND, attach the same still on every shot: one adult right hand, short bare nails, no polish, no rings, plain gray cuff at the wrist. The face, hair, and any other person stay out of frame. Do not redesign the hand.
A plain black phone with no logo lies flat on the desk. The screen is a soft blur with no letters, numbers, or a face.
One action: the hand stands the phone on its edge once and lets go. The screen stays an unreadable blur. No letters, numbers, or faces appear.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face anywhere in the frame.
Sound: one soft set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

## 美容

### 31. `2026-10-12/beauty/01-frost-slim`

絵の合計: 12秒。ショット 4 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: すりガラスのポンプを持って止まる

保存名: `beauty-01-frost-slim-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/01-frost-slim/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands hold a matte frosted pump bottle with no label still above the shelf.
One action: the hands hold that bottle still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（4秒、2–6秒）

動作: 手の甲に1回つける

保存名: `beauty-01-frost-slim-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/01-frost-slim/imagine/shot-02.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
a matte frosted pump bottle with no label is in one hand.
One action: the other hand receives one dab on the back of the hand.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft dab, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（2秒、6–8秒）

動作: 細い瓶に持ち替える

保存名: `beauty-01-frost-slim-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/01-frost-slim/imagine/shot-03.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands are on a matte frosted pump bottle with no label.
One action: the hands move once from the first bottle onto a slim clear bottle with a plain white cap and no label.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame. No third bottle.
Sound: one soft bottle set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-04.mp4（4秒、8–12秒）

動作: 手の甲に1回つける

保存名: `beauty-01-frost-slim-shot-04.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/01-frost-slim/imagine/shot-04.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
a slim clear bottle with a plain white cap and no label is in one hand.
One action: the other hand receives one dab on the back of the hand.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft dab, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 32. `2026-10-12/beauty/02-dropper-pump`

絵の合計: 12秒。ショット 4 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: スポイト瓶を持って止まる

保存名: `beauty-02-dropper-pump-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/02-dropper-pump/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands hold a small glass dropper bottle with no label still above the shelf.
One action: the hands hold that bottle still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（4秒、2–6秒）

動作: 手の甲に1回つける

保存名: `beauty-02-dropper-pump-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/02-dropper-pump/imagine/shot-02.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
a small glass dropper bottle with no label is in one hand.
One action: the other hand receives one dab on the back of the hand.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft dab, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（2秒、6–8秒）

動作: 短いポンプに持ち替える

保存名: `beauty-02-dropper-pump-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/02-dropper-pump/imagine/shot-03.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands are on a small glass dropper bottle with no label.
One action: the hands move once from the first bottle onto a short pump bottle with no label.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame. No third bottle.
Sound: one soft bottle set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-04.mp4（4秒、8–12秒）

動作: 手の甲に1回つける

保存名: `beauty-02-dropper-pump-shot-04.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/02-dropper-pump/imagine/shot-04.mp4`

```text
Duration: 4 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
a short pump bottle with no label is in one hand.
One action: the other hand receives one dab on the back of the hand.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft dab, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 33. `2026-10-12/beauty/03-hand`

絵の合計: 12秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: 右手の甲の近い画で止まる

保存名: `beauty-03-hand-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/03-hand/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
Frame shows the back of the right hand only. An unlabeled pump bottle waits at the edge of the shelf.
One action: the skin site rests still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（5秒、2–7秒）

動作: 右手の甲に1回だけ塗る

保存名: `beauty-03-hand-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/03-hand/imagine/shot-02.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands, same unlabeled pump bottle. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
Frame shows the back of the right hand.
One action: the fingers apply the bottle once onto that site.
One camera move: the camera pushes in once, slowly, and does not pan or tilt.
No face in frame. No before-and-after change of the skin.
Sound: one soft apply, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（5秒、7–12秒）

動作: 塗る前と同じ画角で止まる

保存名: `beauty-03-hand-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/03-hand/imagine/shot-03.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up matching the first shot's framing. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
Frame shows the back of the right hand again. The unlabeled pump bottle is back at the edge of the shelf.
One action: the hand rests still beside the site.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame. The skin is not presented as changed.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 34. `2026-10-12/beauty/04-forearm`

絵の合計: 12秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: 前腕の近い画で止まる

保存名: `beauty-04-forearm-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/04-forearm/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
Frame shows the inner forearm, wrist to elbow, no face only. An unlabeled pump bottle waits at the edge of the shelf.
One action: the skin site rests still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（5秒、2–7秒）

動作: 前腕に1回だけ塗る

保存名: `beauty-04-forearm-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/04-forearm/imagine/shot-02.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands, same unlabeled pump bottle. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
Frame shows the inner forearm, wrist to elbow, no face.
One action: the fingers apply the bottle once onto that site.
One camera move: the camera pushes in once, slowly, and does not pan or tilt.
No face in frame. No before-and-after change of the skin.
Sound: one soft apply, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（5秒、7–12秒）

動作: 塗る前と同じ画角で止まる

保存名: `beauty-04-forearm-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/04-forearm/imagine/shot-03.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up matching the first shot's framing. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
Frame shows the inner forearm, wrist to elbow, no face again. The unlabeled pump bottle is back at the edge of the shelf.
One action: the hand rests still beside the site.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame. The skin is not presented as changed.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 35. `2026-10-12/beauty/05-wrist`

絵の合計: 12秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: 手首の近い画で止まる

保存名: `beauty-05-wrist-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/05-wrist/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
Frame shows the top of one wrist only. An unlabeled pump bottle waits at the edge of the shelf.
One action: the skin site rests still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（5秒、2–7秒）

動作: 手首に1回だけ塗る

保存名: `beauty-05-wrist-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/05-wrist/imagine/shot-02.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands, same unlabeled pump bottle. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
Frame shows the top of one wrist.
One action: the fingers apply the bottle once onto that site.
One camera move: the camera pushes in once, slowly, and does not pan or tilt.
No face in frame. No before-and-after change of the skin.
Sound: one soft apply, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（5秒、7–12秒）

動作: 塗る前と同じ画角で止まる

保存名: `beauty-05-wrist-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/05-wrist/imagine/shot-03.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up matching the first shot's framing. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
Frame shows the top of one wrist again. The unlabeled pump bottle is back at the edge of the shelf.
One action: the hand rests still beside the site.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame. The skin is not presented as changed.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 36. `2026-10-12/beauty/06-other-hand`

絵の合計: 12秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: 左手の甲の近い画で止まる

保存名: `beauty-06-other-hand-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/06-other-hand/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
Frame shows the back of the left hand only. An unlabeled pump bottle waits at the edge of the shelf.
One action: the skin site rests still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（5秒、2–7秒）

動作: 左手の甲に1回だけ塗る

保存名: `beauty-06-other-hand-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/06-other-hand/imagine/shot-02.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands, same unlabeled pump bottle. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
Frame shows the back of the left hand.
One action: the fingers apply the bottle once onto that site.
One camera move: the camera pushes in once, slowly, and does not pan or tilt.
No face in frame. No before-and-after change of the skin.
Sound: one soft apply, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（5秒、7–12秒）

動作: 塗る前と同じ画角で止まる

保存名: `beauty-06-other-hand-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/06-other-hand/imagine/shot-03.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up matching the first shot's framing. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
Frame shows the back of the left hand again. The unlabeled pump bottle is back at the edge of the shelf.
One action: the hand rests still beside the site.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame. The skin is not presented as changed.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 37. `2026-10-12/beauty/07-extra-bottle`

絵の合計: 12秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: もう1本のポンプを持って止まる

保存名: `beauty-07-extra-bottle-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/07-extra-bottle/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands hold a second unlabeled pump bottle still. a slim clear bottle with a plain white cap and no label already sits on the shelf.
One action: the hands hold the item still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（5秒、2–7秒）

動作: もう1本のポンプを机の外へ1回動かす

保存名: `beauty-07-extra-bottle-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/07-extra-bottle/imagine/shot-02.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
One action: the hands move a second unlabeled pump bottle off the shelf in one motion.
One camera move: the camera stays locked and does not follow the item.
No face in frame.
Sound: one soft slide, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（5秒、7–12秒）

動作: 残った1本だけが棚にある

保存名: `beauty-07-extra-bottle-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/07-extra-bottle/imagine/shot-03.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of the same night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands leave the frame. Only a slim clear bottle with a plain white cap and no label remains on the shelf.
One action: the hands leave the frame.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame. No second product remains.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 38. `2026-10-12/beauty/08-cotton`

絵の合計: 12秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: コットンを持って止まる

保存名: `beauty-08-cotton-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/08-cotton/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands hold a plain stack of white cotton pads with no printing still. an unlabeled pump bottle already sits on the shelf.
One action: the hands hold the item still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（5秒、2–7秒）

動作: コットンを机の外へ1回動かす

保存名: `beauty-08-cotton-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/08-cotton/imagine/shot-02.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
One action: the hands move a plain stack of white cotton pads with no printing off the shelf in one motion.
One camera move: the camera stays locked and does not follow the item.
No face in frame.
Sound: one soft slide, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（5秒、7–12秒）

動作: 残った1本だけが棚にある

保存名: `beauty-08-cotton-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/08-cotton/imagine/shot-03.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of the same night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands leave the frame. Only an unlabeled pump bottle remains on the shelf.
One action: the hands leave the frame.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame. No second product remains.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 39. `2026-10-12/beauty/09-pouch`

絵の合計: 12秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: パックの袋を持って止まる

保存名: `beauty-09-pouch-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/09-pouch/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands hold one plain sealed pouch with no printing still. an unlabeled pump bottle already sits on the shelf.
One action: the hands hold the item still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（5秒、2–7秒）

動作: パックの袋を机の外へ1回動かす

保存名: `beauty-09-pouch-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/09-pouch/imagine/shot-02.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
One action: the hands move one plain sealed pouch with no printing off the shelf in one motion.
One camera move: the camera stays locked and does not follow the item.
No face in frame.
Sound: one soft slide, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（5秒、7–12秒）

動作: 残った1本だけが棚にある

保存名: `beauty-09-pouch-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/09-pouch/imagine/shot-03.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of the same night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands leave the frame. Only an unlabeled pump bottle remains on the shelf.
One action: the hands leave the frame.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame. No second product remains.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 40. `2026-10-12/beauty/10-dish`

絵の合計: 12秒。ショット 3 本。

#### imagine/shot-01.mp4（2秒、0–2秒）

動作: 小皿を持って止まる

保存名: `beauty-10-dish-shot-01.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/10-dish/imagine/shot-01.mp4`

```text
Duration: 2 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands hold one small empty ceramic dish still. a small glass dropper bottle with no label already sits on the shelf.
One action: the hands hold the item still.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-02.mp4（5秒、2–7秒）

動作: 小皿を机の外へ1回動かす

保存名: `beauty-10-dish-shot-02.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/10-dish/imagine/shot-02.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up, same night shelf, same hands. Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
One action: the hands move one small empty ceramic dish off the shelf in one motion.
One camera move: the camera stays locked and does not follow the item.
No face in frame.
Sound: one soft slide, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

#### imagine/shot-03.mp4（5秒、7–12秒）

動作: 残った1本だけが棚にある

保存名: `beauty-10-dish-shot-03.mp4`

ファイル: `shorts-stock/2026-10-12/beauty/10-dish/imagine/shot-03.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of the same night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands leave the frame. Only a small glass dropper bottle with no label remains on the shelf.
One action: the hands leave the frame.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame. No second product remains.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 41. `2026-10-13/beauty/01-cap`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 細い瓶の白いキャップを1回閉める

保存名: `beauty-01-cap-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/beauty/01-cap/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
A slim clear bottle with a plain white cap sits open on the dark wood shelf. The cap is in one hand. A matte frosted pump bottle with no label stands beside it. No third bottle.
One action: the hands close the white cap onto the slim bottle once.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft cap click, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 42. `2026-10-13/beauty/02-pump`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: すりガラスのポンプの頭を1回押して戻す

保存名: `beauty-02-pump-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/beauty/02-pump/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands hold a matte frosted pump bottle with no label above the shelf, away from skin. A slim clear bottle with a plain white cap and no label stands on the shelf. No third bottle.
One action: one finger presses the pump head once. No liquid appears. Nothing lands on skin.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft pump click, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 43. `2026-10-13/beauty/03-align`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 棚の2本を奥へ1回揃える

保存名: `beauty-03-align-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/beauty/03-align/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
A matte frosted pump bottle and a slim clear bottle with a plain white cap sit a little apart on the dark wood shelf. Both have no labels. The hands rest at the sides. No third bottle.
One action: the hands push both bottles once toward the back of the shelf so they sit in one line. Both bottles stay on the shelf.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft slide of glass, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 44. `2026-10-13/beauty/04-lamp`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 小さなランプを瓶の横へ1回寄せる

保存名: `beauty-04-lamp-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/beauty/04-lamp/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
A small warm lamp sits at the far end of the dark wood shelf. The matte frosted pump and the slim clear bottle with a plain white cap stand in dimmer light. No labels. No third bottle.
One action: the hands slide the lamp once closer to the two bottles.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft lamp slide, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 45. `2026-10-13/beauty/05-wipe`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 無地の布で棚の木を1回拭く

保存名: `beauty-05-wipe-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/beauty/05-wipe/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The two unlabeled bottles stay on the dark wood shelf. The hands hold a plain gray cloth, not a cotton pad. No labels. No third bottle.
One action: the hands wipe the wood once in front of the bottles. The bottles do not move.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft cloth wipe, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 46. `2026-10-13/beauty/06-turn`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: すりガラスの瓶を1回回す

保存名: `beauty-06-turn-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/beauty/06-turn/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The hands rest on a matte frosted pump bottle with no label. The slim clear bottle with a plain white cap stands beside it. No third bottle.
One action: the hands rotate the frosted bottle one quarter turn. No label appears.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft turn of glass, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 47. `2026-10-13/beauty/07-cap-down`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 外してある白いキャップを棚に1回置く

保存名: `beauty-07-cap-down-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/beauty/07-cap-down/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The slim clear bottle stands open on the shelf. Its plain white cap is already off, held above the shelf. The matte frosted pump stands beside it. No labels. No third bottle.
One action: the hands set the cap down once beside the slim bottle. They do not put the cap back on.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft cap set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 48. `2026-10-13/beauty/08-pinch`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 細い瓶の腹を2本の指で1回挟む

保存名: `beauty-08-pinch-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/beauty/08-pinch/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
A slim clear bottle with a plain white cap and no label stands on the shelf. The matte frosted pump stands beside it. The hands are near the slim bottle. No third bottle.
One action: two fingers pinch the body of the slim bottle once. The bottle stays on the shelf.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft pinch, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 49. `2026-10-13/beauty/09-shadow`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 手をランプと瓶の間で1回止めて影を落とす

保存名: `beauty-09-shadow-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/beauty/09-shadow/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The two unlabeled bottles stand in the small lamp's light. The hands are outside the light. No third bottle.
One action: one hand moves once between the lamp and the bottles, so a shadow falls on the bottles.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 50. `2026-10-13/beauty/10-tilt`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: すりガラスの瓶をランプの方へ1回傾けて止める

保存名: `beauty-10-tilt-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/beauty/10-tilt/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
A matte frosted pump bottle with no label stands upright on the shelf. The slim clear bottle with a plain white cap stands beside it. The small warm lamp is to one side. No third bottle.
One action: the hands tilt the frosted bottle once toward the lamp. Nothing pours.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft tilt, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 51. `2026-10-14/beauty/01-return`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: ずらしてあるすりガラスのポンプを元の位置へ1回戻す

保存名: `beauty-01-return-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/beauty/01-return/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
A matte frosted pump bottle with no label sits slightly aside on the dark wood shelf. A slim clear bottle with a plain white cap stands in its place. No third bottle.
One action: the hands slide the frosted pump back to its place once and stop. They do not press the pump.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft slide on wood, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 52. `2026-10-14/beauty/02-lift-cap`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 細い瓶の白いキャップを1回持ち上げて止める

保存名: `beauty-02-lift-cap-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/beauty/02-lift-cap/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
A slim clear bottle with a plain white cap sits closed on the shelf. A matte frosted pump bottle with no label stands beside it. No third bottle.
One action: the hands lift the white cap off the slim bottle once and hold it. They do not close it again and do not set it on the shelf.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft cap lift, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 53. `2026-10-14/beauty/03-gap`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 並んだ2本の間隔を1回あける

保存名: `beauty-03-gap-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/beauty/03-gap/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
A matte frosted pump bottle and a slim clear bottle with a plain white cap sit close together on the shelf. Both are unlabeled. No third bottle.
One action: the hands move the slim bottle once so the gap between the two bottles is wider, then stop. No measured distance is shown.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft slide on wood, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 54. `2026-10-14/beauty/04-lamp-back`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 瓶の横にあるランプを奥へ1回戻す

保存名: `beauty-04-lamp-back-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/beauty/04-lamp-back/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The small warm lamp sits close beside the two unlabeled bottles: a matte frosted pump and a slim clear bottle with a plain white cap. No third bottle.
One action: the hands move the lamp once farther back on the shelf and stop. The bottles stay where they are.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft slide, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 55. `2026-10-14/beauty/05-cap-wipe`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 無地の布で白いキャップの上面を1回拭く

保存名: `beauty-05-cap-wipe-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/beauty/05-cap-wipe/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The slim clear bottle stands with its plain white cap on. A matte frosted pump bottle stands beside it. One hand holds a plain cloth with no pattern and no logo. No third bottle.
One action: the cloth wipes the top of the white cap once and stops. It does not wipe the wood.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft wipe, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 56. `2026-10-14/beauty/06-upright`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 傾いている細い瓶を1回立てる

保存名: `beauty-06-upright-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/beauty/06-upright/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
The slim clear bottle with a plain white cap leans on the shelf. The matte frosted pump bottle stands upright beside it. No third bottle.
One action: the hands stand the slim bottle upright once and stop. They do not tilt it toward the lamp.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft set-down, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 57. `2026-10-14/beauty/07-palm`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 手のひらを棚の木に1回置く

保存名: `beauty-07-palm-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/beauty/07-palm/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
A matte frosted pump bottle and a slim clear bottle with a plain white cap stand on the shelf. Both are unlabeled. No third bottle. One palm is above the wood, beside the bottles.
One action: the palm rests flat on the dark wood once and stays. No product leaves either bottle. The hand does not dab skin.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft palm on wood, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 58. `2026-10-14/beauty/08-swap`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 棚の2本の位置を1回入れ替える

保存名: `beauty-08-swap-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/beauty/08-swap/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
A matte frosted pump bottle stands on the left. A slim clear bottle with a plain white cap stands on the right. Both are unlabeled. No third bottle.
One action: the hands swap the places of the two bottles once and stop.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: two soft set-downs, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 59. `2026-10-14/beauty/09-nozzle`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: ポンプの口を横へ1回向ける

保存名: `beauty-09-nozzle-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/beauty/09-nozzle/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
A matte frosted pump bottle stands with its nozzle pointing forward. A slim clear bottle with a plain white cap stands beside it. Both are unlabeled. No third bottle.
One action: the hands turn only the pump nozzle once so it points sideways, then stop. They do not press the pump. The bottle body does not spin.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft click of the nozzle, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 60. `2026-10-14/beauty/10-fold`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 瓶の横の無地の布を1回畳む

保存名: `beauty-10-fold-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/beauty/10-fold/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal close-up of hands at a night shelf. A dark wood shelf at night, one small warm lamp, no labels, no letters, no logos.
Reference image REF-NIGHT-HANDS, attach the same still on every shot: adult hands only, short bare nails, no polish, no rings, no watch, no bracelets. The face, hair, and body above the wrists stay out of frame. Do not redesign the hands.
A plain cloth with no pattern and no logo lies open beside the two unlabeled bottles: a matte frosted pump and a slim clear bottle with a plain white cap. No third bottle.
One action: the hands fold the plain cloth once and stop. They do not wipe the shelf or the bottles.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
No face in frame.
Sound: one soft fold of cloth, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

## ペット

### 61. `2026-10-13/pet/01-gray-blink`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: グレーのマンチカンがソファでまばたきを1回する

保存名: `pet-01-gray-blink-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/pet/01-gray-blink/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed high corner camera aimed at the sofa. Night, dark living room, no clock overlay.
Reference image REF-GRAY, attach the same still on every shot: one adult gray munchkin, solid blue-gray short fur, no stripes, no white patches, short legs, round head, upright open ears, amber eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The gray munchkin sits on a low beige sofa in a dark living room. Eyes are open.
One action: the cat blinks once, slowly, on the sofa.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 62. `2026-10-13/pet/02-white-yawn`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 白いスコティッシュフォールドがラグで欠伸を1回する

保存名: `pet-02-white-yawn-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/pet/02-white-yawn/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed low corner camera aimed at the rug. Same dark living room, no clock overlay.
Reference image REF-WHITE, attach the same still on every shot: one adult white Scottish fold, solid white short fur, folded ears, round face, copper eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The white Scottish fold sits on a plain sand-colored rug. Mouth is closed.
One action: the cat yawns once on the rug.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft yawn, then room tone. No words.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 63. `2026-10-13/pet/03-gray-lick`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: グレーのマンチカンがソファで前足を1回なめる

保存名: `pet-03-gray-lick-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/pet/03-gray-lick/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed high corner camera aimed at the sofa. Night, dark living room, no clock overlay.
Reference image REF-GRAY, attach the same still on every shot: one adult gray munchkin, solid blue-gray short fur, no stripes, no white patches, short legs, round head, upright open ears, amber eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The gray munchkin sits on a low beige sofa. Both front paws are down.
One action: the cat licks one front paw once.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft lick, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 64. `2026-10-13/pet/04-white-ear`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 白いスコティッシュフォールドがソファで耳を1回動かす

保存名: `pet-04-white-ear-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/pet/04-white-ear/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed high corner camera aimed at the sofa. Night, dark living room, no clock overlay.
Reference image REF-WHITE, attach the same still on every shot: one adult white Scottish fold, solid white short fur, folded ears, round face, copper eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The white Scottish fold sits on a low beige sofa. Folded ears are still.
One action: one folded ear twitches once.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 65. `2026-10-13/pet/05-gray-paw`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: グレーのマンチカンがラグの上で前足を前へ1回伸ばす

保存名: `pet-05-gray-paw-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/pet/05-gray-paw/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed low corner camera aimed at the rug. Same dark living room, no clock overlay.
Reference image REF-GRAY, attach the same still on every shot: one adult gray munchkin, solid blue-gray short fur, no stripes, no white patches, short legs, round head, upright open ears, amber eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The gray munchkin sits on a plain sand-colored rug. Front paws are close to the chest.
One action: the cat extends one front paw forward along the rug, away from the lens.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft paw on the rug, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 66. `2026-10-13/pet/06-white-tail`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 白いスコティッシュフォールドがラグでしっぽの先を1回振る

保存名: `pet-06-white-tail-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/pet/06-white-tail/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed low corner camera aimed at the rug. Same dark living room, no clock overlay.
Reference image REF-WHITE, attach the same still on every shot: one adult white Scottish fold, solid white short fur, folded ears, round face, copper eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The white Scottish fold sits on a plain sand-colored rug. The tail lies still on the rug.
One action: the tip of the tail flicks once on the rug.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft tail brush, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 67. `2026-10-13/pet/07-gray-loaf`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: グレーのマンチカンがソファで両前足を腹の下にしまう

保存名: `pet-07-gray-loaf-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/pet/07-gray-loaf/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed high corner camera aimed at the sofa. Night, dark living room, no clock overlay.
Reference image REF-GRAY, attach the same still on every shot: one adult gray munchkin, solid blue-gray short fur, no stripes, no white patches, short legs, round head, upright open ears, amber eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The gray munchkin sits upright on a low beige sofa. Both front paws are visible.
One action: the cat draws both front paws under its chest and stays upright.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft shift on the cushion, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 68. `2026-10-13/pet/08-white-window`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 白いスコティッシュフォールドがソファで窓の方へ顔を1回向ける

保存名: `pet-08-white-window-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/pet/08-white-window/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed high corner camera aimed at the sofa. Night, dark living room, no clock overlay.
Reference image REF-WHITE, attach the same still on every shot: one adult white Scottish fold, solid white short fur, folded ears, round face, copper eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The white Scottish fold sits on a low beige sofa. Its face is toward the cushion, not the lens. A dark window is at the side of the room.
One action: the cat turns its head once toward the dark window. The eyes do not aim at the lens.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 69. `2026-10-13/pet/09-gray-sniff`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: グレーのマンチカンがラグに鼻を1回近づける

保存名: `pet-09-gray-sniff-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/pet/09-gray-sniff/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed low corner camera aimed at the rug. Same dark living room, no clock overlay.
Reference image REF-GRAY, attach the same still on every shot: one adult gray munchkin, solid blue-gray short fur, no stripes, no white patches, short legs, round head, upright open ears, amber eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The gray munchkin sits on a plain sand-colored rug. Its head is up.
One action: the cat sniffs the rug once.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft sniff, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 70. `2026-10-13/pet/10-white-chin`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 白いスコティッシュフォールドがラグであごを前足の上に乗せる

保存名: `pet-10-white-chin-shot-01.mp4`

ファイル: `shorts-stock/2026-10-13/pet/10-white-chin/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed low corner camera aimed at the rug. Same dark living room, no clock overlay.
Reference image REF-WHITE, attach the same still on every shot: one adult white Scottish fold, solid white short fur, folded ears, round face, copper eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The white Scottish fold sits on a plain sand-colored rug. Its chin is up.
One action: the cat lowers its chin onto one front paw.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft settle, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 71. `2026-10-14/pet/01-gray-paws`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: グレーのマンチカンがソファで自分の前足を1回見る

保存名: `pet-01-gray-paws-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/pet/01-gray-paws/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed high corner camera aimed at the sofa. Night, dark living room, no clock overlay.
Reference image REF-GRAY, attach the same still on every shot: one adult gray munchkin, solid blue-gray short fur, no stripes, no white patches, short legs, round head, upright open ears, amber eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The gray munchkin sits on a low beige sofa. Both front paws rest on the cushion, in front of the chest.
One action: the cat looks down at its own front paws once, then holds still. It does not blink as the action, and it does not reach the camera.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 72. `2026-10-14/pet/02-white-side`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 白いスコティッシュフォールドがラグで顔を横へ1回向ける

保存名: `pet-02-white-side-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/pet/02-white-side/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed low corner camera aimed at the rug. Same dark living room, no clock overlay.
Reference image REF-WHITE, attach the same still on every shot: one adult white Scottish fold, solid white short fur, folded ears, round face, copper eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The white Scottish fold sits on a plain sand-colored rug. Its face starts toward the rug, not the lens. No window is the target.
One action: the cat turns its head once to the side and stops. The eyes do not aim at the lens and do not aim at a window.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 73. `2026-10-14/pet/03-gray-wrap`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: グレーのマンチカンがラグでしっぽを体に1回巻く

保存名: `pet-03-gray-wrap-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/pet/03-gray-wrap/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed low corner camera aimed at the rug. Same dark living room, no clock overlay.
Reference image REF-GRAY, attach the same still on every shot: one adult gray munchkin, solid blue-gray short fur, no stripes, no white patches, short legs, round head, upright open ears, amber eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The gray munchkin sits on a plain sand-colored rug. The tail lies beside the body, not yet around it.
One action: the cat wraps its tail once around its own body and stops. The tail tip does not wag.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft shift of fur, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 74. `2026-10-14/pet/04-white-stack`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 白いスコティッシュフォールドがソファで前足を1回重ねる

保存名: `pet-04-white-stack-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/pet/04-white-stack/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed high corner camera aimed at the sofa. Night, dark living room, no clock overlay.
Reference image REF-WHITE, attach the same still on every shot: one adult white Scottish fold, solid white short fur, folded ears, round face, copper eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The white Scottish fold sits on a low beige sofa. Both front paws rest apart on the cushion.
One action: the cat sets one front paw on top of the other once and stays. It does not tuck both paws under the chest.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft shift on the cushion, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 75. `2026-10-14/pet/05-gray-lift`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: グレーのマンチカンがソファで顔を1回上げる

保存名: `pet-05-gray-lift-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/pet/05-gray-lift/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed high corner camera aimed at the sofa. Night, dark living room, no clock overlay.
Reference image REF-GRAY, attach the same still on every shot: one adult gray munchkin, solid blue-gray short fur, no stripes, no white patches, short legs, round head, upright open ears, amber eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The gray munchkin sits on a low beige sofa. The head starts lowered toward the cushion. The eyes are not on the lens.
One action: the cat raises its head once and stops. The eyes do not aim at the lens.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 76. `2026-10-14/pet/06-white-chest`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 白いスコティッシュフォールドがラグで胸を1回なめる

保存名: `pet-06-white-chest-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/pet/06-white-chest/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed low corner camera aimed at the rug. Same dark living room, no clock overlay.
Reference image REF-WHITE, attach the same still on every shot: one adult white Scottish fold, solid white short fur, folded ears, round face, copper eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The white Scottish fold sits on a plain sand-colored rug. The cat sits upright. The chest is visible. The mouth is closed.
One action: the cat licks its own chest once and stops. It does not lick a paw.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft lick, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 77. `2026-10-14/pet/07-gray-tap`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: グレーのマンチカンがソファのクッションを前足で1回触る

保存名: `pet-07-gray-tap-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/pet/07-gray-tap/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed high corner camera aimed at the sofa. Night, dark living room, no clock overlay.
Reference image REF-GRAY, attach the same still on every shot: one adult gray munchkin, solid blue-gray short fur, no stripes, no white patches, short legs, round head, upright open ears, amber eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The gray munchkin sits on a low beige sofa. One front paw is just above the cushion, close to the body, not toward the camera.
One action: the cat taps the sofa cushion once with that front paw and stops. The paw does not reach the camera.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft tap, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 78. `2026-10-14/pet/08-white-paw-up`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 白いスコティッシュフォールドがソファで前足を1回上げて止める

保存名: `pet-08-white-paw-up-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/pet/08-white-paw-up/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed high corner camera aimed at the sofa. Night, dark living room, no clock overlay.
Reference image REF-WHITE, attach the same still on every shot: one adult white Scottish fold, solid white short fur, folded ears, round face, copper eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The white Scottish fold sits on a low beige sofa. Both front paws start down on the cushion.
One action: the cat lifts one front paw once and holds it. The paw does not stretch forward and does not cover the face.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: quiet room tone only.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 79. `2026-10-14/pet/09-gray-chin`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: グレーのマンチカンがラグであごをラグに1回つける

保存名: `pet-09-gray-chin-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/pet/09-gray-chin/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed low corner camera aimed at the rug. Same dark living room, no clock overlay.
Reference image REF-GRAY, attach the same still on every shot: one adult gray munchkin, solid blue-gray short fur, no stripes, no white patches, short legs, round head, upright open ears, amber eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The gray munchkin sits on a plain sand-colored rug. The cat sits upright. The chin is up. The front paws are not under the chin.
One action: the cat lowers its chin onto the rug once and stops. The chin does not rest on the paws.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft contact with the rug, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```

### 80. `2026-10-14/pet/10-white-hide`

絵の合計: 5秒。ショット 1 本。

#### imagine/shot-01.mp4（5秒、0–5秒）

動作: 白いスコティッシュフォールドがラグで前足を顔の前へ1回置く

保存名: `pet-10-white-hide-shot-01.mp4`

ファイル: `shorts-stock/2026-10-14/pet/10-white-hide/imagine/shot-01.mp4`

```text
Duration: 5 seconds. Vertical 9:16.
Photoreal pet-camera frame from a fixed low corner camera aimed at the rug. Same dark living room, no clock overlay.
Reference image REF-WHITE, attach the same still on every shot: one adult white Scottish fold, solid white short fur, folded ears, round face, copper eyes, no collar. Do not redesign this cat. No second cat, no dog, no human.
The white Scottish fold sits on a plain sand-colored rug. The face starts visible. Both front paws are down.
One action: the cat places one front paw over its face once and stops.
One camera move: the camera stays locked and does not pan, tilt, zoom, or follow.
Sound: one soft shift, then room tone.
No text, subtitles, captions, letters, numbers, logos, brand names, watermarks, buttons, or end cards. No call to action.
No music and no spoken words inside this clip.
```
