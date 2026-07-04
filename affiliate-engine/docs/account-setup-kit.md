# アカウント設営キット（コピペ用）

4アカウント分の開設素材一式。**このページの内容をそのままコピペすれば開設できる**ことを目的とする。

## ⚠️ 先に読む: ペルソナ運用の3ルール

1. **ペンネーム・キャラクター設定はOK**（出版・メディア業界の通常慣行）。ただし **使ってもいない商品の体験談を装うのはNG**（景品表示法・不実証広告のリスク）。紹介は「調べた」「まとめた」「選択肢を整理した」の形にする（テンプレはこの形で作ってある）
2. DM やリプで辻褄が合わなくなるので、**自分が無理なく演じられる設定**にする。細かい年齢・家族構成をプロフィールで断定しない（下のプロフィール文はそのように設計済み）
3. 5アカウントを**同日に一気に開設しない**。1〜2週間隔で1つずつ。開設直後の2〜3日は自動投稿を待たず、手動で2〜3投稿+同ジャンルへのコメント回りをしてアカウントを温める

## 共通: 開設手順（各アカウント共通）

1. Instagram アカウントを新規作成（Threads は Instagram 連携が必須）→ 下記のユーザー名を使用
2. Threads アプリで該当 Instagram アカウントからログイン → プロフィール設定（下記コピペ）
3. アイコン: 下記プロンプトを画像生成AI（ChatGPT/Midjourney/Canva等）に貼って生成 → 正方形で書き出し
4. 固定投稿（下記）を投稿してプロフィールに固定
5. 2〜3日の手動ウォームアップ後、API 連携:
   - [Meta for Developers](https://developers.facebook.com/) でアプリに Threads ユースケースを追加 → 該当アカウントでアクセストークン発行（既存の婚活アカウントと同一アプリでOK。長期トークンの更新は既存の `refresh_threads_token.yml` を参照）
   - GitHub Secrets に登録: `THREADS_<キー>_USER_ID` / `THREADS_<キー>_ACCESS_TOKEN`
   - `config/accounts.json` の該当アカウントを `"enabled": true`
   - `cd affiliate-engine && node src/strategy-engine.js --from-file data/seed_templates.json` → コミット&プッシュ

---

## 1. 教育アカウント（推奨: 最初に開設）

| 項目 | 内容 |
|---|---|
| キー / Secrets | `education` / `THREADS_EDUCATION_*` |
| コンセプト | 小学生の子の習い事・プログラミング教育を「費用と続くか」で現実的に検討する保護者メモ。必修化・情報Ⅰに漠然と焦る親の「何をすればいいか分からない」に応える |
| ターゲット | 小学生の子を持つ30〜45歳の親 |
| 収益導線 | ヒューマンアカデミージュニア（資料請求・体験）+ 楽天（知育グッズ） |

**表示名（コピペ）**
```
はな｜小学生の習い事メモ
```

**ユーザー名候補（上から順に空きを確認）**
```
hana_naraigoto_memo
hana_manabi_memo
naraigoto_hana_note
```

**アイコン生成プロンプト（コピペ）**
```
温かみのあるフラットイラスト。ノートとえんぴつ、小さな星のモチーフを添えた、微笑む優しい雰囲気の女性の上半身。丸顔、ショートボブ。背景は明るいクリームイエローの単色。シンプル、清潔感、親しみやすい、絵本のようなタッチ。正方形、中央配置、円形トリミングでも顔が判別できる構図。文字なし。
```
```
English: Warm flat illustration of a friendly smiling woman (short bob hair, round face, upper body) with a notebook, pencil and small star motifs. Plain bright cream-yellow background. Simple, clean, approachable, picture-book style. Square, centered, readable when cropped to a circle. No text.
```

**プロフィール文（コピペ・全角139字）**
```
小学生の習い事を「月謝・送迎・続くか」で検討しては記録📚
プログラミング必修化と情報Ⅰ、気になるけど焦らない派。
体験・資料請求のレビューは正直に。紹介には #PR を付けます。
質問・体験談リプ歓迎です🙌
```

**固定投稿（コピペ）**
```
はじめまして。子どもの習い事を「なんとなく」で決めて後悔したことがある保護者です。

このアカウントでは
・習い事の費用と選び方のリアル
・プログラミング教育/ 情報Ⅰの情報整理
・体験レビュー（正直に書く・案件は #PR 表記）
を発信します。

みなさんの家の「習い事の月謝上限」、良かったら教えてください👇
```

---

## 2. 副業アカウント

| 項目 | 内容 |
|---|---|
| キー / Secrets | `sidejob` / `THREADS_SIDEJOB_*` |
| コンセプト | 「盛らない副業記録」。誰でも月◯万系が飽和する市場での逆張り信頼型。現実的な数字・失敗・経費も書く |
| ターゲット | 30〜40代の会社員・主婦 |
| 収益導線 | ココナラ / A8メディア会員 / mixhost / DMM FX（教育型・リスク明記のみ） |

**表示名（コピペ）**
```
ゆう｜盛らない副業メモ
```

**ユーザー名候補**
```
yu_moranai_fukugyo
yu_fukugyo_memo
moranai_sidework
```

**アイコン生成プロンプト（コピペ）**
```
フラットデザインのイラスト。ノートPCとコーヒーカップを前にした、落ち着いた雰囲気の30代日本人男性の上半身。シンプルな眼鏡、無地のシャツ。背景は濃紺（ネイビー）の単色。誠実、堅実、ミニマル。派手な要素・お金のモチーフ（札束・コイン）は入れない。正方形、中央配置、円形トリミング対応。文字なし。
```
```
English: Flat-design illustration of a calm Japanese man in his 30s (simple glasses, plain shirt, upper body) at a laptop with a coffee cup. Plain navy-blue background. Sincere, modest, minimal. No money motifs (no cash, no coins). Square, centered, circle-crop safe. No text.
```

**プロフィール文（コピペ・全角131字）**
```
会社員のまま、副業を現実的な数字で記録📝
うまくいった話より、失敗と経費を先に書く方針。
「誰でも簡単に稼げる」話は扱いません。
紹介する案件・サービスには #PR を付けます。
```

**固定投稿（コピペ）**
```
このアカウントの方針を最初に書いておきます。

・副業の収支は盛らずに書く（経費と作業時間も）
・「誰でも」「簡単に」「必ず」が付く話は扱わない
・紹介する案件には必ず #PR を付ける
・投資系はリスクがある前提でしか書かない

副業でいちばん知りたいのは成功談より「現実のペース」だと思うので、そこを担当します。

平日に副業へ使える時間、みんなは何分くらいありますか👇
```

---

## 3. 筋トレ（ボディメイク）アカウント

| 項目 | 内容 |
|---|---|
| キー / Secrets | `bodymake` / `THREADS_BODYMAKE_*` |
| コンセプト | デスクワーカーの「週2×30分」時短ボディメイク。体は台所で作る（食事7割）路線で、ガチ勢と差別化 |
| ターゲット | 30〜45歳のデスクワーク男性 |
| 収益導線 | Muscle Deli（宅食）/ HMBマッスルプレス（補助の位置づけ） |

**表示名（コピペ）**
```
たく｜週2ジムの30代
```

**ユーザー名候補**
```
taku_week2gym
taku_deskworker_fit
week2gym_taku
```

**アイコン生成プロンプト（コピペ）**
```
ミニマルなイラスト。ジムでダンベルラックの前に立つ男性の後ろ姿のシルエット（顔は見えない）。程よく引き締まった普通の体型（ボディビルダーではない）。背景はチャコールグレー、差し色にオレンジのライン。モダン、シンプル、清潔感。正方形、中央配置、円形トリミング対応。文字なし。
```
```
English: Minimal illustration, back-view silhouette of a man standing in front of a dumbbell rack at a gym (face not visible). Moderately fit average build, not a bodybuilder. Charcoal-gray background with an orange accent line. Modern, simple, clean. Square, centered, circle-crop safe. No text.
```

**プロフィール文（コピペ・全角129字）**
```
デスクワーク10年目。ジムは週2×30分だけ💪
体は台所で作る派（食事7割・トレ3割）。
コンビニ飯の選び方と、やめない仕組みを発信。
宅食・サプリの紹介には #PR を付けます。
```

**固定投稿（コピペ）**
```
筋トレアカウントですが、先に言っておくと週2×30分しかやりません。

発信するのは
・デスクワーカー向けの最小限メニュー
・コンビニと宅食でつくる高タンパクの食事
・「続かない」を仕組みで潰す方法
です。ストイックさは他の人に任せます。

ちなみにジム、何時に行く派ですか？朝・昼・夜で続きやすさが全然違う気がしてます👇
```

---

## 4. 美容アカウント

| 項目 | 内容 |
|---|---|
| キー / Secrets | `beauty` / `THREADS_BEAUTY_*` |
| コンセプト | 「がんばらない35歳からのケア」。成分マニア路線を避け、疲れた夜でも続く最低限ケアの共感型 |
| ターゲット | 35〜50歳の時間がない女性 |
| 収益導線 | オルビスユー ドット（トライアル→ライン使い） |

**表示名（コピペ）**
```
みほ｜がんばらないケア
```

**ユーザー名候補**
```
miho_yurucare
miho_gambaranai_care
yurucare_miho
```

**アイコン生成プロンプト（コピペ）**
```
柔らかいフラットイラスト。リラックスした表情で頬に手を当てる女性の上半身。ゆるくまとめた髪。そばにスキンケアボトルを1本だけ配置。背景は淡いベージュ〜ピンクベージュの単色。優しい、落ち着いた、清潔感のあるトーン。過度な華やかさなし。正方形、中央配置、円形トリミング対応。文字なし。
```
```
English: Soft flat illustration of a relaxed woman (loosely tied hair, upper body, hand gently on cheek) with a single skincare bottle beside her. Plain pale beige / pink-beige background. Gentle, calm, clean tone, not glamorous. Square, centered, circle-crop safe. No text.
```

**プロフィール文（コピペ・全角133字）**
```
仕事と家のことで手一杯な30代後半のスキンケア記録🧴
疲れた夜は「落とす+保湿」の2工程まで削る派。
続けられるケアしか紹介しません。感じ方には個人差があります。
紹介品には #PR を付けます。
```

**固定投稿（コピペ）**
```
スキンケア、10工程やってた時期より2工程に減らした今のほうが調子がいい、という体験からこのアカウントを始めました。

発信すること
・疲れた夜の「最低限ケア」の組み立て方
・続かない原因を仕組みで潰す話
・試したものの正直な感想（#PR 表記あり・感じ方は個人差あり）

夜のスキンケア、現実的に何分かけられてますか？👇
```

---

## 開設後チェックリスト（各アカウント）

- [ ] プロフィール・アイコン・固定投稿を設定した
- [ ] 手動ウォームアップ 2〜3日（1日2投稿+同ジャンルの投稿5件にまともなコメント）
- [ ] Meta for Developers でトークン発行 → Secrets 登録（`THREADS_<キー>_USER_ID` / `_ACCESS_TOKEN`）
- [ ] `config/accounts.json` を `enabled: true` にしてスケジュール再生成→コミット
- [ ] `config/links.json` の該当ジャンルのリンクを設定（A8で発行→短縮URL化）
- [ ] 翌日以降、Actions の実行ログと投稿を目視確認
