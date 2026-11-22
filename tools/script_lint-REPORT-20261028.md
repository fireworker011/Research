# 字幕・台本チェッカー 2026-10-28

依頼2だけ。投稿・送信・動画生成・申し込みはしていない。ドラフトPRで、マージしない。

入力は `inputs/20261028/`（渡されたアーカイブを展開したもの）。`kachigata.md` は書式の見本で、9本には数えない。

## 判定

`python tools/script_lint.py inputs/20261028`

- SRT は番号が 1 から連続、時刻は `HH:MM:SS,mmm`、開始は終了より前
- セリフ字幕どうしの空きは 1.5 秒以内。ちょうど 1.5 秒は PASS。PR 行（右上の PR、`#PR`、`PR｜`）とフック行（`{\an8}`）は空きの計算に入れない
- ペット・美容・婚活は、0.000 秒の行に右上 PR があり、SRT の終端から見て最後 2 秒を `#PR` が覆う
- ゆあ・金メモは、その PR が無い
- 禁止語（治る、必ず稼げる、若返る、必ず、絶対）を、台詞・セリフ・字幕・画の流れと SRT から探す。根拠メモと PR の注記は対象外。自己採点は直したあとの最後の合計が 80 以上
- URL の断片があれば a8 列が WARN。今回の 9 本には無かった

長さの基準は各 SRT の終端。台本の「尺」とは突き合わせていない。

## 9本の結果

| 本 | SRT書式 | 字幕の間 | PR | 禁止語 | 見出し | 自己採点 | a8 | 結果 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-28-ゆあ-kasa-hairu | PASS | PASS（最大1.5秒） | PASS（PRなし） | PASS | PASS | PASS（82） | なし | PASS |
| 2026-10-28-ゆあ-kogeta-tamagoyaki | FAIL（SRTファイルなし） | FAIL（SRTファイルなし） | FAIL（SRTファイルなし） | FAIL（SRTなし） | PASS | PASS（82） | なし | FAIL |
| 2026-10-28-ゆあ-sentaku-uragaeshi | PASS | PASS（最大1.5秒） | PASS（PRなし） | PASS | PASS | PASS（81） | なし | PASS |
| 2026-10-28-ペット-kuroneko-hidamari | PASS | PASS（セリフ字幕なし） | PASS | PASS | PASS | PASS（82） | なし | PASS |
| 2026-10-28-婚活-konkatsu12-miru-dake | PASS | PASS（最大0.4秒） | PASS | PASS | PASS | PASS（81） | なし | PASS |
| 2026-10-28-婚活-sanoufuku | PASS | PASS（最大0.6秒） | PASS | PASS | PASS | PASS（81） | なし | PASS |
| 2026-10-28-婚活-senmenjo-photo | PASS | PASS（最大0.5秒） | PASS | PASS | PASS | PASS（80） | なし | PASS |
| 2026-10-28-美容-amber-hitotsu | PASS | PASS（最大0.5秒） | PASS | PASS | PASS | PASS（80） | なし | PASS |
| 2026-10-28-金メモ-hoken-hagaki | PASS | PASS（最大0.4秒） | PASS（PRなし） | PASS | PASS | PASS（80） | なし | PASS |

合計 9本: PASS 8 / FAIL 1 / WARN 0

終了コードは 1（FAIL が1本あるため）。

FAIL は `2026-10-28-ゆあ-kogeta-tamagoyaki`。台本 md には 0〜1秒フック、brief、自己採点（直した後 82）がある。同じ名前の SRT がアーカイブに無い。字幕は新規に書いていない。

## 壊したSRTのログ

`python tools/script_lint.py --self-test`（終了コード 0）

テスト用の実体は `tools/script_lint_fixtures/`。

```
# 壊したSRT 3つ

| 本 | SRT書式 | 字幕の間 | PR | 禁止語 | 見出し | 自己採点 | a8 | 結果 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-28-ゆあ-test-gap | PASS | FAIL（最大2秒） | PASS（PRなし） | PASS | PASS | PASS（80） | なし | FAIL |
| 2026-10-28-婚活-test-pr | PASS | PASS（最大0.4秒） | FAIL（0.000秒の右上PRが無い、最後2秒の#PRが無い） | PASS | PASS | PASS（80） | なし | FAIL |
| 2026-10-28-金メモ-test-kinshi | PASS | PASS（セリフ字幕1つ） | PASS（PRなし） | FAIL（SRT「治る」） | PASS | PASS（80） | なし | FAIL |

合計 3本: PASS 0 / FAIL 3 / WARN 0

確認:
- 間が2秒: OK FAIL（最大2秒）
- PR抜け: OK FAIL（0.000秒の右上PRが無い、最後2秒の#PRが無い）
- 禁止語: OK FAIL（SRT「治る」）

境界:
- 1.500秒は以内: OK PASS（最大1.5秒）
- 1.501秒は超過: OK FAIL（最大1.501秒）
- 自己採点は最後の合計: OK FAIL（79）
- 開始と終了が同じ: OK FAIL（1は開始が終了以上）
- PR行とフック行は間隔に入れない: OK PASS（セリフ字幕なし） / PASS
- ゆあにPRがあるとFAIL: OK FAIL（PRなしのラインにPRがある）

実ファイルの抜き取り:
- ペット実ファイル: OK PASS / PASS / PASS（セリフ字幕なし）
- ゆあ傘の間隔1.5秒: OK PASS（最大1.5秒）
- 婚活三往復は注記の語を台詞に数えない: OK PASS / PASS（81）

自己テスト: OK
```

間が2秒のテストは、根拠メモに禁止語と同じ字を置いてある。FAIL にはなっていない（台詞・字幕ではないため）。PR抜けのテストは、注記側に同じ字があり、直す前の合計は 70、直したあとは 80。禁止語の FAIL は SRT の「治る」だけで、台本側は PASS。

## push前の検索

依頼の `git grep` を、push 前に実行する。

- 今回追加する `inputs/20261028/` と `tools/` に、連続した対象文字列は 0 件
- パラメータ名の断片は、リポジトリ全体でも 0 件
- `px.` 付きの追跡ホストも 0 件
- ホスト名の検索は、このブランチより前から `research/` と `affiliate-engine/docs/` に案内ページが 143 行ある。この PR の差分では 1 行も足していない。行の URL はここに再掲しない

検査スクリプトの定数は、ソース上で文字列を分割してあり、連続した対象文字列にはならない。

## 引き継ぎメモ

上限の 45 分には達していない。直しは 0 回（自己テストは 1 回目で通った）。

### できたこと

- `tools/script_lint.py` を追加し、9 本の表を出した
- わざと壊した SRT 3 つ（間が 2 秒、PR 抜け、禁止語）が、その項目だけ FAIL になることを確認した
- 1.500 秒は PASS、1.501 秒は FAIL。自己採点は最後の合計を使う

### 残り

- ゆあ「焦げた卵焼き」の SRT が入力に無い。8 本は PASS、この 1 本だけ FAIL
- リポジトリ全体のホスト名検索は 0 件ではない。残っているのは作業前からの案内ページで、この PR では消しても足してもいない

### 失敗した直しと理由

なし。

### 次の一手

卵焼きの SRT を台本側で足したら、`python tools/script_lint.py inputs/20261028` を再実行する。字幕の新規作成はここではしない。既存の案内ページを消すかどうかは、人間が決める。
