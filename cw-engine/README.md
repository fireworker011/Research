# CW Engine — 全自動受注の司令塔

CrowdWorks の **選定と下書きはルール、司令塔は停止判断、応募送信は人間**。
Affiliate / XM と同じく GitHub 上で保守し、Grok Bot は dump **1ファイル**だけ開く。

> **最初に正直な前提を。** クラウドワークスに公式の応募 REST API は無い。
> ログイン自動化・非公式スクレイピング応募は、利用規約第22条（無断アクセス・運営妨害）と AI ポリシー（迷惑行為）に触れる。
> このエンジンは「Bot が会員ページに入って応募する」機械ではない。
> remain / n10 の毎晩宿題は **駐車のまま**。引用1手は替えない。

正本: [`docs/AUTO.md`](docs/AUTO.md)。役の数: [`docs/AGENTS.md`](docs/AGENTS.md)。懸念: [`docs/CONCERNS.md`](docs/CONCERNS.md)。Grok の1行: [`docs/COMMANDS.md`](docs/COMMANDS.md)。

```
Grok Bot（司令塔・1体）
  Issue「Grok Bot — 指示」の CW: GO でこの dump を開く
  Issue「CW — 司令塔」の cw-desk: を写す
  止めるときだけ CW: HALT
  応募送信は出さない
        │
Cursor（仕組み）                 GitHub（キュー + 報告）
  資格判定・応募稿・納品パイプライン    capability → queue.json → TODAY.md
        │                                │
        └──────────┬─────────────────────┘
                   ▼
            人間が fireworker12 で送信・契約・納品ボタン・出金
```

| 役割 | やる | やらない |
|---|---|---|
| **qualify / queue** | 公開文から作ったレコードを allowlist で落とす。重複・終了・実績必須を拒否 | ログイン、応募 POST、カタログ円を approved にする |
| **Grok Bot** | デスクを写す。HALT。日常チャット | 仕事 ID を足す、N=10、XM/AFFI と結合、2体目を作る |
| **Cursor** | 環境、完成稿、納品の仕組み | 毎晩の応募指示、ログイン確認ループ |
| **ナオミチ** | ログイン、送信、契約、素材受領、納品ボタン、出金 | コード、dump 結合、円の発明 |

## スイッチ

Issue `Grok Bot — 指示` に1行:

- `CW: GO` — dump を `cw-engine/docs/grok-bots/G_cw.txt` へ
- `CW: STOP` — XM に戻す
- `AFFI: GO` と同時は **後に書いた行が勝つ**。混ぜて読まない

`G_hq_cw_remain.txt` と `G_hq_cw_n10.txt` は開けない。

## 検証

```bash
cd cw-engine
node src/self-test.js
node src/report.js
```
