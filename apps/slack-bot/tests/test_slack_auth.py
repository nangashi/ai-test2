import hashlib
import hmac
import time

from slack.auth import verify_slack_signature


class TestSlackAuth:
    """Slack認証機能のテスト"""

    def test_verify_slack_signature_valid(self):
        """有効なSlack署名のテスト"""
        signing_secret = "test_secret"
        request_body = "test_body"
        timestamp = str(int(time.time()))

        # 正しい署名を生成
        sig_basestring = f"v0:{timestamp}:{request_body}"
        expected_signature = (
            "v0=" + hmac.new(signing_secret.encode(), sig_basestring.encode(), hashlib.sha256).hexdigest()
        )

        # 検証
        result = verify_slack_signature(signing_secret, request_body, timestamp, expected_signature)
        assert result is True

    def test_verify_slack_signature_invalid(self):
        """無効なSlack署名のテスト"""
        signing_secret = "test_secret"
        request_body = "test_body"
        timestamp = str(int(time.time()))
        invalid_signature = "v0=invalid_signature"

        # 検証
        result = verify_slack_signature(signing_secret, request_body, timestamp, invalid_signature)
        assert result is False

    def test_verify_slack_signature_old_timestamp(self):
        """古いタイムスタンプのテスト"""
        signing_secret = "test_secret"
        request_body = "test_body"
        # 6分前のタイムスタンプ
        old_timestamp = str(int(time.time()) - 360)

        # 正しい署名を生成（古いタイムスタンプで）
        sig_basestring = f"v0:{old_timestamp}:{request_body}"
        signature = "v0=" + hmac.new(signing_secret.encode(), sig_basestring.encode(), hashlib.sha256).hexdigest()

        # 検証（古いタイムスタンプのため失敗するはず）
        result = verify_slack_signature(signing_secret, request_body, old_timestamp, signature)
        assert result is False
