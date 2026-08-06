# 市場リサーチ：スキンケア×AI美女画像 ショート動画アフィリエイト

調査日: 2026-08-06 / 調査手法: Web検索（一次ソースは末尾）

---

## 1. 結論（先に読むところ）

1. **勝負は冒頭2秒。** 視聴者は最初の2〜3秒で残るか離脱するかを決める。最も強いのは**視覚フックと言語フックの同時発火**で、どちらか片方だけは弱い。
2. **美容はアフィリエイトで最も密度が高いカテゴリ。** 商品数・案件数・報酬率のすべてで有利で、報酬率は一般カテゴリの8〜12%に対し**15〜30%**。
3. **売れる動画と伸びる動画は違う。** 再生数を取りたければ GRWM、**リンクを踏ませたければ「特定の悩みを解決するチュートリアル」**。毛穴・脂性肌・くすみ・ニキビ跡のように悩みを1つに絞ったほうが売れる。
4. **中堅クリエイターで機能している5フォーマット**：GRWM／成分解説（コメント返信形式）／ルーティン／習慣ナラティブ型のビフォーアフター／懐疑→転向レビュー。加えて**テクスチャ接写のASMR**と**dupe比較**が伸びている。
5. **TikTokの2026年アルゴリズムは中盤・終盤の構成の一貫性まで見る。** フックで釣って中身が伴わない動画は完走率で落とされる。フックの約束は必ず回収する。
6. **AI生成コンテンツの締め付けは急速に強まっている。** TikTokは2026年Q1だけで合成メディアポリシー違反として**230万本超を削除（前年同期比+180%）**。Instagram/Threadsは2026年5月から**アカウント単位のAIクリエイターラベル**をテスト中（現状は任意）。
7. **日本で最大の落とし穴は薬機法。** 化粧品が言える効能効果は厚労省の**56項目**に限定され、課徴金は売上の4.5%。企業から金銭・商品提供を受けたSNS投稿は個人でも「広告」として規制対象になる。

---

## 2. バズっているフォーマットの分解

### 2-1. フックのフォーミュラ（横断して機能しているもの）

| フォーミュラ | 構造 | スキンケアでの実装 |
|---|---|---|
| Problem–Solution | 悩みを名指し → 解決を匂わせる | 「毛穴、実はスキンケアの前の30秒で決まってた」 |
| Before–After Reveal | 結果を先に見せ、後から手順 | ※AI画像では使用禁止（後述） |
| Open Loop | 「誰も言わない〜」で好奇心ギャップ | 「誰も言わないけど、乾燥肌の人がやりがちなことが1個ある」 |
| Skeptic | 期待していなかったと言い切る | 「正直、これは期待してなかった」 |
| Enumeration | 「3つ」で確認欲求を作る | 「毛穴で損してる人の3パターン」 |
| Sensory | 言語なし、映像と音だけ | テクスチャ超接写＋「音アリでどうぞ🔊」 |
| Reply | コメント返信UIを冒頭に置く | 「『これ効果ある？』に正直に答える」 |

共通構造は**「注意を掴む → 悩みか欲求に接続 → 解決を匂わせる」**で、これは商材が変わっても不変。

### 2-2. 尺と構成

- 冒頭0〜3秒：フック（5パターンから選ぶ）
- 中盤：**1動画1メッセージ**、カットは2〜3秒、視覚的変化でテンポ維持
- 末尾3秒：具体的なCTA

ミニマルなルーティン紹介なら **GRWM 30〜45秒＋ASMRボイスオーバー＋手のひらに商品を出すデモ**、スカルプケアなら **POVの接写（ローアングル）＋根元への塗布デモ20〜40秒** が最適解として挙がっている。

### 2-3. AI美女運用側の実態

日本語圏で流通している手法は、要するに **「AI美女画像を作る → 伸びているショートを見つける → 顔を差し替えて編集して投稿」** で、動画編集スキルも顔出しも発声も不要という点が売り。1本あたり数十秒〜数分で作れるため、**1本の質ではなく試行回数で勝つ**設計になっている。

これは本リポジトリの既存方針（`23ff1f5 手数勝負への戦略転換`）と同じ思想なので、**バズの型を固定して量産する**方向に素直に乗せられる。

> ただし「伸びている動画を見つけて顔を差し替える」部分はそのまま真似しない。他人の動画・構成の複製は著作権と各プラットフォームの重複コンテンツ判定の両方に触れる。本パイプラインは**型（構造）だけをオマージュし、素材はすべて自前生成する**。

---

## 3. 決定的な設計判断：AI美女は「証拠」ではなく「世界観」に使う

スキンケアで最も反応が取れるのはビフォーアフターだが、**AI生成画像でビフォーアフターを作ると、それは効果の捏造そのもの**になる。

- 景表法：実際にはない効果を示す優良誤認
- 薬機法：化粧品の効能効果56項目を超える標ぼう
- Meta / TikTok：ビフォーアフター表現自体に広告ポリシー上の制限
- 本リポジトリの不変条件5：体験談の捏造の禁止

そこで、リサーチで確認された**「暗示型（implied before/after）」**を採用する。これは変化そのものを見せず、**「この状態を保つためにやっていること」**というナラティブで変化を想起させる手法で、実際に機能しているフォーマットとして報告されている。

**本パイプラインの原則：AI美女画像は、視線を止め、世界観を統一し、動画の温度感を作るためだけに使う。肌の状態を成果として提示しない。** この線引きは倫理上の話であると同時に、量産の持続可能性（アカウント凍結と行政処分の回避）に直結する。

---

## 4. バズの型 7種（`data/viral-patterns.json` に実装済み）

| ID | 型 | ランク | 強み | 主な用途 |
|---|---|---|---|---|
| `p1_texture_asmr` | 無音テクスチャASMR型 | S | 言語非依存で量産最速、法務リスク最小 | 横展開の主力 |
| `p2_mirror_grwm` | 鏡ごしGRWM型 | S | 再生数最大フォーマット。鏡構図でAI画像の破綻を隠せる | フォロワー獲得 |
| `p3_ingredient_reply` | 成分ひとこと解説型 | A | 保存率トップ、クリック理由を作れる | CVR狙い |
| `p4_skeptic_convert` | 懐疑→転向型 | A | 広告耐性を下げる。CVR最上位 | ※体験談の扱いに要注意 |
| `p5_three_mistakes` | やりがちミス3つ型 | A | テロップ主導でAI画像の粗が出ない | コメント誘発 |
| `p6_implied_narrative` | 暗示型ナラティブ | S | Before/Afterの安全代替。最も汎用 | **新案件はまずここから** |
| `p7_dupe_ab` | dupe比較／2択型 | B | スプリット構図で強い視覚フック | コメント数狙い |

各型のカット割り・秒数配分・テロップ・音・リスクは JSON に構造化してあるので、`node src/build-brief.js` がそのままプロンプトに展開する。

---

## 5. ツール側の事実確認（2026-08時点）

### Grok Imagine（画像→動画）
- 2026-02-02 の Imagine 1.0 更新で **動画長6秒 → 最大10秒**、解像度 **720p**、Aurora-2 エンジンで音声生成・リップシンク・BGM/効果音に対応
- プロンプトは**「何が動くか」と「カメラがどう動くか」を必ず両方書く**。動きは1〜2種類に絞る。`drifts` `unfurls` `surges` のような具体的な動詞が `moves` より効く
- キーワードの羅列ではなく**短いクリエイティブブリーフとして書く**ほうが従う
- 主語が明確で背景が整理された画のほうが安定する。混雑した画は破綻する
- 既知の弱点：**クリップ間で顔が変わる**。→ プロンプトに「変えてはいけないもの」を明示するのが対策（`build-brief.js` の `Must stay stable:` 節）
- 実在人物・キャラクター・商標を含むプロンプトは避ける。権利リスクは生成者側に来る

### Gemini による編集（ユーザー提供の7プロンプトについて）
7つのプロンプトはそのまま使えるが、**期待値の調整が必要**：

- **Gemini 単体はタイムラインを描き出して動画ファイルを吐かない。** Gemini は「短く速いプロジェクト」向けのチャット側コンソールで、実際の**タイムライン編集と長尺化は Google Flow 側**の役割
- Veo の1生成は**最大8秒**。長尺は Flow のタイムラインでクリップを連結して作る
- したがって7プロンプトの正しい位置づけは **「編集ディレクション生成器」**。EDL（編集指示表）を出させて、実レンダリングは Flow / CapCut / ffmpeg のいずれかで行う
- 「CapCut不要」は**成立する**が、それは Gemini が描き出すからではなく、**Gemini が出した EDL を Flow か ffmpeg に流し込めるから**

この前提で `prompts/gemini-edit.md` に7プロンプトをスキンケア向けに調整して収録した。

---

## 6. コンプライアンス（詳細は `docs/compliance-checklist.md`）

- **薬機法**：化粧品の効能効果は56項目に限定。「シミ・そばかすが消えてなくなる」「使えば使うほど肌が白くなる」等はNG。一般化粧品で言えるのは「メーキャップにより肌を白く見せる」まで。医薬部外品なら「メラニンの生成を抑え、しみ・そばかすを防ぐ」が言える
- **ステマ規制**（2023年10月施行）：金銭・商品提供を受けた投稿は広告表記が必須。`#PR` を必ず入れる
- **AI表示**：日本には2026年7月時点でSNS投稿のAI表示を一律義務づける法律はない。ただし Meta のガイドラインは「現実と見紛うAI生成の動画・画像」にラベル表示を求めており、TikTok は違反削除を急増させている。**義務がないから付けない、ではなく、凍結回避のために付ける**

---

## Sources

- [ショート動画でバズるための構成テンプレート｜TikTok・Reels完全攻略 - TENANi](https://tenani.jp/2026/03/22/short-video-viral-template/)
- [18 UGC Hook Formulas That Stop the Scroll (2026 Examples) - Sideshift](https://sideshift.app/blog/ugc-hook-formulas)
- [25 Viral TikTok Hooks for Beauty Creators (Tested 2026) - Hook Mafia](https://www.hookmafia.io/tiktok-hooks-for-beauty-creators)
- [What TikTok content trends are working for skincare brands in 2026? - Draper](https://draper.chat/blog/tiktok-skincare-trends-2026)
- [Skincare TikTok Content Ideas: Formats Worth Testing - Superdirector](https://superdirector.app/ideas/tiktok/skincare)
- [Before/After Skincare Ads on Meta and TikTok: What's Actually Allowed in 2026 - InnoBotZ](https://innobotz.com/blog/articles/skincare-before-after-ad-compliance-meta-tiktok-2026.html)
- [【2026年最新】AI美女×TikTokコピーで30秒量産、副業で稼ぐ完全手順 - note](https://note.com/natty_pothos982/n/n669d83a3d6a5)
- [AI美女のインスタは儲かる？マネタイズ方法やAI美女の作り方を紹介 - BuzzCollege](https://buzzcollege.net/instagram/341)
- [【美容・コスメ系業界】企業のTikTokアカウント成功例5選 - LEAD ONE](https://lead-one.info/tiktok/8543/)
- [Grok Imagine Prompts: A Practical Guide for Short AI Videos (2026) - ImagineVid](https://imaginevid.io/blog/grok-imagine-prompts-guide)
- [Grok Imagine Video: A Guide to AI Motion Creation - Scenario](https://help.scenario.com/articles/5410526625-grok-imagine-video-a-guide-to-ai-motion-creation)
- [Grok Imagineで画像から動画を作る完全手順！モード選びとモーション指示のコツ - romptn Magazine](https://romptn.com/article/105423)
- [Grok Imagine 1.0とは｜AI動画・画像生成の完全ガイド【2026年最新】 - AI革命](https://ai-revolution.co.jp/media/what-is-grok-imagine/)
- [Bringing new Veo 3.1 updates into Flow to edit AI video - Google Blog](https://blog.google/technology/ai/veo-updates-flow/)
- [Google Flow + Veo 3 Guide 2026 - veo3ai.io](https://www.veo3ai.io/blog/google-flow-veo-3-guide-2026)
- [薬機法にまつわる表現ルール【化粧品編】 - A8.net](https://www.a8.net/compliance/pmd-rules-cosmetics.php)
- [化粧品・医薬部外品で「美白」「ホワイトニング」は表現できる？ - マクロジ](https://maclogi.co.jp/column/3029/?type=lecture)
- [【薬機法】化粧品・コスメ広告で標ぼうOK/NGな表現について解説 - 薬事法ドットコム](https://www.yakujihou.com/knowledge/cosme-advertisement/)
- [インフルエンサーPRと薬機法の注意点｜化粧品・健康食品のNG表現と対策 - mocha](https://mochainc.co.jp/influencer-pharmaceutical-law/)
- [Instagram AIラベルとは？仕組み・表示ルール・企業が取るべき対策【2026年最新】 - tatap](https://tatap.jp/knowledge/instagram-ai-label/)
- [TikTokがAI生成コンテンツ規制を大幅強化——Q1で230万本削除 - CREATORS POST](https://torihada.co.jp/creatorspost/4013/)
- [AI生成の投稿に開示表示は必要？｜各SNSのルール整理 - BtoB AIマーケティングナビ](https://debono.co.jp/media/sns-ai-kaiji-label-ai/)
- [【ChatGPT4】同じキャラクターを生成する手法｜選択編集 - note](https://note.com/hirota626/n/n8a36b4ab218e)
