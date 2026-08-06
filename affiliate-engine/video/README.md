# スキンケア動画アフィリエイト パイプライン

ChatGPTで作った美女画像 → **Grok Imagine Agent Mode にまるなげ** → 投稿。
1本あたりの作業を「JSONに5行足して `node` を1回叩く」まで縮めるための仕組み。

```
config/briefs.json       ──┐
data/viral-patterns.json   │
data/hooks.json            ├─► node src/build-brief.js ─► output/<ID>.md
data/agent-variants.json ──┘                              ├─ ① Agent Mode まるなげプロンプト ←本命
                                                          ├─ ② ChatGPT画像プロンプト（渡す素材）
                                                          ├─ ③ Grok単体プロンプト（フォールバック）
                                                          ├─ ④ テロップ全文
                                                          ├─ ⑤ 投稿キャプション
                                                          └─ ⑥ 検品結果
```

編集は Grok Imagine Agent Mode に一本化してある。CapCut も Gemini も使わない。

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
  "ai_disclosure": true,
  "tone": "自然なUGC風",
  "variant": "problem_solution"
}
```

`variant` は `data/agent-variants.json` のキー（`problem_solution` / `cinematic` / `fast_buzz` /
`self_deprecating` / `from_existing_video`）。まるなげプロンプトの末尾に用途別の追加指示が入る。

`fill` の記入漏れは `【要記入:キー名】` として出力に残り、コンソールにも警告が出る。

---

## 実際の運用フロー（1本 = 15〜25分）

| # | 工程 | 使うもの | 時間 |
|---|---|---|---|
| 0 | 案件と型を決めて `briefs.json` に追記 | エディタ | 2分 |
| 1 | `node src/build-brief.js --id <ID>` | Node | 5秒 |
| 2 | ベース画像を用意（初回のみ） | ChatGPT + `prompts/character-sheet.md` | 初回20分 / 2回目以降0分 |
| 3 | 人物カットの画像を生成 | ChatGPT（ベース画像を毎回添付）＋ 出力の② | 5分 |
| 4 | **まるなげ**（生成〜スティッチ〜仕上げ） | Grok Imagine Agent Mode ＋ 出力の① | 5〜10分 |
| 5 | テロップを乗せる | 任意のツール（Agent Modeが出したテロップ台本を使う） | 3分 |
| 6 | 検品 | `docs/compliance-checklist.md` | 1分 |
| 7 | 投稿（AIラベルON、`#PR`） | 各アプリ | 2分 |

### 工程4のやり方

1. grok.com/imagine をデスクトップで開く（**SuperGrok $30/月以上**が必要。Lite では Agent Mode が出ない）
2. 入力欄で **Agent Mode を ON**、プリセット **UGC Product Stories** を選ぶ
3. 工程3で作った人物画像と、商品写真（正面・斜め・使用シーン・パッケージ・テクスチャの5枚が目安）をアップロード
4. 出力の「① Agent Mode まるなげプロンプト」を貼って送信
5. ストーリーボードが出たら承認 → 以降は止まらずに完成まで走る

**まず15秒で試し、当たったら同じストーリーボードで30秒に伸ばす。** 最初から長尺を狙うと破綻シーンの引き当てで作り直しコストが跳ねる。

### テロップを焼き込ませない理由

Grok は文字をシステムフォントではなく**ピクセルとして描画する**ため、日本語は崩れる。
まるなげプロンプトには「日本語を焼き込むな／上15%・下25%をセーフエリアとして空けろ／テロップ台本をタイムコード付きテキストで出せ」を入れてある。出てきた台本を工程5で乗せる。

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
| `prompts/grok-agent-mode.md` | Agent Mode の実仕様、汎用マスタープロンプト、詰まった時の対処 |
| `data/agent-variants.json` | まるなげプロンプトの用途別アドオン5種 |
| `output/` | 生成物 |

## 既存エンジンとの関係

- `link_key` は `affiliate-engine/config/links.json` のキーと揃える。URL未設定の間はリンクなしで運用する（既存の投稿側と同じ挙動）
- 検品は `affiliate-engine/src/compliance.js` を直接呼んでいる。禁止表現の追加はそちらに入れれば動画側にも効く
- 動画そのものの自動投稿はしない。Threads/Instagram/TikTok とも動画投稿は手動または各公式ツール経由（`src/video-semi-auto.js` と同じ方針）
- Agent Mode は API ではなくWeb UIなので、この工程だけは自動化しない（手で貼る）

## 検証

```bash
cd affiliate-engine/video
node --check src/build-brief.js
node src/build-brief.js --all        # exit 0 なら全案件が検品を通過
```
