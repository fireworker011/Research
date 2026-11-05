lane: none
review: true
timeout_min: 60

# 夜間ジョブ: queueB フェーズB 仕上げ kane-10（声・字幕・エンドカード・QC）
手順の本体は `rebuild-kane-10-20261019.md` の **フェーズB**（箱の原本 /home/box/video-unit/grokbuild/rebuild-kane-10-20261019.md）。
- セリフ: C:\Users\hp\Documents\grokbuild\lines\kane-10.md（先頭「台本係 確定」を確認。無ければ始めず REPORT.md に書いて終了）。
- 作業フォルダ C:\Users\hp\Documents\grokbuild\rebuild-20261019\kane-10\。
- 完成品 mp4 とシーンごとのQC表 `kane-10_scenes_QA.md` を out\kane-10\upload\ に置く（Drive へは上げない。上げるのは 90-upload ジョブ）。
- ブラウザは使わない。

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
