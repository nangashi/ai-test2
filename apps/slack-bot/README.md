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

### 3. AWS Bedrock利用準備

AWS Bedrockで利用可能なClaude 4モデルをリクエストする必要があります。

#### 3.1 Model Access Request
1. AWS Console → Bedrock → Foundation models → Model access
2. `Claude 4 Sonnet (us.anthropic.claude-sonnet-4-20250514-v1:0)` をリクエスト
3. 承認されるまで待機（通常数分～数時間）

### 4. AWS Secrets Manager設定

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

### 5. アプリケーションデプロイ

```bash
cd apps/slack-bot
./deploy.sh
```

### 6. Slack Event Subscriptions設定

#### 6.1 Event Subscriptions有効化
1. Event Subscriptions → ONに設定
2. Request URL: `https://your-function-url.lambda-url.ap-northeast-1.on.aws/`
   - Terraform outputの`lambda_function_url`を使用
3. URL検証が成功することを確認

#### 6.2 Bot Events設定
Subscribe to bot eventsで以下を追加:
- `app_mention`

#### 6.3 変更保存
Save Changesで設定を保存

### 7. Slackアプリインストール

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
- **Claude 4会話**: AWS BedrockでClaude 4 Sonnetと会話
  - 通常のメンション: Claude 4との新規会話
  - スレッド内メンション: 会話履歴を含めたClaude 4との継続会話
- **スレッド履歴取得**: 会話の文脈をClaudeに渡すための履歴読み込み
- **AI会話履歴管理**: Slackのスレッド履歴をClaude用のメッセージ形式に変換
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
- Lambda実行ロールは最小権限の原則に従って設定（Bedrock、Secrets Manager、CloudWatch Logsのみ）
- Function URLsはSlack署名検証で保護
- Bedrock利用によりAI処理がAWS内で完結