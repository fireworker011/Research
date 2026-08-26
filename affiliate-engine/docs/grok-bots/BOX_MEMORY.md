# BOX_MEMORY — ブラウザは1つ

手足はこのファイルを読んで実行する。書いていない回避は **INSUFFICIENT**。発明するな。品質を推論するな。売上予想を書くな。`agents/` 本文は直すな。

Imagine の作り方は [IMAGE_PLAYBOOK.md](IMAGE_PLAYBOOK.md)。メモリ回避を IMAGE_PLAYBOOK 側で足すな。

---

## 0. 確定（これ以外は無い）

| 規則 | 値 |
|---|---|
| 同時に開いてよいブラウザ | **1つ** |
| Canva / Imagine / CrowdWorks（CW） | **並らない**（同時に開かない。タブもプロセスも） |
| ファイルに無い回避 | **INSUFFICIENT**。実行するな |

並らない = 3つのうち2つ以上を、同じ時刻に開かない。終わった方を閉じてから次を1つ開く。

---

## 1. 実測（2026-08-26）箱の box-doctor

推論ではない。今夜出た表示だけ。

| 表示 | 値 |
|---|---|
| Chrome | **26プロセス** |
| Canva | **Error 9** |
| Imagine | ページがメモリ不足で落ちる |
| その他 | `browser driver shell failed` が複数 |

Error 9 の公式定義ページは取れず **INSUFFICIENT**（§3）。意味を推測して直すな。

---

## 2. 開く前（毎回）

1. Canva を閉じてることを確認する。
2. grok.com / Imagine を閉じてることを確認する。
3. CrowdWorks を閉じてることを確認する。
4. 上以外のブラウザ窓も閉じる。残してよいブラウザは **1つ**。
5. 今から使うサイトを **1つ** だけ開く。

| 今の仕事 | 開いてよいもの | 閉じたまま |
|---|---|---|
| 画像生成 | grok.com/imagine だけ | Canva、CW、他 |
| バナー文字載せ（別ファイルに手順があるときだけ） | Canva だけ | Imagine、CW、他 |
| CW 応募 | CrowdWorks だけ | Canva、Imagine、他 |

IMAGE_PLAYBOOK に Canva 後載せ手順は無い。Canva を Imagine の代わりに開くな。

---

## 3. 公開事実（URL）

取れなかった項は INSUFFICIENT。

| 事実 | 出典 |
|---|---|
| Canva が落ちる・固まるとき、使っていない他アプリやタブを閉じる、と公式ヘルプが書く | https://www.canva.com/help/canva-crash-freeze/ |
| 同ページ: 対応ブラウザ、プライベート/インコグニト、キャッシュ削除、status.canva.com も列挙 | 同上。**本ファイルの実行手順には入れない**（§0: ファイルに無い回避は INSUFFICIENT。確定は「ブラウザ1つ」「3つを並らない」だけ） |
| grok.com は標準の Chrome / Chromium で、と FAQ が書く | https://docs.x.ai/grok/faq 「What's the correct web address — grok.com or grok.x.ai?」 |
| Canva **Error 9** という名称の公式ヘルプ | **INSUFFICIENT**（2026-08-26 に公式定義URLを取れない） |
| Chrome が 26 プロセスであることの公式上限 | **INSUFFICIENT** |
| `browser driver shell failed` の公式修復手順 | **INSUFFICIENT** |

---

## 4. 実行中に落ちたら

記録して止まる。次を発明するな。

| 起きたこと | やる | やるな |
|---|---|---|
| Imagine がメモリ不足で落ちる | Canva と CW が閉じているか確認する。ブラウザが1つか確認する。1つにしてから Imagine を1回だけ開き直す | 2つ目のブラウザ、拡張のON/OFF、キャッシュ削除、別PC、API 切替 |
| Canva Error 9 | Imagine と CW を閉じる。Canva だけ1つ。公式定義は INSUFFICIENT なので、閉じても同じ表示なら止まる | Error 9 の意味を推測する。インコグニト等の未記載回避 |
| `browser driver shell failed` | 表示を記録して止まる | ドライバ再インストール、再起動スクリプト |
| Chrome プロセスが多い | 規則どおり閉じる（残すブラウザは1つ） | プロセスを番号で殺す手順（本ファイルに無い） |

開き直しは **1回**。2回目も落ちたら **INSUFFICIENT**。3つ目の手段は書かない。

---

## 5. 切り替えるとき

1. 今のタブを閉じる（最小化は閉じたことにしない）。
2. 残っている Canva / Imagine / CW がゼロであることを確認する。
3. 次のサイトを1つ開く。

同時に3つを「裏でログイン維持」するな。

---

## 6. 返したら終わり（記録）

```
日付:
Chrome窓の数: 1 / 2以上（2以上なら開くな）
開いているサイト: Imagineのみ / Canvaのみ / CWのみ / それ以外
Canva Error 9: 出た / 出ていない
Imagineメモリ不足: 出た / 出ていない
browser driver shell failed: 出た / 出ていない
Chromeプロセス数: （測った値。測っていなければ「測っていない」）
判定: このファイルどおり / INSUFFICIENT（やった未記載回避を書くな。止まれ）
```

---

## 7. ファイルに無いもの（INSUFFICIENT）

- ブラウザ2つ以上を同時に開いてよい条件
- Canva と Imagine の同時起動
- Imagine と CW の同時起動
- Canva と CW の同時起動
- Error 9 の公式意味
- キャッシュ削除・拡張無効・インコグニト・VPN切断・再起動・別ブラウザへの乗り換え（公式ヘルプに書いてあっても、本ファイルの確定手順ではない）
- プロセス26を何個まで減らすかの数値目標
- 売上予想
