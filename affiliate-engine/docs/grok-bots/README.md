# Grok Bot エージェント

**今アプリで作るのは9体。** 一覧と貼るファイルは [CREATE.md](CREATE.md)。

各体に [PHONE.md](PHONE.md) の文を **スマホから一度だけ** 貼って送る。以降は `agents/<id>.md` と `ledger/<id>.md` を毎朝 raw で開く。全文が同じならスルー。投稿したら [POSTED.md](POSTED.md) を送ってチェックさせる。前日のチェックが無ければ動画を作らせない。量産するな。投稿はしない。

| 増やす単位 | やる / やらない |
|---|---|
| 今 | ジャンル9体を Grok Bot に作る |
| レシピ | `data/genre_video_packets.json` に id を足す。`node src/genre-video-gen.js --write-agents` |
| 将来BOT追加 | 新ジャンル1体。リンクキー22本分のボットは作らない |
| 作らない | 投稿ボット、判定ボット、TikTok/IG専用、サクラ（Issue #54） |

**毎朝読む:** [FETCH.md](FETCH.md) の raw URL（`agents/` と `ledger/`）。全文同じならスルー。  
投稿後: [POSTED.md](POSTED.md)  
市場と型: [MARKET_AND_KATA.md](MARKET_AND_KATA.md) / `data/video_kata.json`  
日次の事実inbox: [research/](research/)（ここでプレイブックは直さない。Cursorが後で読む）  
編集仕様: `data/video_production.json`  
台帳: `data/video_ledger.json`  
生成コマンド: `cd affiliate-engine && node src/genre-video-gen.js --write-agents`

旧 `launch-keys/LIVE-video-*.md` は機能分割の下書き。Grok Bot 上では作らなくてよい。中身は各 `agents/ジャンル_*.md` に入った。
