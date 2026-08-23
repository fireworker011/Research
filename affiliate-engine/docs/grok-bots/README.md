# Grok Bot エージェント

**今アプリで作るのは9体。** 一覧と貼るファイルは [CREATE.md](CREATE.md)。

各体に `wake/<id>.txt` を **一度だけ** 貼る。以降は GitHub の所定ファイル（ASCII の `agents/pet.md` など）を毎朝 raw で開く。チャットに md 全文を貼り直さなくてよい。投稿はしない。

| 増やす単位 | やる / やらない |
|---|---|
| 今 | ジャンル9体を Grok Bot に作る |
| レシピ | `data/genre_video_packets.json` に id を足す。`node src/genre-video-gen.js --write-agents` |
| 将来BOT追加 | 新ジャンル1体。リンクキー22本分のボットは作らない |
| 作らない | 投稿ボット、判定ボット、TikTok/IG専用、サクラ（Issue #54） |

**毎朝読む:** [FETCH.md](FETCH.md) の raw URL（ASCII の `agents/pet.md` など）。PC不要。  
市場と型: [MARKET_AND_KATA.md](MARKET_AND_KATA.md) / `data/video_kata.json`  
編集仕様: `data/video_production.json`  
生成コマンド: `cd affiliate-engine && node src/genre-video-gen.js --write-agents`

旧 `launch-keys/LIVE-video-*.md` は機能分割の下書き。Grok Bot 上では作らなくてよい。中身は各 `agents/ジャンル_*.md` に入った。
