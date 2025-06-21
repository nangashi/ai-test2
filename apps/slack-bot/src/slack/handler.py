import logging
from typing import Any

from slack_sdk import WebClient

from ai.bedrock_client import chat_with_bedrock_direct
from config.settings import settings
from slack.message_parser import extract_clean_message, parse_thread_history_for_ai

logger = logging.getLogger(__name__)


def handle_app_mention(event: dict[str, Any]) -> None:
    """
    アプリメンションイベントを処理

    Args:
        event: Slackイベントデータ
    """
    try:
        # Slack APIクライアントを作成
        client = WebClient(token=settings.slack_bot_token)

        channel = event.get("channel")
        message_ts = event.get("ts")
        thread_ts = event.get("thread_ts", message_ts)
        user_text = event.get("text", "")

        # 必須パラメータのチェック
        if not channel or not thread_ts:
            logger.error("Missing required parameters: channel or thread_ts")
            return

        # メンションを除去してユーザーメッセージを取得
        clean_user_message = extract_clean_message(user_text)

        # スレッド内でのメンションかチェック
        if event.get("thread_ts"):
            # スレッド履歴を取得してAIと会話
            try:
                thread_response = client.conversations_replies(channel=channel, ts=event["thread_ts"], limit=50)

                if thread_response["ok"]:
                    messages = thread_response["messages"]
                    logger.info(f"Retrieved {len(messages)} messages from thread")
                    
                    # 現在のメッセージを除外（重複を避けるため）
                    conversation_history = parse_thread_history_for_ai(
                        [msg for msg in messages if msg.get("ts") != message_ts]
                    )
                    logger.info(f"Parsed {len(conversation_history)} messages for AI context")

                    # AIと会話（履歴付き）
                    response_text = chat_with_bedrock_direct(clean_user_message, conversation_history)
                else:
                    # 履歴取得失敗時は履歴なしで会話
                    response_text = chat_with_bedrock_direct(clean_user_message)
            except Exception as e:
                logger.error(f"Error getting thread history: {e}")
                response_text = chat_with_bedrock_direct(clean_user_message)
        else:
            # 通常のメンション - AIと会話（履歴なし）
            response_text = chat_with_bedrock_direct(clean_user_message)

        # Slackに返信
        client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=response_text)

        logger.info(f"Responded to app mention in channel: {channel}")

    except Exception as e:
        logger.error(f"Error handling app mention: {e}")
        raise
