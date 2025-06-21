import hashlib
import hmac
import logging
import time

logger = logging.getLogger(__name__)


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
    computed_signature = "v0=" + hmac.new(signing_secret.encode(), sig_basestring.encode(), hashlib.sha256).hexdigest()

    # 署名を比較
    return hmac.compare_digest(computed_signature, signature)
