import json
import logging
import os
import urllib.parse
from typing import Any

from config.settings import settings
from slack.auth import verify_slack_signature
from slack.handler import handle_app_mention
from utils.http_response import create_response

# OpenTelemetryの基本設定（テレメトリーは無効化）
os.environ["OTEL_SDK_DISABLED"] = "true"

# ログレベル設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda関数のエントリーポイント（Function URLs対応）
    """
    try:
        # リクエストIDをログ出力
        request_id = getattr(context, 'aws_request_id', 'unknown') if context else "unknown"
        logger.info(f"=== Lambda invoked with request_id: {request_id} ===")
        # HTTPメソッドチェック
        if event.get("requestContext", {}).get("http", {}).get("method") != "POST":
            return create_response(405, "Method Not Allowed")

        # ヘッダーとボディを取得
        headers = event.get("headers", {})
        body = event.get("body", "")

        # Slackのリトライをチェック
        retry_num = headers.get("x-slack-retry-num")
        retry_reason = headers.get("x-slack-retry-reason")
        if retry_num:
            logger.warning(f"Slack retry detected: retry_num={retry_num}, reason={retry_reason}")
            # リトライの場合は即座にOKを返す
            return create_response(200, "OK")

        # 必要なヘッダーを取得
        slack_signature = headers.get("x-slack-signature")
        slack_timestamp = headers.get("x-slack-request-timestamp")

        if not slack_signature or not slack_timestamp:
            logger.warning("Missing Slack signature or timestamp")
            return create_response(400, "Bad Request")

        # 署名検証
        if not settings.slack_signing_secret:
            logger.error("SLACK_SIGNING_SECRET is not configured")
            return create_response(500, "Internal Server Error")

        if not verify_slack_signature(settings.slack_signing_secret, body, slack_timestamp, slack_signature):
            logger.warning("Invalid Slack signature")
            return create_response(401, "Unauthorized")

        # リクエストボディをパース
        try:
            if body.startswith("payload="):
                # URL-encodedの場合（Interactive Components）
                payload = urllib.parse.unquote_plus(body[8:])
                slack_request = json.loads(payload)
            else:
                # JSONの場合（Events API）
                slack_request = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Failed to parse request body")
            return create_response(400, "Bad Request")

        # URL verification（初回設定時）
        if slack_request.get("type") == "url_verification":
            return create_response(200, slack_request.get("challenge", ""))

        # Event callback処理
        if slack_request.get("type") == "event_callback":
            event_data = slack_request.get("event", {})
            event_id = slack_request.get("event_id")
            event_time = slack_request.get("event_time")
            
            # イベントIDをログ出力（重複チェック用）
            logger.info(f"Processing event_id: {event_id}, event_type: {event_data.get('type')}, event_time: {event_time}")
            logger.info(f"Event details: user={event_data.get('user')}, text={event_data.get('text', '')[:50]}...")

            # app_mentionイベントの処理
            if event_data.get("type") == "app_mention":
                # 自分自身のメッセージは無視（bot_idがある場合）
                if event_data.get("bot_id"):
                    logger.info("Ignoring bot's own message")
                    return create_response(200, "OK")
                    
                logger.info(f"Processing app_mention event from user {event_data.get('user')}")
                handle_app_mention(event_data)
                logger.info("app_mention processing completed")

        return create_response(200, "OK")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return create_response(500, "Internal Server Error")
