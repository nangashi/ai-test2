import logging
import os

import boto3

logger = logging.getLogger(__name__)


def get_secret_value(secret_arn: str) -> str | None:
    """Secrets Managerからシークレット値を取得"""
    try:
        # Lambda環境ではboto3のデフォルト設定を使用
        secrets_client = boto3.client("secretsmanager")
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        logger.info(f"Successfully retrieved secret: {secret_arn}")
        return str(response["SecretString"])
    except Exception as e:
        logger.error(f"Failed to get secret {secret_arn}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None


class Settings:
    """アプリケーション設定を管理"""

    def __init__(self) -> None:
        # 環境変数からSecrets Manager ARNを取得
        slack_bot_token_arn = os.environ.get("SLACK_BOT_TOKEN_SECRET_ARN")
        slack_signing_secret_arn = os.environ.get("SLACK_SIGNING_SECRET_SECRET_ARN")

        logger.info(f"Token ARN: {slack_bot_token_arn}")
        logger.info(f"Signing ARN: {slack_signing_secret_arn}")

        # Secrets Managerから値を取得（環境変数がある場合は直接使用）
        self.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN") or (
            get_secret_value(slack_bot_token_arn) if slack_bot_token_arn else None
        )
        self.slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET") or (
            get_secret_value(slack_signing_secret_arn) if slack_signing_secret_arn else None
        )
        
        logger.info(f"Bot token retrieved: {'Yes' if self.slack_bot_token else 'No'}")
        logger.info(f"Signing secret retrieved: {'Yes' if self.slack_signing_secret else 'No'}")

        # AWS設定
        self.aws_region = os.environ.get("AWS_REGION", "ap-northeast-1")
        self.bedrock_region = os.environ.get("BEDROCK_REGION", "ap-northeast-1")

        # AI設定
        # Claude 4 Sonnetはinference profileを使用する必要がある
        self.ai_model_id = os.environ.get("AI_MODEL_ID", "apac.anthropic.claude-sonnet-4-20250514-v1:0")
        self.ai_max_tokens = int(os.environ.get("AI_MAX_TOKENS", "1000"))
        self.ai_temperature = float(os.environ.get("AI_TEMPERATURE", "0.7"))

        # システムプロンプト
        self.system_prompt = os.environ.get(
            "AI_SYSTEM_PROMPT",
            """あなたは親しみやすいSlack Botアシスタントです。
            日本語で自然に会話し、ユーザーを支援してください。
            簡潔で分かりやすい回答を心がけてください。""",
        )


# シングルトンインスタンス
settings = Settings()
