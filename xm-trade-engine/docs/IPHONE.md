# iPhone だけで XM 自動売買を回す（初めての人・生姜向け）

パソコンが無くても、iPhone だけで実装できる。ただし **iPhone の XM アプリに自動売買を載せることはできない。**  
やることは「安い Windows のレンタルパソコン（VPS）を借りて、そこに MT5 を置きっぱなしにする」こと。iPhone はその画面に一度入って設定し、あとは通知を見る。

この文書は **画面に出る言葉どおり** に進める。分からない英単語はコピペ欄をそのまま貼ればよい。

> デモ（練習用のお金）が先。本物の口座はまだ開かない。
> Threads の自動投稿は触らない。Grok に XM のパスワードを渡さない。

---

## 0. 先にメモアプリへコピペする（全部使う）

iPhone のメモを新規作成し、見出しごと貼る。あとで値を書き足す。

```
【Issue】
https://github.com/fireworker011/Research/issues/93
NotifyIssueNumber: 93

【CommanderURL】（1行のまま）
https://api.github.com/repos/fireworker011/Research/contents/xm-trade-engine/output/state/commander.json?ref=claude/setup-colab-comfyui-Eb9Lh

【GitHubRepo】
fireworker011/Research

【PAT】（あとで書く。ghp_ で始まる）
Authorization: token 

【XMデモ】
口座番号:
MT5パスワード:
サーバー名:

【VPS】
IP:
ユーザー名:
パスワード:
```

`Authorization: token ` のあとに半角スペースが1つ必要。PAT を発行したら、そのスペースの直後に貼る。

所要時間の目安: 初回 60〜90 分。2日目以降は iPhone で Issue を見るだけ。

---

## 1. GitHub の通知をオンにする（3分）

1. Safari で開く → https://github.com/fireworker011/Research/issues/93
2. GitHub にログインする。
3. 画面の **Subscribe**（購読）をオン。ベルのアイコンならそれをタップ。
4. iPhone の設定 → 通知 → GitHub がオンか確認（GitHub アプリを使っている場合）。

これで約定コメントが来たらバナーが出る。

---

## 2. PAT（鍵）を作る（10分）

EA が GitHub を読むための鍵。パスワードとは別物。

1. Safari を **デスクトップ用 Web サイトを表示** にする（AA アイコン → デスクトップ用）。
2. 開く → https://github.com/settings/tokens/new
3. Note（名前）に `xm-demo-mt5` と入れる。
4. Expiration は 90 days でよい（切れたら作り直す）。
5. スコープは **`repo` にだけチェック**。他は触らない。
6. 一番下の Generate token をタップ。
7. `ghp_` で始まる長い英数字が出る。**この画面は二度と出ない。**
8. メモの【PAT】を次の形にする（token のあと半角スペース、その直後に ghp_）:

```
Authorization: token ghp_ここに貼る
```

Grok に送らない。Issue に貼らない。写真をチャットに投げない。

---

## 3. XM のデモ口座を開く（15分）

1. App Store で **XM** と検索し、公式アプリを入れる（会社名が XM）。
2. アプリで口座開設。必ず **デモ**（練習）を選ぶ。リアル／ライブは選ばない。
3. メールに MT5 のログイン情報が来る。メモへ転記する。
   - 口座番号（数字）
   - パスワード
   - サーバー（`XMGlobal-MT5 2` のような名前。メールの表記をそのまま）
4. アプリでチャートが見られれば十分。**ここで自動は始まらない。正常。**

---

## 4. Windows VPS を借りる（20分）

家のパソコンの代わりに、インターネット上の Windows を月額で借りる。

### 選ぶもの（これだけ守る）

- 名前に **Windows** と書いてあるプラン
- **Linux / Ubuntu / Rocky / Debian は選ばない**（MT5 が入らない）
- 24時間つく
- リモートデスクトップ（RDP）が使える

日本の画面で進めやすい例: **ConoHa VPS** の Windows。他社でも Windows なら同じ。

### ConoHa での押し方（例）

1. Safari で ConoHa の公式を開き、会員登録・ログイン。
2. VPS を追加。イメージ／OS で **Windows Server** を選ぶ。
3. 一番安いプランでよい（メモリ 2GB 以上ならなお良い）。
4. ルートパスワードを自分で決めてメモの【VPS】パスワードへ。
5. 作成完了まで待つ（数分）。
6. コントロールパネルに **IPアドレス** が出る。メモの【VPS】IP へ。
7. ユーザー名はよく **Administrator**。画面に別の名前があればそれをメモる。

メールにも IP とパスワードが来る。届くまで次へ進まない。

---

## 5. iPhone から Windows 画面を開く（10分）

1. App Store で **Windows App** と検索（昔の名前は Microsoft Remote Desktop。発行元 Microsoft）。
2. 入れる → 開く。
3. 右上の **＋** → **Add PC**（PC を追加）。
4. PC name に、メモの VPS の IP をそのまま入れる（例 `123.45.67.89`）。
5. User account → Add User Account。
   - User name: `Administrator`（またはメモのユーザー名）
   - Password: VPS のパスワード
6. Save → その PC をタップして接続。
7. 「証明書を信頼しますか」→ **Trust / 信頼**（自分が今借りた機械なので）。
8. Windows のデスクトップ（真っ青や壁紙）が見えたら成功。

画面が小さい: 二本指でピンチイン。キーボードは画面上のキーボードアイコン。

**ここから先は、全部この Windows 画面の中でやる。** iPhone の XM アプリには戻らない。

---

## 6. Windows に MT5 を入れる（15分）

Windows 画面の中のブラウザ（Edge）で:

1. XM 公式の MT5 ダウンロードページを開く。検索して「XM MT5 ダウンロード」。
2. **Windows 版 MT5** をダウンロード。Mac / iOS は選ばない。
3. ダウンロードした `xmsetup.exe` のようなファイルを実行 → 次へ でインストール。
4. MT5 が開く → ログイン。
   - ログイン: メモの XM 口座番号
   - パスワード: メモの MT5 パスワード
   - サーバー: メールと同じ名前をリストから選ぶ
5. 左の **気配値表示**（Market Watch）に `GOLD` または `XAUUSD` があるか見る。
   - 無ければ気配値の空白で右クリック → シンボル表示 → gold で検索 → 表示。
6. `GOLD`（または `XAUUSD`）をダブルクリック。チャートが開く。
7. チャート上で右クリック → 時間足 → **M15**。  
   画面上の `M15` ボタンでもよい。**H1 や M1 にしない。**

---

## 7. 自動売買のプログラムを Windows に置く（15分）

GitHub は非公開なので、Windows の Edge でも GitHub にログインする（iPhone と同じアカウント）。

1. Edge で開く → https://github.com/fireworker011/Research
2. 左上付近のブランチ名が `claude/setup-colab-comfyui-Eb9Lh` か確認。違ったらその名前を選ぶ。
3. フォルダを順にタップ: `xm-trade-engine` → `ea`
4. `XMGoldSemi.mq5` を開く → 右上 **Raw** または Download → 保存。
5. 戻って `xm_notify.mqh` も同じように保存。
6. 保存先は通常 `ダウンロード`（Downloads）。
7. MT5 のメニュー **ファイル → データフォルダを開く**。
8. フォルダ `MQL5` を開く → `Experts` を開く。
9. ダウンロードした **2つのファイルを両方** `Experts` の中へコピーする。
   - `XMGoldSemi.mq5`
   - `xm_notify.mqh`
   - `mqh` だけ別の場所に置かない。同じ `Experts` の中。

MT5 左の **ナビゲーター** → エキスパートアドバイザ の上で右クリック → **更新**。

`XMGoldSemi` が見えれば成功。灰色のままでも次のコンパイルで直ることがある。

---

## 8. コンパイルしてチャートに付ける（20分）

### 8-1 コンパイル

1. MT5 メニュー **ツール → MetaQuotes Language Editor**（MetaEditor）。
2. 左の一覧から `XMGoldSemi.mq5` を開く。
3. 上の **Compile**（コンパイル）を押す。
4. 下の欄が `0 error(s)` なら成功。error が 1 以上なら、`xm_notify.mqh` が同じ `Experts` に無いか確認。

### 8-2 チャートにドラッグ

1. MetaEditor を閉じて MT5 に戻る。
2. ナビゲーター → エキスパートアドバイザ → `XMGoldSemi` を、**GOLD の M15 チャートへドラッグ**。
3. 窓が開く。

**共通** タブ:

- 「自動売買を許可する」にチェック
- 「DLL の使用を許可」はオフのまま

**入力** タブ（値はメモからコピペ。1文字も足さない）:

| 名前 | 入れる値 |
|---|---|
| CommanderURL | メモの【CommanderURL】1行 |
| CommanderAuthHeader | メモの【PAT】1行（`Authorization: token ghp_...`） |
| GitHubRepo | `fireworker011/Research` |
| NotifyIssueNumber | `93` |
| NotifyEnabled | true |
| AutoOco | true |
| SlackWebhookURL | 何も入れない |

4. OK。
5. MT5 **ツール → オプション → エキスパートアドバイザ**。
6. 「WebRequest を許可する URL」に次を1行追加:

```
https://api.github.com
```

7. OK。
8. ツールバーの **自動売買** ボタンを押して **緑** にする。赤のままだと発注しない。
9. チャートの **左下** に文字が出る。次が含まれていれば成功。
   - `cmd=PAPER_ONLY`
   - `auto=yes`
   - `notify_issue=93`

下の **Experts** タブ（ターミナル。Ctrl+T で出る）に `commander HTTP 401` なら PAT が違う。`404` なら URL が違う。`200` やエラー無しならよい。

同じチャートに他のロボットを付けない。

---

## 9. iPhone の画面を閉じる

1. 自動売買が緑か、もう一度見る。
2. Windows App を切る（iPhone のホームに戻る）。
3. VPS のコントロールパネルで **停止・シャットダウン・削除はしない。**

iPhone を切っても、借りた Windows と MT5 は動き続ける。それが自動化。

---

## 10. Grok Bot に命令を貼る

Grok Bot の指示欄に、次のファイルの中身 **だけ** を貼る。他の dump と混ぜない。

リポジトリの `xm-trade-engine/docs/grok-bots/G_xm_trade.txt`

貼ったあと Grok に言うことは:

```
この命令だけで動け。Issue https://github.com/fireworker011/Research/issues/93 を読め。XMにはログインするな。普段はコメントするな。
```

---

## 11. 毎日やること（iPhone で1分）

通常は **何もしない。** 見るのは Issue だけ。

https://github.com/fireworker011/Research/issues/93

| Issue に付くコメント | 意味 |
|---|---|
| `gold-notice:` | 今日のレンジが決まった。指令ではない |
| `xm-fill:` | エントリーした |
| `xm-close:` | 決済した |

全部止めるとき、Issue のコメント欄に **この1行だけ**:

```
KILL_SWITCH: HALT
```

今日の金だけ休む:

```
SKIP: GOLD
```

`RESUME` は書かない。

MT5 右下の時計は日本時間ではない（XM はだいたい UTC+2）。  
サーバー 7時〜11時（日本時間の昼過ぎ〜夕方）に、ターミナルの「取引」に Buy Stop と Sell Stop が2本付けば動いている。月初の金曜に付かないのは正常。

---

## うまくいかないとき

| 見た目 | やること |
|---|---|
| iPhone の XM アプリで注文が付かない | 仕様。VPS の MT5 を見る |
| Windows 画面に入れない | IP・ユーザー・パスワード。VPS が停止していないか |
| チャート左下が空白 | 自動売買が赤。EA が別の足についている |
| `HTTP 401` | PAT の行。`token` のあとスペース、`ghp_` の欠け |
| `HTTP 404` | CommanderURL をメモから貼り直し |
| pending が昼に付かない | サーバー時計が 7〜11 か。Experts に `asia skip` なら今日は見送り |
| Grok が「買え」と言う | dump が混ざっている。`G_xm_trade.txt` だけに差し替え |

---

## まだやらないこと

- リアル口座
- `KILL_SWITCH: RESUME`
- ロットを 0.1 固定にする
- VPS を毎日電源オフ
- Grok に XM のログインをさせる
