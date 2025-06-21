from typing import Any


def create_response(status_code: int, body: str = "") -> dict[str, Any]:
    """
    Lambda Function URLs用のHTTPレスポンスを作成

    Args:
        status_code: HTTPステータスコード
        body: レスポンスボディ

    Returns:
        dict: HTTPレスポンス
    """
    return {"statusCode": status_code, "headers": {"Content-Type": "application/json"}, "body": body}
