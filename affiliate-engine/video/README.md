# スキンケア動画アフィリエイト パイプライン

ChatGPTで作った美女画像 → Grok Imagineで動画化 → 編集 → 投稿。
1本あたりの作業を「JSONに5行足して `node` を1回叩く」まで縮めるための仕組み。

```
config/briefs.json  ──┐
data/viral-patterns.json ├─► node src/build-brief.js ─► output/<ID>.md
data/hooks.json     ──┘                                  ├─ ① ChatGPT画像プロンプト
                                                         ├─ ② Grok i2vプロンプト
                                                         ├─ ③ imagine agent 丸投げプロンプト（①②＋編集）
                                                         ├─ ④ テロップ全文
                                                         ├─ ⑤ 投稿キャプション
                                                         └─ ⑥ 検品結果
```

---

## クイックスタート

```bash
cd affiliate-engine/video

# 型とブリーフの一覧
node src/build-brief.js --list

# 1案件ぶんのプロンプト一式を生成
node src/build-brief.js --id 2026-08-serum-a

# 全件
node src/build-brief.js --all
```

`output/<ブリーフID>.md` が出る。検品NGなら exit code 2 で落ちる。

新しい案件を足すときは `config/briefs.json` の `briefs` に1オブジェクト足すだけ。

```json
{
  "id": "2026-09-toner-c",
  "product": "□□化粧水",
  "category": "化粧水",
  "link_key": "skincare_toner_c",
  "concern": "乾燥",
  "pattern_id": "p6_implied_narrative",
  "usp": "べたつかないのに夕方まで持つ",
  "fill": { "stopped": "コットンでバシャバシャ叩くこと", "kept": "手のひらで30秒温めてから入れる" },
  "platform": "instagram_reels",
  "ai_disclosure": true
}
```

`fill` の記入漏れは `【要記入:キー名】` として出力に残り、コンソールにも警告が出る。

---

## 実際の運用フロー（1本 = 15〜25分）

| # | 工程 | 使うもの | 時間 |
|---|---|---|---|
| 0 | 案件と型を決めて `briefs.json` に追記 | エディタ | 2分 |
| 1 | `node src/build-brief.js --id <ID>` | Node | 5秒 |
| 2 | ベース画像を用意（初回のみ） | ChatGPT + `prompts/character-sheet.md` | 初回20分 / 2回目以降0分 |
| 3 | カットごとの画像を生成 | ChatGPT（ベース画像を毎回添付）＋ 出力の① | 5分 |
| 4 | 各画像を動画化 | Grok Imagine ＋ 出力の② | 5分 |
| 5 | 編集 | 出力の③を丸投げ、または `prompts/gemini-edit.md` の1・3 | 5分 |
| 6 | 検品 | `docs/compliance-checklist.md` | 1分 |
| 7 | 投稿（AIラベルON、`#PR`） | 各アプリ | 2分 |

**工程3〜5をまとめてエージェントに投げるなら、出力の「③ imagine agent 丸投げプロンプト」だけを画像と一緒に渡す。** これが画像→動画プロンプトと編集プロンプトを1本に結合したもの。

---

## バズの型

リサーチ（`docs/market-research.md`）から抽出した7つ。`data/viral-patterns.json` に構造化してある。

| ID | 型 | ランク | 用途 |
|---|---|---|---|
| `p6_implied_narrative` | 暗示型ナラティブ | S | **新案件はまずこれ**。Before/Afterの安全代替で最も汎用 |
| `p1_texture_asmr` | 無音テクスチャASMR型 | S | 量産最速・法務リスク最小 |
| `p2_mirror_grwm` | 鏡ごしGRWM型 | S | フォロワー獲得。鏡構図でAI画像の破綻を隠せる |
| `p3_ingredient_reply` | 成分ひとこと解説型 | A | 保存率トップ。ただし薬機法事故が最も起きる型 |
| `p5_three_mistakes` | やりがちミス3つ型 | A | テロップ主導。コメント誘発 |
| `p4_skeptic_convert` | 懐疑→転向型 | A | CVR最上位。**体験談の捏造に直結するので語り手は運用者本人限定** |
| `p7_dupe_ab` | dupe比較／2択型 | B | コメント数狙い。比較NGの案件では使えない |

型を足すときは JSON に1オブジェクト足すだけ。コード変更は不要。

---

## この設計で外してはいけないところ

1. **AI美女画像は「世界観」であって「効果の証拠」ではない。**
   肌の変化をAI画像で見せた瞬間、それは景表法の優良誤認・薬機法違反・CLAUDE.md 不変条件5（体験談の捏造禁止）の三重アウトになる。だから型のレベルで「暗示型ナラティブ」を主力に据えてある。ここを崩すと仕組み全体が違法広告の量産機に変わる。

2. **生成物は必ず検品を通す。**
   `build-brief.js` は出力を `compliance.checkContent()` とスキンケア固有の禁止語リストに通す。モデルの賢さに品質を依存させない（CLAUDE.md 不変条件4と同じ思想）。事故った表現は `data/hooks.json` の `banned_in_hooks` に追記していく。

3. **同じブリーフからは常に同じ台本が出る。**
   フック選択は `brief.id` から計算する決定論。ランダムや日付カーソルを入れない（CLAUDE.md 不変条件2と同じ理由）。差分を試したい時は `fill.hook_line` を明示的に書く。

4. **画（え）の検品は機械では通せない。**
   ビフォーアフター・露出・顔の破綻は人間が見る。`docs/compliance-checklist.md` の C・E・F 節。

---

## ファイル

| パス | 中身 |
|---|---|
| `docs/market-research.md` | 市場リサーチ結果と出典。型の根拠 |
| `docs/compliance-checklist.md` | 投稿前チェックリスト（薬機法／ステマ規制／AI表示／プラットフォーム） |
| `data/viral-patterns.json` | バズの型7種。カット割り・秒数・テロップ・音・リスク |
| `data/hooks.json` | フック7フォーミュラ、悩みワード、禁止語 |
| `config/briefs.json` | 案件定義とペルソナ（`briefs.example.json` が雛形） |
| `src/build-brief.js` | プロンプト一式のビルダー |
| `prompts/character-sheet.md` | ChatGPTで同一人物を安定させる手順 |
| `prompts/gemini-edit.md` | 編集用7プロンプト（スキンケア向けに調整済み） |
| `output/` | 生成物 |

## 既存エンジンとの関係

- `link_key` は `affiliate-engine/config/links.json` のキーと揃える。URL未設定の間はリンクなしで運用する（既存の投稿側と同じ挙動）
- 検品は `affiliate-engine/src/compliance.js` を直接呼んでいる。禁止表現の追加はそちらに入れれば動画側にも効く
- 動画そのものの自動投稿はしない。Threads/Instagram/TikTok とも動画投稿は手動または各公式ツール経由（`src/video-semi-auto.js` と同じ方針）

## 検証

```bash
cd affiliate-engine/video
node --check src/build-brief.js
node src/build-brief.js --all        # exit 0 なら全案件が検品を通過
```
