import logging
import os
from typing import Any

from strands import Agent, tool
from strands.models.bedrock import BedrockModel

from config.settings import settings

logger = logging.getLogger(__name__)

# Tavilyツール定義
@tool
def search_web(query: str) -> str:
    """
    Web検索を実行してリアルタイム情報を取得します
    
    Args:
        query: 検索クエリ
        
    Returns:
        検索結果のテキスト
    """
    try:
        import requests
        
        # Tavilyの無料APIを使用（環境変数から取得）
        tavily_api_key = os.environ.get("TAVILY_API_KEY")
        if not tavily_api_key:
            return "Web検索機能を使用するにはTAVILY_API_KEYが必要です。"
        
        # Tavily Search API呼び出し
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True,
                "include_images": False,
                "include_raw_content": False,
                "max_results": 3,
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # 検索結果を整形
            results = []
            if data.get("answer"):
                results.append(f"回答: {data['answer']}")
            
            if data.get("results"):
                results.append("\n関連情報:")
                for i, result in enumerate(data["results"][:3], 1):
                    title = result.get("title", "無題")
                    url = result.get("url", "")
                    content = result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", "")
                    results.append(f"{i}. {title}\n   {content}\n   参照: {url}")
            
            return "\n".join(results) if results else "関連する情報は見つかりませんでした。"
        else:
            return f"検索エラー: {response.status_code}"
            
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"検索中にエラーが発生しました: {str(e)}"


class StrandsClient:
    """Strands Agentを使用したAIクライアント"""
    
    def __init__(self):
        """Strands Agentを初期化"""
        try:
            # BedrockModelを設定
            self.model = BedrockModel(
                model_id=settings.ai_model_id,
                region_name=settings.bedrock_region,
                temperature=settings.ai_temperature,
                max_tokens=settings.ai_max_tokens,
            )
            
            # ツールリストを定義
            tools = [search_web]
            
            # Strands Agentを作成
            self.agent = Agent(
                model=self.model,
                tools=tools,
                system_prompt=settings.system_prompt,
            )
            
            logger.info("Strands Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Strands Agent: {e}")
            raise
    
    def chat(self, user_message: str, conversation_history: list[dict[str, str]] | None = None) -> str:
        """
        Strands Agentを使ってユーザーメッセージに応答
        
        Args:
            user_message: ユーザーのメッセージ
            conversation_history: 会話履歴（Strands Agentが自動管理するため、主に互換性のため保持）
            
        Returns:
            AIの応答テキスト
        """
        try:
            # Strands Agentで処理
            result = self.agent(user_message)
            
            # 結果からテキストを抽出
            if hasattr(result, 'content'):
                if isinstance(result.content, str):
                    return result.content
                elif isinstance(result.content, list):
                    # コンテンツリストからテキストを抽出
                    text_parts = []
                    for block in result.content:
                        if isinstance(block, dict) and "text" in block:
                            text_parts.append(block["text"])
                        elif isinstance(block, str):
                            text_parts.append(block)
                    return "\n".join(text_parts) if text_parts else str(result)
            
            # フォールバック: 結果を文字列に変換
            return str(result)
            
        except Exception as e:
            logger.error(f"Error in Strands Agent chat: {e}")
            return f"申し訳ありません。AI処理中にエラーが発生しました: {str(e)}"


# グローバルインスタンス（Lambda環境での再利用のため）
_strands_client = None

def get_strands_client() -> StrandsClient:
    """Strands Clientのシングルトンインスタンスを取得"""
    global _strands_client
    if _strands_client is None:
        _strands_client = StrandsClient()
    return _strands_client


def chat_with_strands(user_message: str, conversation_history: list[dict[str, str]] | None = None) -> str:
    """
    Strands Agentを使って会話（既存のAPIと互換性保持）
    
    Args:
        user_message: ユーザーのメッセージ
        conversation_history: 会話履歴（互換性のため保持）
        
    Returns:
        str: AIの返答
    """
    client = get_strands_client()
    return client.chat(user_message, conversation_history)