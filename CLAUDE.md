# Affiliate Engine 運用ガイド（保守セッション向け）

Threads 9アカウントのアフィリエイト完全自動運用システム。詳細は `affiliate-engine/README.md`。
このファイルは**将来の保守セッション（モデル不問）が壊さず作業するための不変条件と手順**をまとめる。

## 絶対に守る不変条件

1. **ブランチ運用**: 開発は `claude/monthly-revenue-system-gvi02u`。デフォルトブランチは `claude/setup-colab-comfyui-Eb9Lh`。
   - コード変更は作業ブランチに push した時点で本番反映される（全ワークフローが実行時に作業ブランチを checkout するため）
   - **ワークフローYAMLの cron/トリガー変更だけはデフォルトブランチへのマージが必要**（GitHubの仕様）
   - マージ後は必ず `git fetch origin <default> && git checkout -B <作業ブランチ> origin/<default> && git push --force-with-lease` で作業ブランチを再スタート
2. **スケジュールCSVは日付決定論**: `strategy-engine.js` のテンプレ選択は日付から計算で決まる。
   生成ごとにリセットされる巡回カーソル等を導入してはならない（毎日再生成されるため「毎日同じ投稿」事故になる。2026-07-07〜09に実際に発生）
3. **重複ガードを外さない**: `threads-poster.js` は直近7日の投稿内容ハッシュ（`output/state/posted.json` の `recent`）と照合し、一致は投稿しない
4. **AI生成テンプレは必ず検品を通す**: `compliance.js` の `validateTemplate()`（構造）→ `checkContent()`（法令/規約）。この順序・両方必須。モデルの賢さに品質を依存させない
5. **やらないこと（倫理・凍結リスク）**: いいね/フォローの自動実行（公式API非対応）、人間を装う自動返信・DM、#PRなしのリンク投稿、体験談の捏造
6. **トークン等の秘密情報はGitHub Secretsのみ**。ファイル・コミット・ログに書かない

## 構成（すべてGitHub上で完結・ローカル依存なし）

| 場所 | 役割 |
|---|---|
| `.github/workflows/affiliate_engine_post.yml` | 投稿。毎時23分起動、期日到来分のみ投稿（ステートレス）。concurrencyで二重実行防止 |
| `.github/workflows/affiliate_engine_insight.yml` | デイリー自動改善。1日2ティック+冪等ガード。分析→ジャンル別リサーチ→テンプレ自動反映→エンゲージキット→Issue #13へ投稿 |
| `.github/workflows/affiliate_engine_report.yml` | 日次KPIレポート（14時JST） |
| `.github/workflows/refresh_threads_token.yml` | 週次トークン更新。`GH_SECRETS_PAT` があればSecrets自動書き戻し |
| `affiliate-engine/config/accounts.json` | 9アカウント定義。`created` はランプアップ起点（1週目1本/日→2週目2本→3本） |
| `affiliate-engine/config/budget.json` | **APIコスト制御**（リサーチは日替わりNジャンルのローテーション）。スマホから編集可 |
| `affiliate-engine/config/links.json` | アフィリンク。空キーのテンプレは投稿時に自動スキップ。`awareness_until`（accounts.json）まではリンク投稿自体を除外 |
| `affiliate-engine/data/seed_templates.json` | テンプレ本体。デイリー改善が自動で追加/引退させる（--prune 3 --cap 36） |
| `output/state/posted.json` | 投稿状態（済みキー+直近内容ハッシュ）。手で編集しない |

## よくある保守タスク

- **投稿されない**: ①GitHub cronは1〜4時間遅延が常態（毎時起動で吸収済み。数時間は待つ）②Actionsの実行ログ→`skipped_*` の理由を見る（duplicate/no_link/awareness は正常動作）③トークン失効なら Issue が立つ
- **コスト調整**: `config/budget.json` の数値を変えるだけ（翌朝反映）
- **アカウント追加**: accounts.json に追記 + links.json にキー + seed にテンプレ（validateTemplate を通す）+ 4つのワークフローに Secrets env 追加 + engage.js の PERSONAS/SEARCH_KEYWORDS + insight.js の link_key リスト
- **8/5リンク解禁**: links.json にURLを入れておけば自動で収益投稿に切り替わる。追加作業なし

## 変更時の検証手順（最低限）

```bash
cd affiliate-engine
node --check src/<変更ファイル>.js
node src/strategy-engine.js --from-file data/seed_templates.json   # 破棄警告が出ないこと
node src/threads-poster.js --dry-run                               # 実投稿なしで内容確認
# スケジュールの決定論性: 2回生成してmd5が一致すること
```

コミットは `git pull --rebase` してから push（自動投稿の状態コミットと競合するため）。
