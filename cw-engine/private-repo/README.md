# 非公開リポジトリの作り方（人間が一度だけ）

公開リポジトリ `Research` は誰でも読める。クライアントの素材・契約後のやり取り・完成品・年齢などの事実は、ここには置けない。
だから **実行と保存は非公開リポジトリ**、**コードは公開リポジトリ** に分ける。

1. GitHub で非公開リポジトリを作る（例: `cw-work`）。Issues を有効にする。README だけあればよい。
2. GitHubアプリで `cw-work` → 「コード」→ 「+」→ 新しいファイル。ファイル名は `.github/workflows/cw.yml`（スラッシュごと）。中身は
   https://github.com/fireworker011/Research/blob/cursor/cw-auto-commander-c1fb/cw-engine/private-repo/cw.yml
   をコピーして貼り、main にコミット。`ENGINE_REF` は今 `cursor/cw-auto-commander-c1fb`。#122 マージ後にデフォルト枝へ戻す。
3. Settings → Secrets and variables → Actions に次を入れる（任意）。
   - `CW_FACTS_JSON`（任意。`cw-engine/config/facts.example.json` の形。CW 公開プロフィールに既に書いてある事実だけ。氏名・年齢は入れない）
   - `ANTHROPIC_API_KEY` は不要。完成品は Grok Bot が書く。
4. Settings → Actions → General → Workflow permissions を **Read and write** にする。
5. Actions タブで「CW 司令塔」を一度 Run workflow する（または `cw.yml` を push する）。Issue `CW — 司令塔` が自動で立つ。
6. 以後はその Issue にコメントするだけ。1行目 `CW: JOB <仕事ID>`、2行目以降に公開文を貼る。

`ENGINE_REF` は最初は PR の枝名にしてよい。マージ後にデフォルトブランチへ戻す。
公開リポジトリの Issue には何も書かない。100万本線の Issue（`Grok Bot — 指示`）にも CW を書かない。
