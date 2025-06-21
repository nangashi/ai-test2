from utils.http_response import create_response


class TestHttpResponse:
    """HTTPレスポンス作成のテスト"""

    def test_create_response_with_body(self):
        """ボディ付きレスポンスのテスト"""
        response = create_response(200, "OK")

        assert response["statusCode"] == 200
        assert response["body"] == "OK"
        assert response["headers"]["Content-Type"] == "application/json"

    def test_create_response_without_body(self):
        """ボディなしレスポンスのテスト"""
        response = create_response(404)

        assert response["statusCode"] == 404
        assert response["body"] == ""
        assert response["headers"]["Content-Type"] == "application/json"

    def test_create_response_various_status_codes(self):
        """様々なステータスコードのテスト"""
        status_codes = [200, 400, 401, 403, 404, 500]

        for code in status_codes:
            response = create_response(code, f"Status {code}")
            assert response["statusCode"] == code
            assert response["body"] == f"Status {code}"
