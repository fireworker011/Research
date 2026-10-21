# YouTube の準備

確認日: 2026-10-21。登録、許可、審査申請、投稿はここではしない。押すのはナオミチ。

プロジェクトは1つ。5チャンネルで共有する。枠はプロジェクト単位で、チャンネルを増やしても増えない。枠を増やすためにプロジェクトを分けない。追加は下の監査フォームだけ。

各チャンネルは別のGoogleアカウント。OAuthクライアントは1つで、refresh token はアカウントごとに別。

## いまの仕様

- アップロードは `videos.insert`。既定は1日100回、1回1ユニット。バケットは `videos.insert` 専用。日付が変わると太平洋時間の深夜に戻る。
  - https://developers.google.com/youtube/v3/docs/videos/insert （2026-10-15 更新）
  - https://developers.google.com/youtube/v3/determine_quota_cost
  - https://developers.google.com/youtube/v3/getting-started （2026-10-15 更新。アップロードは1ユニット、と書いてある）
- それ以外のメソッドは、合計1日10,000ユニット。`channels.list` と `videos.list` は1回1ユニット。
- 2025-12-04 にアップロードのコスト表記が約1600から約100へ変わり、2026-06-01 に `videos.insert` が独立バケットになった。古い記事の「1日6本」は現行のページと違う。正は上の3URL。
  - https://developers.google.com/youtube/v3/revision_history
- 100回を超える枠は、監査のあとでしか増えない。
  - https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits
- 予約は `status.publishAt`。公開状態は `private` とセットで、時刻は未来の ISO 8601。その時刻に公開になる。過去の時刻はすぐ公開になる。限定公開の予約は無い。
  - https://developers.google.com/youtube/v3/docs/videos （`status.publishAt`）
- タイトルは100文字まで。説明は5000バイトまで。`<` と `>` は使えない。
- A8の動画は説明に「アフィリエイト広告を含みます」を入れる。スクリプトは `--a8` のとき、これと `paidProductPlacementDetails.hasPaidProductPlacement=true` を付ける。
- 子ども向けかは `status.selfDeclaredMadeForKids`。スクリプトは `--made-for-kids` か `--not-made-for-kids` を必須にしている。
- 使うスコープは `youtube.upload` と `youtube.readonly`。期間内の再生数まで取るときだけ `yt-analytics.readonly` を足す。削除できる `youtube.force-ssl` は使わない。
  - https://developers.google.com/youtube/v3/guides/auth/installed-apps

## 未監査アプリと、API監査は別

1. OAuthの同意画面が Testing のあいだ、テストユーザーの refresh token は同意から7日で切れる。テストユーザーは100人まで。
   - https://support.google.com/cloud/answer/10311615
   - https://developers.google.com/identity/protocols/oauth2
2. アプリを本番公開したあとも、機微スコープの確認が終わるまでは「未確認のアプリ」と出る。この警告が出るアプリは、新規ユーザーがプロジェクトの生涯で100人まで。
   - https://support.google.com/cloud/answer/7454865
   - https://support.google.com/cloud/answer/15549945
3. スコープ確認の目安（保証ではない）: ブランド確認 2〜3営業日、機微スコープはサポートの表で10営業日。開発者向けの別ページは機微スコープを通常3〜5営業日と書いている。制限付きスコープは約6週間。追加したスコープがどちらに入るかは、同意画面の表が正。
   - https://support.google.com/cloud/answer/13463817
   - https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification
4. YouTube APIのコンプライアンス監査は、上とは別のフォーム。既定の100回/日を超えるときに必要。返信時期は「as soon as possible」とだけ書いてあり、日数は無い。
   - フォーム: https://support.google.com/youtube/contact/yt_api_form
5. `videos.insert` の現行ページは「未監査プロジェクトからのアップロードは非公開視聴に制限されない」と書いている。2020-07-28 の改定履歴には、それ以降に作った未監査プロジェクトは非公開になる、と残っている。挙動が履歴どおりなら、Studioで公開へ切り替える。
   - https://developers.google.com/youtube/v3/docs/videos/insert
   - https://developers.google.com/youtube/v3/revision_history

100回/日で足りるあいだ、監査フォームは出さなくてよい。7日で切れるトークンを避けたいときは、下の「本番公開」だけ行う。警告を消したいとき、または枠を増やすときに申請する。

## ナオミチが押す場所

使うブラウザはシークレットウィンドウ。チャンネルが変わるたびに、そのチャンネルのGoogleアカウントで開く。

1. https://console.cloud.google.com/ を、プロジェクトを持つ1つのGoogleアカウントで開く。
2. 上部のプロジェクト選択 → 新しいプロジェクト → 名前（例: channel-desk）→ 作成。
3. そのプロジェクトを選んだまま、APIライブラリで YouTube Data API v3 を有効にする。
   - https://console.cloud.google.com/apis/library/youtube.googleapis.com
4. 期間内の再生数を使うなら YouTube Analytics API も有効にする。累計の再生数だけなら不要。
   - https://console.cloud.google.com/apis/library/youtubeanalytics.googleapis.com
5. 「Google Auth Platform」を開く（古い画面名は OAuth 同意画面）。
   - Branding: アプリ名、サポートメール、デベロッパーの連絡先。アプリ名は「チャンネル机」など自前の名前にする。
   - Audience: External、公開ステータスは Testing。
   - Data Access → Add or remove scopes。`youtube.upload` と `youtube.readonly` を追加。表が Sensitive か Restricted かを控える。Analytics を使うときだけ `yt-analytics.readonly` も追加。
   - Audience のテストユーザーに、5チャンネルのGoogleアカウントを追加する。メールアドレスはこのリポジトリへ書かない。
6. 認証情報 → 認証情報を作成 → OAuth クライアント ID → デスクトップアプリ。JSONをダウンロードし、`secrets/youtube-client.json` として置く。中身はコミットしない。承認済みリダイレクトURIに `http://127.0.0.1:8765/` が無ければ追加する。
7. チャンネルごとに、シークレットウィンドウで次を実行する。同意画面では、必ずその動画のチャンネル（ブランドアカウント）を選ぶ。

```bash
cd affiliate-shorts/posting-api
python3 auth_youtube.py --channel pet_story_select
```

表示されたチャンネル名が `channels.json` と違うときは、タイトルかハンドルを表示どおりに直す。トークンは保存済みなので、許可はやり直さない。終了コード 4 がその状態。

同じことを次の key でも行う。

| key | チャンネル | ログインの目印 |
| --- | --- | --- |
| pet_story_select | @pet_story_select | fireworker01 |
| yoru_neko_camera | よるのねこカメラ日記 | fireworker06 |
| sonae_30 | 30秒そなえ帳 | fireworker04 |
| yoru_no_tana | よるの棚 / @夜の棚 | 依頼文に無い。許可したアカウントを手元に控える |
| nemuri_no_tana | ねむりの棚 | fireworker011 |

期間内再生数も取るなら、許可コマンドに `--with-analytics` を付ける。スコープを後から足すと、そのアカウントは許可のやり直しになる。

8. Testing のまま運用するなら、7日ごとに同じコマンドをやり直す。7日で切れたくなければ、Audience でアプリを Publish して本番にする。未確認の警告が出たら、詳細（Advanced）からアプリへ進む。文言はアカウントの言語で変わる。ユーザー上限は100人で、この5アカウントは収まる。

トークンの置き場は `tokens/youtube/<key>.json`。環境変数にするなら `YOUTUBE_CLIENT_ID`、`YOUTUBE_CLIENT_SECRET`、`YOUTUBE_REFRESH_TOKEN`。ファイルがあるときはファイルを使う。

取り消しは https://myaccount.google.com/permissions （開発者ポリシーが示すページは https://security.google.com/settings/security/permissions ）。

## 監査フォームを出すとき

100回/日で足りるなら、この節は後でよい。

1. `review/` のプライバシーポリシーと利用規約の `[運営者名]` `[連絡先メール]` `[公開日]` を埋める。
2. 別の公開リポジトリの `docs/` に `review/*.html` をコピーし、GitHub Pages を有効にする。この Research リポジトリ自体は Pages にしない。
3. 非公開で1本上げるところから、Studioでその動画を開くところまでを画面録画する。内部ツールなので、フォームのデモ用パスワード欄には本番のパスワードを書かない。録画のURLを「Other Supporting Materials」に置く。
4. https://support.google.com/youtube/contact/yt_api_form を、プロジェクトを作ったGoogleアカウントで開く。
5. 理由はコンプライアンス監査。枠の増加が不要なら、増加ではなく監査の選択肢を選ぶ。
6. アプリ名、PagesのURL、プライバシーポリシーのURLを入れる。APIクライアントは1つ。プロジェクト番号はコンソールのダッシュボードに出る数字。
7. 用途は、自社チャンネルへの動画アップロード（内部ツール）。第三者のチャンネルへ上げる機能は無い、と書く。
8. 使うメソッドは `videos.insert`、`videos.list`、`channels.list`。Analytics を有効にしたときだけ reports.query。
9. 証拠として、同意画面、スコープ、取り消し画面、アップロードの画面を添える。貼る文面は `review/APPLICATION_DRAFT.md`。

ポリシー: https://developers.google.com/youtube/terms/developer-policies
