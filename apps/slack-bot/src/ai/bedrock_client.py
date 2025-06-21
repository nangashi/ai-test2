import logging
import traceback

from config.settings import settings

logger = logging.getLogger(__name__)



def chat_with_bedrock_direct(user_message: str, conversation_history: list[dict[str, str]] | None = None) -> str:
    """
    Bedrock直接呼び出しでClaude 4を使って会話する

    Args:
        user_message: ユーザーのメッセージ
        conversation_history: 会話履歴のリスト

    Returns:
        str: Claudeの返答
    """
    try:
        import json

        import boto3

        # Bedrock Runtimeクライアントを作成
        bedrock = boto3.client("bedrock-runtime", region_name=settings.bedrock_region)

        # メッセージを構築
        messages = []

        # 会話履歴がある場合は追加
        if conversation_history:
            # 最新20件の履歴を使用（コンテキストウィンドウに収まる範囲で）
            recent_history = conversation_history[-20:]
            logger.info(f"Using {len(recent_history)} messages from conversation history")
            
            for msg in recent_history:
                if msg.get("role") == "user":
                    messages.append({"role": "user", "content": msg.get("content", "")})
                elif msg.get("role") == "assistant":
                    messages.append({"role": "assistant", "content": msg.get("content", "")})

        # 現在のユーザーメッセージを追加
        messages.append({"role": "user", "content": user_message})

        # リクエストボディを構築
        request_body = {
            "messages": messages,
            "system": settings.system_prompt,
            "max_tokens": settings.ai_max_tokens,
            "temperature": settings.ai_temperature,
            "anthropic_version": "bedrock-2023-05-31",
        }

        # Bedrockを呼び出し
        response = bedrock.invoke_model(
            modelId=settings.ai_model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body),
        )

        # レスポンスを解析
        response_body = json.loads(response["body"].read())

        # コンテンツを取得
        if "content" in response_body and len(response_body["content"]) > 0:
            return str(response_body["content"][0]["text"])
        else:
            logger.error(f"Unexpected response format: {response_body}")
            return "申し訳ありません。応答の処理中にエラーが発生しました。"

    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error chatting with Claude 4 via Bedrock direct: {e}")
        logger.error(f"Full error traceback: {error_details}")
        return f"申し訳ありません。AI処理中にエラーが発生しました: {str(e)}"
