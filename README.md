# instagram-poster

Instagramへの自動投稿・インサイト自動収集を行うリポジトリ。
AI社員オフィスの `insta-engineer` 担当領域(構成案・キャプション・画像は他の係が作成し、ここでは公開とデータ収集のみを行う)。

## 0. 前提

- Instagramプロアカウント(ビジネス/クリエイター)とFacebookページの連携: 済み
- Meta for Developersアプリ登録: 済み(未登録の場合は https://developers.facebook.com/apps/ からアプリを作成し、Instagram Graph APIのプロダクトを追加してください)
- 長期アクセストークン: **未取得 → 下記1で取得**

## 1. 長期アクセストークンを取得する(Instagram直接ログイン方式)

本プロジェクトは「Instagram API with Instagram Login」方式を使う(Facebookページ経由の連携は不要)。

1. Meta for Developersでアプリを作成し、「Instagramでメッセージとコンテンツを管理」ユースケースを追加する
2. アプリのダッシュボードで、投稿・インサイト取得に必要な権限を追加する(「Go to permissions and features」から):
   - `instagram_business_basic`
   - `instagram_business_content_publish`
   - `instagram_business_manage_insights`
   - (`manage_comments` / `manage_messages` はユースケースの初期設定で自動付与されるが、今回は未使用)
3. 左メニュー「役割」→「アプリに人を追加」から、投稿したいInstagramアカウントを **Instagramテスター** として追加する
4. **スマホのInstagramアプリ側**で、設定 →「アプリとウェブサイト」→「テスター招待」から招待を承認する
5. ダッシュボードの「アクセストークンを生成する」セクションで「アカウントを追加」を押し、接続が完了すると長期アクセストークンが発行される
6. トークンは安全な場所(パスワードマネージャー等)に控える。チャットやコード内には直接書かないこと

**トークンの更新(有効期限は約60日)**: 期限が切れる前に、以下のエンドポイントを叩くと新しい60日間有効なトークンが発行される。

```bash
curl -i -X GET "https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token={現在のトークン}"
```

## 2. IG_USER_ID について

上記5のトークン生成画面に、IG_USER_ID(Instagramアカウントの数値ID)も一緒に表示される。改めてAPIで調べる必要はない。

⚠️ ダッシュボード上部に表示される「Instagramアプリ ID」(例: `2520133505101...`)とは**別物**なので混同しないこと。`IG_USER_ID` はアクセストークン生成画面で確認できるアカウント側のID(例: `17841443980439894` の形式)。

## 3. GitHubリポジトリを作成してpushする

```bash
cd instagram-poster
git init
git add .
git commit -m "chore: initial setup"
gh repo create instagram-poster --private --source=. --remote=origin
git push -u origin main
```

## 4. GitHub Secretsを設定する

```bash
gh secret set IG_USER_ID
gh secret set IG_ACCESS_TOKEN
```

(それぞれ実行するとプロンプトで値の入力を求められます)

## 5. 投稿する

1. `queue/<post_id>/` フォルダに `caption.txt` と画像(`01.png`, `02.png`...)を配置(詳細は [queue/README.md](queue/README.md))
2. `git add`, `commit`, `push`
3. GitHubの Actions タブ →「Publish Instagram Post」→ Run workflow →`post_id`にフォルダ名を入力して実行
4. 公開されたメディアIDがログに出力され、成功後は `queue/<post_id>/` が自動で `published/<post_id>/` に移動する

投稿前に `insta-checker` の検品(合格判定)を経ていることを確認してから実行すること。

## 6. インサイト収集

`Collect Instagram Insights` ワークフローが毎日自動実行され、`data/insights/insights.csv` に新規投稿分のデータが追記される。手動実行も可能(Actionsタブから workflow_dispatch)。

**既知の制限**: Graph APIから取得できるのは `reach, saved, likes, comments, shares` のみ。「ホーム率」のような発信元別の内訳はAPIから直接取得できないため含まれない。`insta-analyst` はこのCSVと `followers_count_snapshot` を元に保存率・フォロー率等を算出すること。

## ローカルで動作確認する場合

```bash
pip install -r requirements.txt
cp .env.example .env  # IG_USER_ID / IG_ACCESS_TOKEN を記入
export $(cat .env | xargs)
export GITHUB_REPOSITORY="owner/instagram-poster"
export GITHUB_SHA="<pushしたコミットのSHA>"
python scripts/post_to_instagram.py <post_id>
```
