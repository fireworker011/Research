# 矛盾しているルール

どちらが上かは決めていない。文言は変えていない。決めるのは人間。

## 1. 予約投稿 と 予約

`COMMON.md` は「予約投稿」。ジャンル体の毎朝ファイルは「予約」。スマホに一度貼る文は「予約するな」。

- `COMMON.md` 3行目。読むのは、`archive/launch-keys/` の起動キー（各ファイルが「必読: affiliate-engine/docs/grok-bots/COMMON.md」と書いている）。ジャンル体の毎朝2ファイルには入っていない。
  - 「どの起動キーを貼っても、これが上位。矛盾したらこちら。」
- `COMMON.md` 16行目。読むのは上と同じ起動キー。
  - 「- 投稿・予約投稿・固定コメント・いいね・フォロー・DM」
- `agents/pet.md` `agents/konkatsu.md` `agents/sidejob.md` `agents/beauty.md` `agents/bodymake.md` `agents/education.md` `agents/setsuyaku.md` `agents/tenshoku.md` `agents/sleep.md` の各43行目。毎朝読むのは ジャンル_ペット、ジャンル_婚活、ジャンル_副業、ジャンル_美容、ジャンル_筋トレ、ジャンル_教育、ジャンル_節約、ジャンル_転職、ジャンル_睡眠。
  - 「- 投稿・予約・固定コメント・いいね・フォロー・DM をするな」
- `PHONE.md`（38行目の直後、各ボットの貼り付け文。ペットは40行目）と `wake/pet.txt` `wake/konkatsu.txt` `wake/sidejob.txt` `wake/beauty.txt` `wake/bodymake.txt` `wake/education.txt` `wake/setsuyaku.txt` `wake/tenshoku.txt` `wake/sleep.txt` の17行目。貼るのは起動時の1回。毎朝の所定ファイルではない。
  - 「投稿するな。予約するな。いいね・フォロー・DMするな。URLを動画の本文・説明・コメントに書くな。」

## 2. 最後の2秒の CTA と、本編に CTA を入れない

ジャンル体の編集仕様は、CTA を最後の2秒に1回出す。台本係の手順は、本編に字幕と CTA を入れない。

- 上の9つの `agents/<id>.md` の45行目と77行目。毎朝、対応するジャンル体が読む。
  - 「- CTA は「詳しくはプロフィールのリンク（PR）」1回だけ」
  - 「- CTA「詳しくはプロフィールのリンク（PR）」は最後の 2秒だけ、同じ位置」
- `knowledge/script-skill.md` 36行目。読むのは台本係。
  - 「- 本編に字幕と CTA は入れない。テロップ、心の声、登録、商品名、相談の URL、LINE は置かない。参考動画がテロップでオチを出していても、台本ではそのオチを絵の最初のフレームで見せる。」
- `knowledge/README.md` 40行目。読むのは台本係と Cursor。
  - 「- 本編は字幕なし、CTA なし。根拠は [`../research/2026-10-17-research70.md`](../research/2026-10-17-research70.md)（D の 63-66 と 70 は、この方針と合わないので使わない）。」
- `research/2026-10-17-research70.md` 17行目。読むのは市場リサーチ。台本係は `script-skill.md` からこのファイルへ来る。
  - 「- 63-66, 70 は、本編は字幕なし・CTAなしというナオミチの方針と合わない。」
- `research/kata/pet.md` 9行目、`research/kata/konkatsu.md` 9行目、`research/kata/beauty.md` 9行目、`research/kata/irasutoya-kanememo.md` 11行目。台本係が `script-skill.md` から開く。
  - pet: 「本編は字幕なし・CTAなし。出典のセリフと映像はコピーしない。」
  - konkatsu: 「出典の高倍率は顔出し。テンプレは顔を出さない。本編は字幕なし・CTAなし。出典のセリフはコピーしない。」
  - beauty: 「本編は字幕なし・CTAなし。効能の断定と、PR表記を省くことはしない。出典のセリフはコピーしない。」
  - irasutoya-kanememo: 「本編は字幕なし・CTAなし。出典の絵とセリフはコピーしない。」

## 3. 1日2本 と 1日1本

リサーチメモは「1日2本、時間を空ける」を仮説として残している。ジャンル体と台帳は「1日1本」。

- `research/2026-10-17-research70.md` 26行目。読むのは市場リサーチ。台本係は `script-skill.md` からこのファイルへ来る。
  - 「6. **#6, #15 投稿頻度と投稿時間**: 量産扱いを避けるためのルール（1日2本、時間を空ける）の根拠になる。」
- `research/2026-10-15-anti-massproduced.md` 261行目。台本係が `script-skill.md` と `knowledge/README.md` から開く。
  - 「12. 投稿を1日2本にして時間を空ける。仮説。公式にその数字は無い。実測の同日複数本は、再生0にはなっていない。」
- `knowledge/script-skill.md` 48行目。読むのは台本係。
  - 「- 仮説のまま強要しないもの: 尺を毎回変えること、投稿を1日2本にして時間を空けること、サムネや色を毎回変えること。同メモは、公式にその数字は無い、と書いている。このスキルが必ず変えるのは、構成かテンポ。」
- `research/2026-10-15.md` 34行目。市場リサーチの日次。
  - 「ペット物語の投稿手順にある「1日2本・時間を空ける・内容を変える」のチェックを疑え（10/14に12秒の同ネタ2本が3分差で出て、片方は189回）。本文は書くな。」
- 上の9つの `agents/<id>.md` の27行目と58行目。毎朝、対応するジャンル体が読む。
  - 「量産するな。1日1本が上限。2本目以降は今日やるな。」
  - 「- 1日1本を超えるな」
- `ledger/pet.md` `ledger/konkatsu.md` `ledger/sidejob.md` `ledger/beauty.md` `ledger/bodymake.md` `ledger/education.md` `ledger/setsuyaku.md` `ledger/tenshoku.md` `ledger/sleep.md` の各4行目。毎朝、対応するジャンル体が読む。
  - 「ルール: 全文同じならスルー。投稿したらチェック。前日の投稿チェックがなければ動画を作るな。未投稿があるなら作るな。1日1本。」
- `PHONE.md` と `wake/*.txt` の15行目（PHONE では各貼り付け文。ペットは38行目）。起動時に1回貼る。
  - 「動画を作ってよいのは、台帳が許可し、未投稿がなく、直近投稿のチェックが済んでいるときだけ。1日1本。前日の投稿チェックが無ければ作るな。」

## 4. raw URL のブランチ

ボットが開く URL は `cursor/video-channel-playbook-e013`。この PR の作業ブランチは `cursor/grok-bot-research-2026-08-26`。URL は変えていない。

- `FETCH.md` 4行目。ジャンル体が所定ファイルの場所を確認するとき。
  - 「参照ブランチ: `cursor/video-channel-playbook-e013`（マージ後は作業ブランチに合わせる。環境変数 GROK_BOT_REF）」
- `agents/pet.md` 15行目（他の8ジャンルの `agents/<id>.md` も同じブランチ）。毎朝、対応するジャンル体が読む。`agents/ジャンル_*.md` は同じ URL へのリンクだけ。
  - 「https://raw.githubusercontent.com/fireworker011/Research/cursor/video-channel-playbook-e013/affiliate-engine/docs/grok-bots/agents/pet.md」
- `wake/pet.txt` 7行目と `PHONE.md` 30行目（他ボットも同じ形）。起動時に1回貼る。
  - 「https://raw.githubusercontent.com/fireworker011/Research/cursor/video-channel-playbook-e013/affiliate-engine/docs/grok-bots/agents/pet.md」

## 5. リプで教えて と コメントで教えて

ペットの待つレシピに、両方の文が残っている。どちらにも揃えていない。

- `archive/recipes/pet.md` の `pet_20260729_01`。読み上げ（51行目）と YouTube説明文（64行目）。毎朝の正本 `agents/pet.md` がここを指す。開くのはジャンル_ペット。`agents/ジャンル_ペット.md` はリンクだけで、この文は無い。
  - 「うちの子だけかと思ったら意外と『あるある』らしい行動、リプで教えてください。」
- `archive/recipes/pet.md` の `pet_20260713_02`。読み上げ（130行目）と YouTube説明文（143行目）。読むのは同じジャンル_ペット。
  - 「『あるある』と思ったもの、コメントで教えてください。意外な共通点が見つかるかもしれません。」
