from slack.message_parser import extract_clean_message, format_thread_history_for_display, parse_thread_history_for_ai


class TestMessageParser:
    """メッセージパーサーのテスト"""

    def test_extract_clean_message(self):
        """メンション除去のテスト"""
        # 通常のメンション
        text = "<@U12345678> hello world"
        result = extract_clean_message(text)
        assert result == "hello world"

        # 複数のメンション
        text = "<@U12345678> <@W87654321> test message"
        result = extract_clean_message(text)
        assert result == "test message"

        # メンションなし
        text = "plain text message"
        result = extract_clean_message(text)
        assert result == "plain text message"

    def test_parse_thread_history_for_ai(self):
        """スレッド履歴のAI用変換テスト"""
        messages = [
            {"text": "<@U12345678> こんにちは", "user": "U12345678"},
            {"text": "こんにちは！お手伝いします", "bot_id": "B12345678"},
            {"text": "<@U12345678> ありがとう", "user": "U87654321"},
        ]

        result = parse_thread_history_for_ai(messages)

        assert len(result) == 3
        assert result[0] == {"role": "user", "content": "こんにちは"}
        assert result[1] == {"role": "assistant", "content": "こんにちは！お手伝いします"}
        assert result[2] == {"role": "user", "content": "ありがとう"}

    def test_parse_thread_history_for_ai_empty_messages(self):
        """空のメッセージリストのテスト"""
        messages = []
        result = parse_thread_history_for_ai(messages)
        assert result == []

    def test_format_thread_history_for_display(self):
        """表示用フォーマットのテスト"""
        messages = [
            {"text": "<@U12345678> test1", "user": "U12345678"},
            {"text": "response1", "bot_id": "B12345678", "username": "TestBot"},
        ]

        result = format_thread_history_for_display(messages)

        assert "📝 スレッド内の会話履歴:" in result
        assert "1. <@U12345678>: test1" in result
        assert "2. TestBot: response1" in result

    def test_format_thread_history_for_display_single_message(self):
        """単一メッセージの場合のテスト"""
        messages = [{"text": "only one message", "user": "U12345678"}]
        result = format_thread_history_for_display(messages)
        assert result == "スレッド内の会話履歴はありません。"
