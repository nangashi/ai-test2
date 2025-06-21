import pytest
from unittest.mock import patch, MagicMock
import json
import time
import hmac
import hashlib
from src.lambda_function import lambda_handler, verify_slack_signature, create_response


class TestLambdaFunction:
    """Lambda関数のテストクラス"""

    def test_verify_slack_signature_valid(self):
        """有効なSlack署名のテスト"""
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
        signing_secret = "test-secret"
        timestamp = str(int(time.time()))
        body = '{"type":"url_verification","challenge":"test"}'
        invalid_signature = "v0=invalid_signature"
        
        assert verify_slack_signature(signing_secret, body, timestamp, invalid_signature) is False

    def test_verify_slack_signature_old_timestamp(self):
        """古いタイムスタンプのテスト"""
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
        response = create_response(200, "OK")
        expected = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": "OK"
        }
        assert response == expected

    @patch.dict('os.environ', {
        'SLACK_BOT_TOKEN': 'xoxb-test-token',
        'SLACK_SIGNING_SECRET': 'test-signing-secret'
    })
    def test_lambda_handler_url_verification(self):
        """URL verification処理のテスト"""
        timestamp = str(int(time.time()))
        body = '{"type":"url_verification","challenge":"test_challenge"}'
        
        # 正しい署名を生成
        sig_basestring = f"v0:{timestamp}:{body}"
        signature = 'v0=' + hmac.new(
            'test-signing-secret'.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        event = {
            'requestContext': {'http': {'method': 'POST'}},
            'headers': {
                'x-slack-signature': signature,
                'x-slack-request-timestamp': timestamp
            },
            'body': body
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 200
        assert result['body'] == 'test_challenge'

    @patch.dict('os.environ', {
        'SLACK_BOT_TOKEN': 'xoxb-test-token',
        'SLACK_SIGNING_SECRET': 'test-signing-secret'
    })
    @patch('src.lambda_function.WebClient')
    def test_lambda_handler_app_mention(self, mock_webclient):
        """app_mentionイベント処理のテスト"""
        # WebClientのモック設定
        mock_client = MagicMock()
        mock_webclient.return_value = mock_client
        
        timestamp = str(int(time.time()))
        body = json.dumps({
            'type': 'event_callback',
            'event': {
                'type': 'app_mention',
                'text': '<@U123456> hello',
                'user': 'U123456',
                'channel': 'C123456'
            }
        })
        
        # 正しい署名を生成
        sig_basestring = f"v0:{timestamp}:{body}"
        signature = 'v0=' + hmac.new(
            'test-signing-secret'.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        event = {
            'requestContext': {'http': {'method': 'POST'}},
            'headers': {
                'x-slack-signature': signature,
                'x-slack-request-timestamp': timestamp
            },
            'body': body
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 200
        mock_client.chat_postMessage.assert_called_once_with(
            channel='C123456',
            text='こんにちは！メンションありがとうございます。'
        )

    def test_lambda_handler_invalid_method(self):
        """無効なHTTPメソッドのテスト"""
        event = {
            'requestContext': {'http': {'method': 'GET'}},
            'headers': {},
            'body': ''
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 405
        assert result['body'] == 'Method Not Allowed'

    def test_lambda_handler_missing_headers(self):
        """必要なヘッダーが不足している場合のテスト"""
        event = {
            'requestContext': {'http': {'method': 'POST'}},
            'headers': {},
            'body': ''
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 400
        assert result['body'] == 'Bad Request'

    @patch.dict('os.environ', {
        'SLACK_BOT_TOKEN': 'xoxb-test-token',
        'SLACK_SIGNING_SECRET': 'test-signing-secret'
    })
    def test_lambda_handler_invalid_signature(self):
        """無効な署名のテスト"""
        timestamp = str(int(time.time()))
        body = '{"type":"url_verification","challenge":"test"}'
        
        event = {
            'requestContext': {'http': {'method': 'POST'}},
            'headers': {
                'x-slack-signature': 'v0=invalid_signature',
                'x-slack-request-timestamp': timestamp
            },
            'body': body
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 401
        assert result['body'] == 'Unauthorized'