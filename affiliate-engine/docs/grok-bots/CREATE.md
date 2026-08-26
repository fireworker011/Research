# Grok Bot に今作るエージェント

9体。毎朝読むファイルは `agents/<id>.md` と `ledger/<id>.md`。
スマホから一度貼る文は [PHONE.md](PHONE.md)。投稿後は [POSTED.md](POSTED.md)。
全文同じならスルー。チェック前に次を作るな。量産するな。投稿しない。

| 作る名前 | 毎朝読む | 今の型 | 今生成してよいもの |
|---|---|---|---|
| ジャンル_ペット | agents/pet.md + ledger/pet.md | visual_question, aruaru3 | 条件つき1本（pet_20260801_02） |
| ジャンル_婚活 | agents/konkatsu.md + ledger/konkatsu.md | kiriwake, miruten | 作るな |
| ジャンル_副業 | agents/sidejob.md + ledger/sidejob.md | miruten, yamenai, kiriwake | 作るな |
| ジャンル_美容 | agents/beauty.md + ledger/beauty.md | min_care | 作るな |
| ジャンル_筋トレ | agents/bodymake.md + ledger/bodymake.md | kiriwake, yamenai | 作るな |
| ジャンル_教育 | agents/education.md + ledger/education.md | miruten | 作るな |
| ジャンル_節約 | agents/setsuyaku.md + ledger/setsuyaku.md | kiriwake, miruten | 作るな |
| ジャンル_転職 | agents/tenshoku.md + ledger/tenshoku.md | kiriwake, miruten | 作るな |
| ジャンル_睡眠 | agents/sleep.md + ledger/sleep.md | kiriwake, min_care, miruten | 作るな |

作らない: 動画判定、投稿ボット、TikTok/IG専用、サクラ（Issue #54）、同人/アダアフィ。
