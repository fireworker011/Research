lane: edge
review: true
requires: 22-queueB-kane-09.md
timeout_min: 45

# 夜間ジョブ: 完成動画を Drive「動画倉庫/00_確認待ち」へアップ
- 対象: C:\Users\hp\Documents\grokbuild\out\*\upload\ にある mp4 と *_scenes_QA.md（QC表が無い mp4 は上げない）。
- 上げ先: Google Drive「動画倉庫」（ID 1ySAza43AknwyYSJItUTGItgyj5qNBTES）の `00_確認待ち`。共有設定は変えない（制限付きのまま）。
- 同名がすでにあれば上書きせず、REPORT.md に書く。上げたものは out\uploaded-YYYYMMDD.txt に1行ずつ記録。
- ログイン切れなら BLOCKED.png を撮って終了（パスワードは打たない）。YouTube・TikTok等には上げない。
- 注意: 1回で上がるのはその時点で揃っている分だけ。残りは翌朝 Grok Bot が箱から追加アップする。

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
