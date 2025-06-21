import os
import json
import hashlib
import hmac
import time
import logging
from slack_bolt import App

# OpenTelemetryの基本設定（テレメトリーは無効化）
os.environ["OTEL_SDK_DISABLED"] = "true"

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
AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")

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

def chat_with_claude4(user_message: str, conversation_history: list = None) -> str:
    """
    AWS Bedrock Claude 4 Sonnetを使って会話する
    
    Args:
        user_message: ユーザーのメッセージ
        conversation_history: 会話履歴のリスト（形式: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]）
    
    Returns:
        str: Claudeの返答
    """
    try:
        from strands import Agent
        from strands.models import BedrockModel
        
        # Claude 4 Sonnet on Bedrockモデルを設定
        model = BedrockModel(
            model_id="anthropic.claude-sonnet-4-20250514-v1:0",
            region="us-east-1",  # Claude 4はus-east-1リージョンで利用可能
            max_tokens=1000,
            temperature=0.7,
            additional_request_fields={
                "anthropic_beta": ["interleaved-thinking-2025-05-14"],
                "thinking": {"type": "enabled", "budget_tokens": 4000},
            }
        )
        
        # エージェントを作成
        agent = Agent(
            model=model,
            system_prompt="""あなたは親しみやすいSlack Botアシスタントです。
            日本語で自然に会話し、ユーザーを支援してください。
            簡潔で分かりやすい回答を心がけてください。"""
        )
        
        # 会話履歴がある場合は履歴を含めてメッセージを構築
        if conversation_history:
            # 履歴を文字列として整理
            history_text = "\n".join([
                f"{'ユーザー' if msg.get('role') == 'user' else 'アシスタント'}: {msg.get('content', '')}"
                for msg in conversation_history[-10:]  # 最新10件のみ使用
            ])
            
            full_message = f"""以下は過去の会話履歴です：
{history_text}

新しいメッセージ: {user_message}

上記の会話履歴を踏まえて、新しいメッセージに応答してください。"""
        else:
            full_message = user_message
        
        # Claude 4と会話
        response = agent.chat(full_message)
        
        return response
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error chatting with Claude 4 via Bedrock: {e}")
        logger.error(f"Full error traceback: {error_details}")
        return f"申し訳ありません。AI処理中にエラーが発生しました: {str(e)}"

def parse_thread_history_for_ai(messages: list) -> list:
    """
    Slackのメッセージ履歴をAI用の会話履歴形式に変換
    
    Args:
        messages: Slackのメッセージリスト
    
    Returns:
        list: AI用会話履歴 [{"role": "user"|"assistant", "content": "..."}]
    """
    conversation_history = []
    
    for msg in messages:
        text = msg.get("text", "")
        if not text:
            continue
            
        # メンションを除去してクリーンなテキストにする
        import re
        clean_text = re.sub(r'<@[UW][A-Z0-9]+>', '', text).strip()
        
        if clean_text:
            if msg.get("bot_id") or msg.get("app_id"):
                # Botのメッセージ
                conversation_history.append({
                    "role": "assistant",
                    "content": clean_text
                })
            else:
                # ユーザーのメッセージ
                conversation_history.append({
                    "role": "user", 
                    "content": clean_text
                })
    
    return conversation_history

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
                    user_text = event_data.get("text", "")
                    
                    # メンションを除去してユーザーメッセージを取得
                    import re
                    clean_user_message = re.sub(r'<@[UW][A-Z0-9]+>', '', user_text).strip()
                    
                    # スレッド内でのメンションかチェック
                    if event_data.get("thread_ts"):
                        # スレッド履歴を取得してClaude 4と会話
                        try:
                            thread_response = client.conversations_replies(
                                channel=channel,
                                ts=thread_ts,
                                limit=20
                            )
                            
                            if thread_response["ok"]:
                                messages = thread_response["messages"]
                                conversation_history = parse_thread_history_for_ai(messages)
                                
                                # Claude 4と会話（履歴付き）
                                response_text = chat_with_claude4(clean_user_message, conversation_history)
                            else:
                                # 履歴取得失敗時は履歴なしで会話
                                response_text = chat_with_claude4(clean_user_message)
                        except Exception as e:
                            logger.error(f"Error getting thread history: {e}")
                            response_text = chat_with_claude4(clean_user_message)
                    else:
                        # 通常のメンション - Claude 4と会話（履歴なし）
                        response_text = chat_with_claude4(clean_user_message)
                    
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