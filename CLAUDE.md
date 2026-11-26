# Research 常時ルール

最終更新: 2026-11-27

正: 部隊は3つだけ。取引は廃止。人間が公開判定。Cursorは現場の手。

1. アフィ動画（affi-shorts-agent）
2. CW（cw-work / PAPER_ONLY）
3. コンテンツ倉庫（BOOTH / Steam。箱だけ）

## 常時

- Secrets をファイル・コミット・ログに書くな。GitHub Secrets のみ。
- Threads の post / insight / report cron を戻すな。`refresh_threads_token.yml` と `affiliate_engine_video_judge.yml` は現状維持。
- 数字を発明するな。カタログ円を確定に足すな。
- XM / DX-Lead / Bitget / EA の実発注と live ゲートを起こすな。`xm-trade-engine/` は開くな。
- draft PR #122 をデフォルトへマージするな。
- 新しい総司令を名乗るな。Research を開いて3部隊を混ぜるな。
- 作業前に `NG-LEDGER.md` を読み、同じNGを繰り返すな。新しいNGは報告に書き、台帳に追記する。

## 場面別（必要なときだけ読む）

- 役割の正: `handover/ROLES.md`
- 再開・停止の経緯: `handover/HANDOVER.md`
- 人間が1回だけやること: `handover/HUMAN_ONCE.md`
- affiliate-engine の保守（workflow、アカウント追加、検証）: `affiliate-engine/README.md`
- Bot 命令: `affiliate-engine/docs/grok-bots/HQ_COMMAND.md`（Bot は開けるな）
- Cursor 常時ルール: `.cursor/rules/hq-command.mdc` と `.cursor/rules/upstream-only.mdc` と `.cursor/rules/ng-ledger.mdc`
- NG台帳: `NG-LEDGER.md`

## NG・失敗の記録ルール（ナオミチ決定 2026-11-27 07:11）
原文:「これ全BOTおよび全grokbuildやcursorのAIに伝えてほしいんだけど、NGだったことダメだったことは忘れないように記録させてね。じゃないとまた同じことやるから。」
1. ナオミチにNG・ダメ出しされたこと、検品FAIL、やってはいけなかったことは、その場で /home/box/bots/ng-ledger.md に1行追記する（日付・誰のNGか・何がダメだったか・次からどうするか）。自分の記憶（memory）にも保存する。
2. 作業を始める前に必ず ng-ledger.md を読み、同じNGを繰り返さない。
3. Grok Build と Cursor への指示書には、この節と ng-ledger.md の該当行を末尾に付ける。Grok Build・Cursor自身も、作業中に出たNGを報告に書き、台帳に追記する。
4. 追記ルール（ナオミチ 2026-11-27 07:12 原文:「マジで徹底させて。ちゃんとようやくして整理もさせてね。」）: 台帳は書きっぱなしにしない。各行は1行で要約（何がダメ→次からどうする）。ジャンル別（全体／X／動画／同人・CG／PC・Grok Build／Cursor／その他）の見出しの下に並べ、同じNGは1行にまとめて回数と最新日付を更新する。各botは自分のラインの節を週1回以上見直して整理する。

## Cursor（このリポジトリ）向け
作業前に NG-LEDGER.md を読む。新しいNGは報告に書き、同じファイルに追記する。成人向けの具体的なNGは公開リポに書かず、箱の /home/box/bots/ng-ledger.md のみに書く。アフィリエイトURLは {A8_LINK} のまま。
