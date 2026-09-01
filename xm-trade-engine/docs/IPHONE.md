# iPhone だけで XM 自動売買を回す

人間の手元は iPhone だけ、という前提の手順の正。
**iPhone の XM / MT5 アプリでは EA（自動売買）は動かない。** 常駐するのは安い Windows VPS 上の MT5。iPhone は Remote Desktop で一度載せ、あとは GitHub Issue で監視・停止する。

> デモが先。実口座はまだ。リスク上限（0.5% / 日次 2% / 0.10 lot）は上げない。
> Threads の schedule は戻さない。Grok に XM ログインさせない。

いまの固定値:

| 項目 | 値 |
|---|---|
| デフォルトブランチ | `claude/setup-colab-comfyui-Eb9Lh` |
| 追跡 Issue | https://github.com/fireworker011/Research/issues/93 |
| Issue 番号（EA 入力） | `93` |
| Grok dump | `xm-trade-engine/docs/grok-bots/G_xm_trade.txt` |

---

## 全体像

```
iPhone
  ├─ Safari: VPS 契約・GitHub Issue・PAT
  ├─ Microsoft Remote Desktop: 初回だけ MT5 に EA を載せる
  └─ Grok Bot: Issue #93 を読む。止めるとき HALT 1行
        │
Windows VPS（24時間起動）
  └─ XM デモ MT5 + XMGoldSemi.mq5
        │  約定 / 決済
Issue #93 に xm-fill: / xm-close:
```

---

## A. GitHub（iPhone の Safari）

### A1. 通知

1. GitHub アプリまたは Safari で https://github.com/fireworker011/Research/issues/93 を開く。
2. Subscribe / 購読を ON。コメントが来たらバナーが来るようにする。

### A2. PAT（トークン）

1. Safari で GitHub にログイン。
2. 右上アイコン → Settings → Developer settings → Personal access tokens。
3. Fine-grained ならこのリポジトリだけ。権限:
   - Contents: **Read**
   - Issues: **Read and Write**
4. 生成された `ghp_...` をパスワードマネージャに保存。スクショをカメラロールに置きっぱなしにしない。
5. Git にコミットしない。Grok に渡さない。Issue に貼らない。

---

## B. XM デモ口座（iPhone の XM アプリで開いてよい）

1. App Store で XM の公式アプリを入れる。
2. **デモ口座**を開く（リアルはまだ）。
3. 口座番号と MT5 パスワードを控える（VPS の MT5 ログインに使う）。
4. アプリでチャートを見るのは確認用。**自動売買はアプリでは絶対に始まらない。**

---

## C. Windows VPS を iPhone から契約する

PC は買わない。ブラウザで Windows の仮想マシンを借りる。

選ぶ条件（これ以外は妥協してよい）:

- OS が **Windows Server**（Linux 不可）
- 24時間起動
- リモートデスクトップ（RDP）付き
- 目安: 1vCPU / RAM 2GB 以上。MT5 1つなら足りる

日本から契約しやすい例: ConoHa、さくらのVPS（Windows）、海外なら Contabo。料金は変動するので画面の表示に従う。

契約後メールに来るもの:

- IP アドレス（例 `123.45.67.89`）
- ユーザー名（よくあるのは `Administrator`）
- パスワード

これをパスワードマネージャに入れる。

---

## D. iPhone から VPS に入る

1. App Store で **Microsoft Remote Desktop**（Windows App）を入れる。
2. 右上 ＋ → Add PC。
   - PC name: VPS の IP
   - User account: メールのユーザー名とパスワード
3. 接続する。証明書警告は「一度だけ信頼」でよい（自分の VPS の場合）。
4. デスクトップが見えたら成功。以降、EA を載せる作業は全部この画面の中。

画面が小さいときは VPS 側で解像度を下げるか、ピンチインする。

---

## E. VPS 上で MT5 を入れる

Remote Desktop の中で:

1. Edge / Chrome を開く。
2. XM 公式から **MT5 Windows** をダウンロードしてインストール。
3. MT5 を起動 → デモの口座番号 / パスワード / サーバー（メールに書いてある XM サーバー名）でログイン。
4. 気配ウィンドウに `GOLD` または `XAUUSD` があるか確認。無い方の名前は使わない。
5. その銘柄をダブルクリックし、時間足を **M15** にする。

---

## F. EA ファイルを VPS に置く

リポジトリは private なので、VPS のブラウザでも GitHub にログインする。

1. https://github.com/fireworker011/Research を開く。
2. ブランチが `claude/setup-colab-comfyui-Eb9Lh` であることを確認。
3. `xm-trade-engine/ea/XMGoldSemi.mq5` を開き、Raw → 名前を付けて保存。
4. 同じフォルダの `xm_notify.mqh` も保存。
5. MT5 で File → Open Data Folder。
6. `MQL5` → `Experts` を開く。
7. 保存した **2ファイルを両方** `Experts` に入れる（`mqh` を別フォルダにしない）。

MT5 の Navigator → Expert Advisors を右クリック → Refresh。

---

## G. コンパイルして載せる

1. MT5 で MetaEditor を開く（ツール → MetaQuotes Language Editor）。
2. `XMGoldSemi.mq5` を開いてコンパイル（Compile）。エラー 0 を確認。
3. MT5 に戻り、Navigator から `XMGoldSemi` を **GOLD M15 チャートへドラッグ**。
4. 共通タブ:
   - 自動売買を許可
   - DLL は不要（オフのままでよい）
5. 入力タブ:

| 入力 | 値 |
|---|---|
| `CommanderURL` | `https://api.github.com/repos/fireworker011/Research/contents/xm-trade-engine/output/state/commander.json?ref=claude/setup-colab-comfyui-Eb9Lh` |
| `CommanderAuthHeader` | `Authorization: token ` の直後に A2 の PAT（スペースは token のあと1つ） |
| `GitHubRepo` | `fireworker011/Research` |
| `NotifyIssueNumber` | `93` |
| `NotifyEnabled` | true |
| `AutoOco` | true |
| `SlackWebhookURL` | 空 |

6. OK。
7. MT5 → ツール → オプション → エキスパートアドバイザ → **WebRequest で許可された URL** に `https://api.github.com` を追加して OK。
8. ツールバーの **AutoTrading** を緑にする。
9. チャート左下に `cmd=PAPER_ONLY` `auto=yes` `notify_issue=93` が出れば通信成功。
10. Experts タブに `commander HTTP 401/404` が無いか見る。401 は PAT、404 は URL。

同じチャートに他の EA を付けない。EURUSD 用 `XMGrokEngine` は今日は載せなくてよい。

---

## H. iPhone を切る

Remote Desktop を切っても VPS と MT5 は動き続ける。それが常駐。  
iPhone を閉じる前に AutoTrading が緑であることだけ確認する。

VPS を「停止」してはいけない。課金を止める停止と、RDP 切断は別。切断はしてよい。電源オフはだめ。

---

## I. Grok Bot（iPhone）

`xm-trade-engine/docs/grok-bots/G_xm_trade.txt` の中身だけを貼る。月100万 dump と混ぜない。

Grok の仕事:

- Issue #93 を読む
- `xm-fill:` / `xm-close:` を人間に要約する
- おかしいときだけ Issue に `KILL_SWITCH: HALT` の1行
- 普段はコメントしない。XM にログインしない。ENTRY しない

---

## J. 毎日の iPhone 操作

何もしない日が正しい。見るのはこれだけ。

1. GitHub の通知、または https://github.com/fireworker011/Research/issues/93
2. サーバー時刻 7:00 以降（XM はだいたい UTC+2。日本時間の昼過ぎ）に pending が付いたか、VPS に入ってターミナルで確認してもよい
3. 約定したら Issue に `xm-fill:`、決済で `xm-close:`

緊急停止（iPhone の GitHub から Issue #93 にコメント）:

```
KILL_SWITCH: HALT
```

今日の Gold だけ休む:

```
SKIP: GOLD
```

`RESUME` は書かない（リアル解禁）。

---

## K. 動いたかの目安（ブローカーサーバー時刻）

MT5 右下の時計。日本時間ではない。

| サーバー | 何が起きるか |
|---|---|
| 0:00–7:00 | アジア計測。pending なし |
| 7:00 過ぎ | 青/赤ライン。Issue に `gold-notice:` |
| 7:00–11:00 | Buy Stop と Sell Stop が2本 |
| 片方約定 | 反対削除。`xm-fill:` と Alert |
| 決済 | `xm-close:` |
| 11:00 | 残り pending 取消 |
| 月初金曜 | 休む（正常） |

---

## まだやらないこと

- リアル口座
- Issue に `KILL_SWITCH: RESUME`
- iPhone の XM アプリに自動を期待する
- Grok に XM のパスワードを渡す
- VPS を毎日シャットダウンする
- リスク%や 0.10 lot 上限を上げる
