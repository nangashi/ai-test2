import pytest
from unittest.mock import patch, MagicMock
import json
import time
import hmac
import hashlib

# Slack Appに依存しない関数のみをテスト


class TestUtilityFunctions:
    """Slack Appに依存しないユーティリティ関数のテスト"""

    def test_verify_slack_signature_valid(self):
        """有効なSlack署名のテスト"""
        # 直接関数をインポートしてテスト
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        # 署名検証関数のみインポート（Slack App初期化を避ける）
        import importlib.util
        spec = importlib.util.spec_from_file_location("lambda_function", 
                                                    os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda_function.py'))
        
        # モジュールレベルでSlack App初期化をスキップするためのモック
        with patch('slack_bolt.App'), \
             patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test', 'SLACK_SIGNING_SECRET': 'test'}), \
             patch('lambda_function.get_secret_value'):
            
            lambda_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lambda_module)
            
            verify_slack_signature = lambda_module.verify_slack_signature
            
            signing_secret = "test-secret"
            timestamp = str(int(time.time()))
            body = '{"type":"url_verification","challenge":"test"}'
            
            # 正しい署名を生成
            sig_basestring = f"v0:{timestamp}:{body}"
            signature = 'v0=' + hmac.new(
                signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256
            ).hexdigest()
            
            assert verify_slack_signature(signing_secret, body, timestamp, signature) is True

    def test_verify_slack_signature_invalid(self):
        """無効なSlack署名のテスト"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("lambda_function", 
                                                    os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda_function.py'))
        
        with patch('slack_bolt.App'), \
             patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test', 'SLACK_SIGNING_SECRET': 'test'}), \
             patch('lambda_function.get_secret_value'):
            
            lambda_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lambda_module)
            
            verify_slack_signature = lambda_module.verify_slack_signature
            
            signing_secret = "test-secret"
            timestamp = str(int(time.time()))
            body = '{"type":"url_verification","challenge":"test"}'
            invalid_signature = "v0=invalid_signature"
            
            assert verify_slack_signature(signing_secret, body, timestamp, invalid_signature) is False

    def test_verify_slack_signature_old_timestamp(self):
        """古いタイムスタンプのテスト"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("lambda_function", 
                                                    os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda_function.py'))
        
        with patch('slack_bolt.App'), \
             patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test', 'SLACK_SIGNING_SECRET': 'test'}), \
             patch('lambda_function.get_secret_value'):
            
            lambda_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lambda_module)
            
            verify_slack_signature = lambda_module.verify_slack_signature
            
            signing_secret = "test-secret"
            old_timestamp = str(int(time.time()) - 400)  # 400秒前
            body = '{"type":"url_verification","challenge":"test"}'
            
            # 正しい署名を生成
            sig_basestring = f"v0:{old_timestamp}:{body}"
            signature = 'v0=' + hmac.new(
                signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256
            ).hexdigest()
            
            assert verify_slack_signature(signing_secret, body, old_timestamp, signature) is False

    def test_create_response(self):
        """HTTPレスポンス作成のテスト"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("lambda_function", 
                                                    os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda_function.py'))
        
        with patch('slack_bolt.App'), \
             patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test', 'SLACK_SIGNING_SECRET': 'test'}), \
             patch('lambda_function.get_secret_value'):
            
            lambda_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lambda_module)
            
            create_response = lambda_module.create_response
            
            response = create_response(200, "OK")
            expected = {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": "OK"
            }
            assert response == expected

    def test_parse_thread_history_for_ai(self):
        """スレッド履歴のAI用変換テスト"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("lambda_function", 
                                                    os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda_function.py'))
        
        with patch('slack_bolt.App'), \
             patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test', 'SLACK_SIGNING_SECRET': 'test'}), \
             patch('lambda_function.get_secret_value'):
            
            lambda_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lambda_module)
            
            parse_thread_history_for_ai = lambda_module.parse_thread_history_for_ai
            
            messages = [
                {
                    "text": "<@U123456> こんにちは",
                    "user": "U654321"
                },
                {
                    "text": "こんにちは！元気ですか？",
                    "bot_id": "B123456"
                },
                {
                    "text": "<@U123456> 元気です",
                    "user": "U654321"
                }
            ]
            
            result = parse_thread_history_for_ai(messages)
            
            expected = [
                {"role": "user", "content": "こんにちは"},
                {"role": "assistant", "content": "こんにちは！元気ですか？"},
                {"role": "user", "content": "元気です"}
            ]
            
            assert result == expected

    def test_parse_thread_history_for_ai_empty_messages(self):
        """空のメッセージリストのテスト"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("lambda_function", 
                                                    os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda_function.py'))
        
        with patch('slack_bolt.App'), \
             patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test', 'SLACK_SIGNING_SECRET': 'test'}), \
             patch('lambda_function.get_secret_value'):
            
            lambda_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lambda_module)
            
            parse_thread_history_for_ai = lambda_module.parse_thread_history_for_ai
            
            messages = []
            result = parse_thread_history_for_ai(messages)
            assert result == []

    @patch('strands.Agent')
    @patch('strands.models.BedrockModel')
    def test_chat_with_claude4_success(self, mock_bedrock_model, mock_agent):
        """Claude 4との会話成功テスト（Strands Agentsのモック）"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("lambda_function", 
                                                    os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda_function.py'))
        
        with patch('slack_bolt.App'), \
             patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test', 'SLACK_SIGNING_SECRET': 'test'}), \
             patch('lambda_function.get_secret_value'):
            
            lambda_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lambda_module)
            
            chat_with_claude4 = lambda_module.chat_with_claude4
            
            # モックの設定
            mock_model_instance = MagicMock()
            mock_bedrock_model.return_value = mock_model_instance
            
            mock_agent_instance = MagicMock()
            mock_agent_instance.chat.return_value = "こんにちは！何かお手伝いできることはありますか？"
            mock_agent.return_value = mock_agent_instance
            
            # テスト実行
            result = chat_with_claude4("こんにちは")
            
            # 検証
            assert result == "こんにちは！何かお手伝いできることはありますか？"
            mock_bedrock_model.assert_called_once()
            mock_agent.assert_called_once()
            mock_agent_instance.chat.assert_called_once_with("こんにちは")

    @patch('strands.Agent')
    @patch('strands.models.BedrockModel')
    def test_chat_with_claude4_error_handling(self, mock_bedrock_model, mock_agent):
        """Claude 4エラーハンドリングテスト"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("lambda_function", 
                                                    os.path.join(os.path.dirname(__file__), '..', 'src', 'lambda_function.py'))
        
        with patch('slack_bolt.App'), \
             patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-test', 'SLACK_SIGNING_SECRET': 'test'}), \
             patch('lambda_function.get_secret_value'):
            
            lambda_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(lambda_module)
            
            chat_with_claude4 = lambda_module.chat_with_claude4
            
            # モックでエラーを発生させる
            mock_bedrock_model.side_effect = Exception("Bedrock接続エラー")
            
            # テスト実行
            result = chat_with_claude4("テストメッセージ")
            
            # エラーメッセージが返されることを確認
            assert "申し訳ありません。AI処理中にエラーが発生しました" in result
            assert "Bedrock接続エラー" in result