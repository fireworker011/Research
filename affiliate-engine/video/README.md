# 動画アフィリエイト パイプライン（マルチジャンル）

ChatGPTで作った被写体画像 → **Grok Imagine Agent Mode にまるなげ** → 投稿。
1本あたりの作業を「JSONに数行足して `node` を1回叩く」まで縮めるための仕組み。
スキンケア（美容アカウント）とペット（pet アカウント）の2ジャンルに対応済み。ジャンル追加は
`data/domains/<domain>/` を1つ足すだけで、コード変更は不要。

```
config/briefs.json（personas.<domain> + briefs[].domain）
data/domains/<domain>/{viral-patterns,hooks,domain}.json  ──┐
data/agent-variants.json                                    ├─► node src/build-brief.js ─► output/<ID>.md
                                                              │     ├─ ① Agent Mode まるなげプロンプト ←本命
                                                              │     ├─ ② ChatGPT画像プロンプト（渡す素材）
                                                              │     ├─ ③ Grok単体プロンプト（フォールバック）
                                                              │     ├─ ④ テロップ全文
                                                              │     ├─ ⑤ 投稿キャプション
                                                              │     └─ ⑥ 検品結果
```

編集は Grok Imagine Agent Mode に一本化してある。CapCut も Gemini も使わない。

---

## クイックスタート

```bash
cd affiliate-engine/video

# ジャンル別の型とブリーフの一覧
node src/build-brief.js --list

# 1案件ぶんのプロンプト一式を生成
node src/build-brief.js --id orbis-u-01
node src/build-brief.js --id furbo-01

# 全件（全ジャンル横断）
node src/build-brief.js --all
```

`output/<ブリーフID>.md` が出る。検品NGなら exit code 2 で落ちる。

新しい案件を足すときは `config/briefs.json` の `briefs` に1オブジェクト足すだけ。`domain` で
ジャンル（`skincare` / `pet`）を切り替える。省略時は `skincare` 扱い。

```json
{
  "id": "hoken-03",
  "domain": "pet",
  "product": "ペット保険（資料請求）",
  "category": "ペット保険",
  "link_key": "ペット_保険",
  "concern": "通院費の負担",
  "pattern_id": "pet_p3_vet_reply",
  "usp": "無料で複数社の補償内容を比較できる",
  "fill": { "question": "保険って入るべき？", "fact": "…", "decision": "…" },
  "platform": "threads",
  "ai_disclosure": true,
  "tone": "落ち着いた、誠実なトーン"
}
```

`variant` は `data/agent-variants.json` のキー（`problem_solution` / `cinematic` / `fast_buzz` /
`self_deprecating` / `from_existing_video`）。ジャンルを問わず共通で使える。まるなげプロンプトの
末尾に用途別の追加指示が入る。

`fill` の記入漏れは `【要記入:キー名】` として出力に残り、コンソールにも警告が出る。

---

## 実際の運用フロー（1本 = 15〜25分）

| # | 工程 | 使うもの | 時間 |
|---|---|---|---|
| 0 | 案件と型を決めて `briefs.json` に追記 | エディタ | 2分 |
| 1 | `node src/build-brief.js --id <ID>` | Node | 5秒 |
| 2 | ベース画像を用意（初回のみ／ジャンルごとに1回） | ChatGPT + `prompts/character-sheet.md` | 初回20分 / 2回目以降0分 |
| 3 | 被写体カットの画像を生成 | ChatGPT（ベース画像を毎回添付）＋ 出力の② | 5分 |
| 4 | **まるなげ**（生成〜スティッチ〜仕上げ） | Grok Imagine Agent Mode ＋ 出力の① | 5〜10分 |
| 5 | テロップを乗せる | 任意のツール（Agent Modeが出したテロップ台本を使う） | 3分 |
| 6 | 検品 | `docs/compliance-checklist.md` | 1分 |
| 7 | 投稿（AIラベルON、`#PR`） | 各アプリ | 2分 |

### 工程4のやり方

1. grok.com/imagine をデスクトップで開く（**SuperGrok $30/月以上**が必要。Lite では Agent Mode が出ない）
2. 入力欄で **Agent Mode を ON**、プリセット **UGC Product Stories** を選ぶ
3. 工程3で作った被写体画像と、商品写真（正面・斜め・使用シーン・パッケージ・テクスチャの5枚が目安）をアップロード
4. 出力の「① Agent Mode まるなげプロンプト」を貼って送信
5. ストーリーボードが出たら承認 → 以降は止まらずに完成まで走る

**まず15秒で試し、当たったら同じストーリーボードで30秒に伸ばす。** 最初から長尺を狙うと破綻シーンの引き当てで作り直しコストが跳ねる。

### テロップを焼き込ませない理由

Grok は文字をシステムフォントではなく**ピクセルとして描画する**ため、日本語は崩れる。
まるなげプロンプトには「日本語を焼き込むな／上15%・下25%をセーフエリアとして空けろ／テロップ台本をタイムコード付きテキストで出せ」を入れてある。出てきた台本を工程5で乗せる。

---

## ジャンル

### スキンケア（`domain: "skincare"`）

美容アカウント（`accounts.json`: `beauty`）・オルビスユー案件向け。リサーチは `docs/market-research.md`、型は `data/domains/skincare/viral-patterns.json` に7種。

| ID | 型 | ランク | 用途 |
|---|---|---|---|
| `p6_implied_narrative` | 暗示型ナラティブ | S | **新案件はまずこれ**。Before/Afterの安全代替で最も汎用 |
| `p1_texture_asmr` | 無音テクスチャASMR型 | S | 量産最速・法務リスク最小 |
| `p2_mirror_grwm` | 鏡ごしGRWM型 | S | フォロワー獲得。鏡構図でAI画像の破綻を隠せる |
| `p3_ingredient_reply` | 成分ひとこと解説型 | A | 保存率トップ。ただし薬機法事故が最も起きる型 |
| `p5_three_mistakes` | やりがちミス3つ型 | A | テロップ主導。コメント誘発 |
| `p4_skeptic_convert` | 懐疑→転向型 | A | CVR最上位。**体験談の捏造に直結するので語り手は運用者本人限定** |
| `p7_dupe_ab` | dupe比較／2択型 | B | コメント数狙い。比較NGの案件では使えない |

### ペット（`domain: "pet"`）

pet アカウント（`docs/account-setup-kit.md` §7『ふく｜いぬと暮らしの手帖』）向け。Furbo（見守りカメラ）・ペット保険・ペットフードの3案件。リサーチは `docs/market-research-pet.md`、型は `data/domains/pet/viral-patterns.json` に5種。

| ID | 型 | ランク | 用途 |
|---|---|---|---|
| `pet_p1_furbo_curiosity` | 留守番のぞき見型 | S | Furbo案件の主力。恐怖訴求ではなく好奇心訴求 |
| `pet_p2_doorstep_wait` | お出迎え儀式型 | S | フォロワー獲得。恐怖要素ゼロで生活導入として使える |
| `pet_p5_food_texture` | ごはん比較型 | S | 犬のフル生成が不要で破綻リスクが最も低い |
| `pet_p3_vet_reply` | 獣医に聞いた話型 | A | 保険案件。**保険業法の規制が最も厳しい型** |
| `pet_p4_cost_reality` | お金のリアル型 | A | 保険案件。列挙型でAI生成リスクが低い |

型を足すときは JSON に1オブジェクト足すだけ。コード変更は不要。ジャンルを新設する時は
`data/domains/<domain>/{viral-patterns,hooks,domain}.json` を3つ作り、`config/briefs.json` に
`personas.<domain>` を追加する（`domain.json` の書式は下記）。

```json
{
  "subject_label": "犬",
  "image_prompt_intro": "画像生成の基礎トーン（写真的リアリズム・構図など）",
  "stability_ja": "変えてはいけない特徴（日本語・agentModePromptで使用）",
  "stability_en": "same in English（Grok単体プロンプトで使用）",
  "mood_en": "英語の雰囲気指定",
  "disclaimer_line": "投稿キャプションに入れる注意書き",
  "banned_claims_note": "そのジャンルの規制に基づく禁止表現の説明文",
  "forbidden_visuals": "作ってはいけない画の説明文",
  "banned_word_label": "検品結果に出すラベル名"
}
```

---

## この設計で外してはいけないところ

1. **AI生成の被写体は「世界観」であって「効果・成果の証拠」ではない。**
   状態の変化をAI画像で見せた瞬間、それは景表法の優良誤認・各ジャンルの表示規制違反・CLAUDE.md 不変条件5（体験談の捏造禁止）の複合違反になる。だからスキンケアでは「暗示型ナラティブ」、ペットでは「留守番のぞき見型」のように、状態を見せずに安心感・世界観だけを見せる型を主力に据えてある。ここを崩すと仕組み全体が違法広告の量産機に変わる。

2. **生成物は必ず検品を通す。**
   `build-brief.js` は出力を `compliance.checkContent()` とジャンル固有の禁止語リストに通す。モデルの賢さに品質を依存させない（CLAUDE.md 不変条件4と同じ思想）。事故った表現は `data/domains/<domain>/hooks.json` の `banned_in_hooks` に追記していく。

3. **同じブリーフからは常に同じ台本が出る。**
   フック選択は `brief.id` から計算する決定論。ランダムや日付カーソルを入れない（CLAUDE.md 不変条件2と同じ理由）。差分を試したい時は `fill.hook_line` を明示的に書く。

4. **画（え）の検品は機械では通せない。**
   ビフォーアフター・露出・被写体の破綻・（ペットなら）動物福祉ポリシー違反は人間が見る。`docs/compliance-checklist.md` の C・E・F 節。

---

## ファイル

| パス | 中身 |
|---|---|
| `docs/market-research.md` | スキンケアの市場リサーチと出典 |
| `docs/market-research-pet.md` | ペットの市場リサーチと出典 |
| `docs/compliance-checklist.md` | 投稿前チェックリスト（全ジャンル共通＋ジャンル別セクション） |
| `data/domains/skincare/` | スキンケアの型・フック・ジャンル固有コピー |
| `data/domains/pet/` | ペットの型・フック・ジャンル固有コピー |
| `data/agent-variants.json` | まるなげプロンプトの用途別アドオン5種（ジャンル共通） |
| `config/briefs.json` | 案件定義とジャンル別ペルソナ（`briefs.example.json` が雛形） |
| `src/build-brief.js` | プロンプト一式のビルダー |
| `prompts/character-sheet.md` | ChatGPTで同一の被写体を安定させる手順（スキンケア・ペット両対応） |
| `prompts/grok-agent-mode.md` | Agent Mode の実仕様、汎用マスタープロンプト、詰まった時の対処 |
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
node src/build-brief.js --all        # exit 0 なら全ジャンル・全案件が検品を通過
```
