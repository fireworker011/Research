# 矛盾しているルール

2026-10-17 に人間が決めた。決めた項目は、下の文言に揃えた。揃えなかった項目は、引用を残したままにした。

## 1. 投稿本数 — 決定済み

ジャンル体の毎朝ファイル、台帳、PHONE、wake、生成器は次の文にした。台帳が許可していること、未投稿が無いこと、前日の投稿チェックが済んでいることは、元の文のまま残した。

「1チャンネル1日2本まで。2本目は時間を空け、内容を変える。」

- `agents/pet.md` `agents/konkatsu.md` `agents/sidejob.md` `agents/beauty.md` `agents/bodymake.md` `agents/education.md` `agents/setsuyaku.md` `agents/tenshoku.md` `agents/sleep.md`。毎朝、対応するジャンル体が読む。
- `ledger/<id>.md` 9本。毎朝、対応するジャンル体が読む。
- `PHONE.md` と `wake/*.txt`。起動時に1回貼る。

## 2. CTA — 決定済み

ジャンル体、台本係の手順、knowledge の案内、kata は次の文に揃えた。PR表記は残した。

「本編にCTAは入れない。最後の2秒だけ「詳しくはプロフィールのリンク（PR）」を1回、同じ位置に出す。」

- 上の9つの `agents/<id>.md`。毎朝、対応するジャンル体が読む。
- `knowledge/script-skill.md`。読むのは台本係。字幕、テロップ、心の声、登録、商品名、相談の URL、LINE を置かない文は残した。
- `knowledge/README.md`。読むのは台本係と Cursor。
- `research/kata/pet.md` `research/kata/konkatsu.md` `research/kata/beauty.md` `research/kata/irasutoya-kanememo.md`。台本係が script-skill から開く。beauty の「PR表記を省くことはしない」は残した。

## 3. 予約投稿 と 予約 — そのまま

文言は変えていない。

- `COMMON.md` 3行目と16行目。読むのは `archive/launch-keys/` の起動キー。
  - 「どの起動キーを貼っても、これが上位。矛盾したらこちら。」
  - 「- 投稿・予約投稿・固定コメント・いいね・フォロー・DM」
- 9つの `agents/<id>.md`。毎朝、対応するジャンル体が読む。
  - 「- 投稿・予約・固定コメント・いいね・フォロー・DM をするな」
- `PHONE.md` と `wake/*.txt`。起動時に1回貼る。
  - 「投稿するな。予約するな。いいね・フォロー・DMするな。URLを動画の本文・説明・コメントに書くな。」

## 4. raw URL のブランチ — マージ後に確認

ボットが開く URL は、まだ `cursor/video-channel-playbook-e013`。`cursor/grok-bot-research-2026-08-26` にマージしたあと、同じパスが HTTP 200 で開くときだけ差し替える。開かなければ、このブランチ名のままにする。

- `FETCH.md`
  - 「参照ブランチ: `cursor/video-channel-playbook-e013`（マージ後は作業ブランチに合わせる。環境変数 GROK_BOT_REF）」
- `agents/<id>.md`、`agents/ジャンル_*.md`、`wake/*.txt`、`PHONE.md` の raw URL。例:
  - 「https://raw.githubusercontent.com/fireworker011/Research/cursor/video-channel-playbook-e013/affiliate-engine/docs/grok-bots/agents/pet.md」

## 5. リプで教えて と コメントで教えて — そのまま

`archive/recipes/pet.md` の2本は、文言を揃えていない。読むのはジャンル_ペット。

- `pet_20260729_01`: 「うちの子だけかと思ったら意外と『あるある』らしい行動、リプで教えてください。」
- `pet_20260713_02`: 「『あるある』と思ったもの、コメントで教えてください。意外な共通点が見つかるかもしれません。」
