lane: chrome
imagine: true
review: true
timeout_min: 120

# 夜間ジョブ: 作り直し5本の新素材 konkatsu-n2（Grok Imagine i2v）
手順の本体は `imagine-new5-i2v-20261020.md`（PC: C:\Users\hp\Documents\grokbuild\jobs\ に置く。箱の原本 /home/box/video-unit/grokbuild/imagine-new5-i2v-20261020.md）。この本 **konkatsu-n2** だけを行う。
- 作業フォルダ C:\work\imagine-new5\、保存先 out\imagine-new5-i2v-20261020\konkatsu-n2\。既に採用済みの shot-0N があればそのカットは飛ばす。
- Imagine が固まる・PCが重くなる兆候が出たら即中止し、REPORT.md に「Imagine異常」と時刻を書く（10/20 クラッシュ実績あり）。
- 4カット揃ったら Eagle（http://localhost:41595）に登録できるか試し、結果を書く。

## 共通の決まり（必ず守る）
- 投稿・予約・共有・送信はしない。X には触らない。パスワード・確認コードは打たない。支払いしない。
- `QC-5rules.md` の5チェックを全部通す（元音声に重ねない／字幕と画面を合わせる／崩れた体・絵は使わない／セリフ間は最大1.5秒／通しで見てシーンごとの表を付ける）。
- 声は VOICEVOX **Keita +45%** 固定（行ごとの速め禁止）。
- 画面に数字を出さない（字幕・図・テロップとも）。
- PR表記は**最後の2秒**のエンドカードだけ。本編にCTAを入れない。
- 人物・ペットのカットは **i2v のみ**（参照静止画→カット静止画→動画化）。t2v 禁止。
- 自分以外の grok.exe / ブラウザ / powershell に触らない。Windows を落とさない・再起動しない。
- 15分以上進まない手順は止めて記録し、次へ。人の操作が要る画面は `BLOCKED.png` を撮って終了。
- 終わったら `C:\Users\hp\Documents\grokbuild\out\<このファイル名>\REPORT.md` に、できたもの・NG・ナオミチに見てほしい点を書く。
