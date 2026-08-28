# BOX_MEMORY — ブラウザは1つ

sprint dump 用コピー（元 `cursor/video-channel-playbook-e013`）。IMAGE_PLAYBOOK から先に開く。秋バナーを Imagine で作り直すな。出品するな。

手足はこのファイルを読んで実行する。市場リサーチの公開事実と、下の実測だけ。推論するな。書いていない回避は **INSUFFICIENT**。売上予想を書くな。円は全行 **無い**。`agents/` 本文は直すな。

Imagine の作り方は [IMAGE_PLAYBOOK.md](IMAGE_PLAYBOOK.md)。

---

## 0. 確定（司令部）

| 規則 | 値 |
|---|---|
| 同時に開いてよいブラウザ | **1つ** |
| Canva / Imagine / CrowdWorks（CW） | **並らない** |
| ファイルに無い回避 | **INSUFFICIENT** |
| 円 | 全行 **無い** |
| Imagine × タブ数 | **公式無い** |
| タブ上限 N | **無い**（Chrome / Canva とも公式に N は無い） |

並らない = 3つのうち2つ以上を同じ時刻に開かない。

---

## 1. 実測（2026-08-26）箱の box-doctor

| 表示 | 値 |
|---|---|
| Chrome | **26プロセス** |
| Canva | **Error 9** |
| Imagine | ページがメモリ不足で落ちる |
| その他 | `browser driver shell failed` が複数 |

Imagine のメモリ落ち条件は公式に無い（IMAGE_PLAYBOOK §3）。Error 9 の公式定義URLは **INSUFFICIENT**。意味を推測するな。

---

## 2. 公開事実（URL）

| 事実 | 出典 |
|---|---|
| Chrome: エラーメッセージが出ているタブ**以外**のすべてのタブを閉じる。実行中の他アプリを終了する。不要な拡張機能をアンインストールする | https://support.google.com/chrome/answer/142063?hl=ja |
| Chrome のタブ上限 N | **無い**（上のヘルプに N は無い） |
| Canva: 使っていない他のアプリやタブを閉じる | https://www.canva.com/help/canva-crash-freeze/ |
| Canva のタブ上限 N | **無い**（上のヘルプに N は無い） |
| Imagine × タブ数 | **公式無い** |
| grok.com は Chrome / Chromium | https://docs.x.ai/grok/faq |
| Canva Error 9 の公式定義 | **INSUFFICIENT** |
| `browser driver shell failed` の公式修復 | **INSUFFICIENT** |
| 円 | **無い** |

Chrome ヘルプは再起動・再インストールも書く。本ファイルの実行に入れるのは、市場リサーチが挙げた次だけ: エラータブ以外を閉じる / 他アプリ終了 / 拡張削除。それ以外は **INSUFFICIENT**。

---

## 3. 開く前（毎回）

1. Canva を閉じる。
2. grok.com / Imagine を閉じる。
3. CrowdWorks を閉じる。
4. 残すブラウザは **1つ**。
5. 今の仕事のサイトを **1つ** だけ開く。

| 今の仕事 | 開いてよいもの | 閉じたまま |
|---|---|---|
| 画像生成 | grok.com/imagine だけ | Canva、CW、他 |
| Canva | Canva だけ | Imagine、CW、他 |
| CW 応募 | CrowdWorks だけ | Canva、Imagine、他 |

---

## 4. 実行中に落ちたら

公式にある手順だけ。N 個まで開け、は無い。

| 起きたこと | やる（公式または確定） | やるな |
|---|---|---|
| Chrome がエラーを出す | エラーが出ているタブ以外を閉じる。他アプリを終了する。不要な拡張をアンインストールする。残すブラウザは1つ | タブ上限 N を決める。Imagine×タブ数を発明する |
| Canva Error 9 / 落ちる | 未使用の他アプリ/タブを閉じる。Imagine と CW は閉じたまま。公式定義は INSUFFICIENT | Error 9 の意味を推測する |
| Imagine がメモリ不足で落ちる | メモリ落ち条件は公式に無い。確定どおり Canva と CW を閉じ、ブラウザ1つで Imagine を1回だけ開き直す | タブ数とメモリの公式関係を書く |
| `browser driver shell failed` | 表示を記録して止まる | ドライバ再インストール |

開き直しは **1回**。2回目も落ちたら **INSUFFICIENT**。

---

## 5. 切り替えるとき

1. 今のタブを閉じる（最小化は閉じたことにしない）。
2. Canva / Imagine / CW がゼロであることを確認する。
3. 次のサイトを1つ開く。

---

## 6. 返したら終わり（記録）

```
日付:
Chrome窓の数: 1 / 2以上（2以上なら開くな）
開いているサイト: Imagineのみ / Canvaのみ / CWのみ / それ以外
Canva Error 9: 出た / 出ていない
Imagineメモリ不足: 出た / 出ていない
browser driver shell failed: 出た / 出ていない
Chromeプロセス数: （測った値。無ければ「測っていない」）
タブ上限N: 無い
Imagine×タブ数: 公式無い
円: 無い
判定: このファイルどおり / INSUFFICIENT
```

---

## 7. ファイルに無いもの（INSUFFICIENT）

- ブラウザ2つ以上を同時に開いてよい条件
- Canva / Imagine / CW の同時起動
- Imagine × タブ数
- タブ上限 N
- Error 9 の公式意味
- Chrome ヘルプにあるが本ファイルに書いていない手順（再起動、再インストール、別ブラウザ、ハードウェアアクセラレーション）
- 円（全行無い）
