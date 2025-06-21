import os
import json
import hashlib
import hmac
import time
import logging
from slack_bolt import App

# ログレベル設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Secrets Managerから設定を取得
import boto3

def get_secret_value(secret_arn):
    """Secrets Managerからシークレット値を取得"""
    try:
        secrets_client = boto3.client('secretsmanager')
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        return response['SecretString']
    except Exception as e:
        logger.error(f"Failed to get secret: {e}")
        return None

# 環境変数からSecrets Manager ARNを取得
SLACK_BOT_TOKEN_ARN = os.environ.get("SLACK_BOT_TOKEN_SECRET_ARN")
SLACK_SIGNING_SECRET_ARN = os.environ.get("SLACK_SIGNING_SECRET_SECRET_ARN")

# Secrets Managerから値を取得（環境変数がある場合は直接使用）
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN") or (
    get_secret_value(SLACK_BOT_TOKEN_ARN) if SLACK_BOT_TOKEN_ARN else None
)
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET") or (
    get_secret_value(SLACK_SIGNING_SECRET_ARN) if SLACK_SIGNING_SECRET_ARN else None
)

# Slack Boltアプリ初期化
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
    process_before_response=True
)

def verify_slack_signature(signing_secret: str, request_body: str, timestamp: str, signature: str) -> bool:
    """
    Slack署名を検証する
    
    Args:
        signing_secret: Slack Signing Secret
        request_body: リクエストボディ
        timestamp: リクエストタイムスタンプ
        signature: Slack署名
    
    Returns:
        bool: 署名が有効な場合True
    """
    # タイムスタンプが5分以内かチェック
    current_time = int(time.time())
    if abs(current_time - int(timestamp)) > 300:
        logger.warning("Request timestamp is too old")
        return False
    
    # 署名文字列を作成
    sig_basestring = f"v0:{timestamp}:{request_body}"
    
    # HMAC-SHA256で署名を生成
    computed_signature = 'v0=' + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # 署名を比較
    return hmac.compare_digest(computed_signature, signature)

def get_thread_history(client, channel: str, thread_ts: str) -> str:
    """
    スレッドの会話履歴を取得してフォーマットする
    
    Args:
        client: Slack WebClient
        channel: チャンネルID
        thread_ts: スレッドのタイムスタンプ
    
    Returns:
        str: フォーマットされた会話履歴
    """
    try:
        # スレッドのメッセージを取得
        response = client.conversations_replies(
            channel=channel,
            ts=thread_ts,
            limit=20  # 最大20件の履歴を取得
        )
        
        if not response["ok"]:
            logger.error(f"Failed to get thread history: {response.get('error')}")
            return "スレッド履歴の取得に失敗しました。"
        
        messages = response["messages"]
        
        if len(messages) <= 1:
            return "スレッド内の会話履歴はありません。"
        
        # 履歴をフォーマット
        history_lines = ["📝 スレッド内の会話履歴:"]
        
        for i, msg in enumerate(messages):
            text = msg.get("text", "")
            
            # メンションを除去してクリーンなテキストにする
            import re
            clean_text = re.sub(r'<@[UW][A-Z0-9]+>', '', text).strip()
            
            if clean_text:
                # メッセージ番号と内容を表示
                msg_num = i + 1
                
                # Botメッセージかユーザーメッセージかを判別
                if msg.get("bot_id") or msg.get("app_id"):
                    # Botのメッセージ
                    bot_name = msg.get("username", "Bot")
                    history_lines.append(f"{msg_num}. {bot_name}: {clean_text}")
                else:
                    # ユーザーのメッセージ
                    user_id = msg.get("user", "unknown")
                    history_lines.append(f"{msg_num}. <@{user_id}>: {clean_text}")
        
        if len(history_lines) == 1:  # ヘッダーのみの場合
            return "スレッド内にメッセージはありません。"
        
        # 最大10行に制限
        if len(history_lines) > 11:  # ヘッダー + 10行
            history_lines = history_lines[:11]
            history_lines.append("... (以下省略)")
        
        return "\n".join(history_lines)
        
    except Exception as e:
        logger.error(f"Error getting thread history: {e}")
        return f"スレッド履歴の取得中にエラーが発生しました: {str(e)}"

def create_response(status_code: int, body: str = "") -> dict:
    """
    Lambda Function URLs用のHTTPレスポンスを作成
    
    Args:
        status_code: HTTPステータスコード
        body: レスポンスボディ
    
    Returns:
        dict: HTTPレスポンス
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": body
    }

@app.event("app_mention")
def handle_app_mention_events(body, say, logger):
    """
    アプリがメンションされたときの処理
    """
    logger.info(f"Received app mention: {body}")
    
    # 固定メッセージを返信
    say("こんにちは！メンションありがとうございます。")

def lambda_handler(event, context):
    """
    Lambda関数のエントリーポイント（Function URLs対応）
    """
    try:
        # HTTPメソッドチェック
        if event.get("requestContext", {}).get("http", {}).get("method") != "POST":
            return create_response(405, "Method Not Allowed")
        
        # ヘッダーとボディを取得
        headers = event.get("headers", {})
        body = event.get("body", "")
        
        # 必要なヘッダーを取得
        slack_signature = headers.get("x-slack-signature")
        slack_timestamp = headers.get("x-slack-request-timestamp")
        
        if not slack_signature or not slack_timestamp:
            logger.warning("Missing Slack signature or timestamp")
            return create_response(400, "Bad Request")
        
        # 署名検証
        if not verify_slack_signature(SLACK_SIGNING_SECRET, body, slack_timestamp, slack_signature):
            logger.warning("Invalid Slack signature")
            return create_response(401, "Unauthorized")
        
        # リクエストボディをパース
        try:
            if body.startswith("payload="):
                # URL-encodedの場合（Interactive Components）
                import urllib.parse
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
            
            # app_mentionイベントの処理
            if event_data.get("type") == "app_mention":
                try:
                    # Slack APIクライアントでメッセージを送信
                    from slack_sdk import WebClient
                    client = WebClient(token=SLACK_BOT_TOKEN)
                    
                    channel = event_data.get("channel")
                    message_ts = event_data.get("ts")
                    thread_ts = event_data.get("thread_ts", message_ts)
                    
                    # スレッド内でのメンションかチェック
                    if event_data.get("thread_ts"):
                        # スレッド履歴を取得
                        response_text = get_thread_history(client, channel, thread_ts)
                    else:
                        # 通常のメンション
                        response_text = "こんにちは！メンションありがとうございます。"
                    
                    client.chat_postMessage(
                        channel=channel,
                        thread_ts=thread_ts,
                        text=response_text
                    )
                    
                    logger.info(f"Responded to app mention in channel: {channel}")
                    
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    return create_response(500, "Internal Server Error")
        
        return create_response(200, "OK")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return create_response(500, "Internal Server Error")