import re
from typing import Any


def extract_clean_message(text: str) -> str:
    """
    Slackメッセージからメンションなどを除去してクリーンなテキストを取得

    Args:
        text: Slackのメッセージテキスト

    Returns:
        str: クリーンなテキスト
    """
    # メンションを除去
    clean_text = re.sub(r"<@[UW][A-Z0-9]+>", "", text).strip()
    return clean_text


def parse_thread_history_for_ai(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    """
    Slackのメッセージ履歴をAI用の会話履歴形式に変換

    Args:
        messages: Slackのメッセージリスト

    Returns:
        list: AI用会話履歴 [{"role": "user"|"assistant", "content": "..."}]
    """
    import logging
    logger = logging.getLogger(__name__)
    
    conversation_history = []

    for msg in messages:
        text = msg.get("text", "")
        if not text:
            continue

        # メンションを除去してクリーンなテキストにする
        clean_text = extract_clean_message(text)

        if clean_text:
            # ボットかユーザーかを判定
            is_bot = bool(msg.get("bot_id") or msg.get("app_id") or msg.get("subtype") == "bot_message")
            
            if is_bot:
                # Botのメッセージ
                conversation_history.append({"role": "assistant", "content": clean_text})
                logger.debug(f"Added bot message: {clean_text[:50]}...")
            else:
                # ユーザーのメッセージ
                conversation_history.append({"role": "user", "content": clean_text})
                logger.debug(f"Added user message: {clean_text[:50]}...")

    return conversation_history


def format_thread_history_for_display(messages: list[dict[str, Any]]) -> str:
    """
    スレッド履歴を表示用にフォーマット

    Args:
        messages: Slackのメッセージリスト

    Returns:
        str: フォーマットされた会話履歴
    """
    if len(messages) <= 1:
        return "スレッド内の会話履歴はありません。"

    # 履歴をフォーマット
    history_lines = ["📝 スレッド内の会話履歴:"]

    for i, msg in enumerate(messages):
        text = msg.get("text", "")

        # メンションを除去してクリーンなテキストにする
        clean_text = extract_clean_message(text)

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
