# Grok Bot エージェント

**今アプリで作るのは9体。** 一覧と貼るファイルは [CREATE.md](CREATE.md)。

各体に対応ファイルを貼り、続けて **「これだけ読んで」** と言う。そのジャンルのレシピから動画を1本生成する。投稿はしない。

| 増やす単位 | やる / やらない |
|---|---|
| 今 | ジャンル9体を Grok Bot に作る |
| レシピ | `data/genre_video_packets.json` に id を足す。`node src/genre-video-gen.js --write-agents` |
| 将来BOT追加 | 新ジャンル1体。リンクキー22本分のボットは作らない |
| 作らない | 投稿ボット、判定ボット、TikTok/IG専用、サクラ（Issue #54） |

市場と型: [MARKET_AND_KATA.md](MARKET_AND_KATA.md) / `data/video_kata.json`  
生成コマンド: `cd affiliate-engine && node src/genre-video-gen.js --genre ペット --list-kata`

旧 `launch-keys/LIVE-video-*.md` は機能分割の下書き。Grok Bot 上では作らなくてよい。中身は各 `agents/ジャンル_*.md` に入った。
