# Slack Bot Lambda Application

AWS LambdaとFunction URLsを使用したSlack Botアプリケーション。メンションに対して固定メッセージで応答します。

## アーキテクチャ

- **Lambda Function**: Python 3.11、Slack Bolt Framework
- **Function URLs**: 直接HTTPアクセス、Slack署名検証
- **Secrets Manager**: Bot Token、Signing Secretの安全な管理
- **Terraform**: インフラストラクチャ管理
- **lambroll**: アプリケーションデプロイ

## セットアップ

### 1. インフラストラクチャ構築

```bash
cd terraform/environments/dev
terraform init
terraform apply
```

### 2. Slackアプリ作成・設定

#### 2.1 Slack App作成
1. [Slack API](https://api.slack.com/apps) でNew Appを作成
2. From scratchを選択
3. App Name、Workspaceを設定

#### 2.2 Bot Token Scopes設定
1. OAuth & Permissions → Bot Token Scopesで以下を追加:
   - `app_mentions:read` (アプリメンション読み取り)
   - `chat:write` (メッセージ送信)
   - `channels:history` (チャンネル履歴読み取り)
   - `groups:history` (プライベートチャンネル履歴読み取り)
   - `im:history` (ダイレクトメッセージ履歴読み取り)
   - `mpim:history` (マルチパーティDM履歴読み取り)

#### 2.3 認証情報取得
- **Bot Token**: OAuth & Permissions → Bot User OAuth Token (`xoxb-...`)
- **Signing Secret**: Basic Information → Signing Secret

### 3. AWS Secrets Manager設定

```bash
# Bot Token設定
aws secretsmanager put-secret-value \
  --secret-id "slack-bot-dev-bot-token" \
  --secret-string "xoxb-your-actual-bot-token" \
  --region ap-northeast-1

# Signing Secret設定  
aws secretsmanager put-secret-value \
  --secret-id "slack-bot-dev-signing-secret" \
  --secret-string "your-actual-signing-secret" \
  --region ap-northeast-1
```

### 4. アプリケーションデプロイ

```bash
cd apps/slack-bot
./deploy.sh
```

### 5. Slack Event Subscriptions設定

#### 5.1 Event Subscriptions有効化
1. Event Subscriptions → ONに設定
2. Request URL: `https://your-function-url.lambda-url.ap-northeast-1.on.aws/`
   - Terraform outputの`lambda_function_url`を使用
3. URL検証が成功することを確認

#### 5.2 Bot Events設定
Subscribe to bot eventsで以下を追加:
- `app_mention`

#### 5.3 変更保存
Save Changesで設定を保存

### 6. Slackアプリインストール

1. OAuth & Permissions → Install to Workspaceでインストール
2. 権限を確認してAllow

## 動作テスト

1. SlackでBotをチャンネルにInvite: `/invite @your-bot-name`
2. Botにメンション: `@your-bot-name hello`
3. 「こんにちは！メンションありがとうございます。」の返信を確認

## 開発

### ファイル構成

```
apps/slack-bot/
├── src/
│   └── lambda_function.py      # メインアプリケーション
├── tests/
│   └── test_lambda_function.py # テスト
├── deploy.sh                   # ビルド・デプロイスクリプト
├── function.json              # lambroll設定
├── requirements.txt           # 依存関係
├── pyproject.toml            # プロジェクト設定
└── README.md                 # このファイル
```

### 機能

- **署名検証**: HMAC-SHA256によるSlack署名検証
- **URL verification**: Slack App初回設定時の検証対応
- **app_mention処理**: メンション受信時の応答
  - 通常のメンション: 挨拶メッセージ
  - スレッド内メンション: スレッド履歴表示（AI会話履歴のテスト用）
- **スレッド履歴取得**: 会話の文脈を把握するための履歴読み込み
- **エラーハンドリング**: 適切なHTTPステータスコード返信

### ローカル開発

```bash
# 依存関係インストール
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt

# テスト実行
pytest tests/

# デプロイ
./deploy.sh
```

### ログ確認

```bash
# CloudWatch Logs確認
aws logs tail /aws/lambda/slack-bot-dev --follow --region ap-northeast-1
```

## トラブルシューティング

### 署名検証エラー
- Signing Secretが正しく設定されているか確認
- Slack App設定のSigning Secretと一致するか確認

### Bot Token認証エラー
- Bot User OAuth Tokenが正しく設定されているか確認
- Bot Scopesが適切に設定されているか確認

### Event URL検証失敗
- Function URLがアクセス可能か確認
- Lambda関数がエラーなく起動するか確認
- CloudWatch Logsでエラー内容を確認

## セキュリティ

- Bot TokenとSigning SecretはSecrets Managerで管理
- Lambda実行ロールは最小権限の原則に従って設定
- Function URLsはSlack署名検証で保護