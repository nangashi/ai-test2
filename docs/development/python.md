# Python開発ガイド

本プロジェクトでのPython開発における運用ルール、設計方針、品質基準を定義します。

## 環境構築

### 必要ツール

Python開発・品質管理に必要なツールをuvとaquaで統一管理：

| ツール | 用途 | インストール方法 |
|--------|------|-----------------|
| uv | Pythonパッケージ管理・仮想環境管理 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| pytest | ユニット・結合テスト実行 | `uv add --dev pytest pytest-cov` |
| ruff | コードフォーマット・リント | `uv add --dev ruff` |
| mypy | 静的型チェック | `uv add --dev mypy` |
| lambroll | Lambda関数デプロイ | `aqua g -i fujiwara/lambroll` |

**プロジェクト共通ツール**: プロジェクトルートで `aqua install` を実行してlambrollを含む共通ツールを一括インストール

### プロジェクト初期設定

新しいPythonアプリケーションを作成する際の初期セットアップ手順：

```bash
# 1. アプリケーションディレクトリの作成
mkdir -p apps/<application_name>
cd apps/<application_name>

# 2. pyproject.tomlの配置
cat > pyproject.toml << 'EOF'
[project]
name = "application-name"
version = "0.1.0"
description = "Application description"
requires-python = ">=3.13"
dependencies = [
    # 必要に応じて追加
    # "boto3>=1.34.0",
    # "injector>=0.21.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
addopts = "-v --strict-markers"

[tool.ruff]
target-version = "py313"
line-length = 120
src = ["src"]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
]
ignore = []

[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
follow_imports = "silent"
ignore_missing_imports = true
EOF

# 3. 仮想環境の作成と有効化
uv venv                    # pyproject.tomlのrequires-pythonに基づいて仮想環境作成
source .venv/bin/activate  # 仮想環境有効化（以降の作業はこの環境で実施）

# 4. 依存関係のインストール
uv sync                    # pyproject.tomlに基づく依存関係インストール

# 5. ディレクトリ構造の作成
mkdir -p src tests tests-it lambroll
touch src/main.py tests/conftest.py tests-it/conftest.py

# 6. .gitignore設定
# Python必要最低限の除外設定
cat > .gitignore << 'EOF'
# Python
__pycache__/
.venv/

# Development tools
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Lambda deployment
*.zip
EOF

# 7. Lambdaデプロイ設定の作成（Lambdaアプリの場合）
# lambroll/function.jsonを作成
```

### ディレクトリ構成標準

```
apps/<application_name>/
├── pyproject.toml           # プロジェクト設定（Python 3.13、strict型チェック）
├── uv.lock                  # 依存関係ロックファイル
├── src/                     # プロダクションコード
│   └── main.py              # エントリーポイント
├── lambroll/                # Lambdaデプロイ設定（Lambda関数の場合）
│   └── function.json        # Lambda関数設定
├── tests/                   # ユニットテスト（クラス単位）
│   ├── conftest.py          # pytest設定・フィクスチャ
│   └── test_*.py           # 各srcファイルに対応
└── tests-it/               # 結合テスト（シナリオ単位）
    ├── conftest.py          # 結合テスト用設定
    └── test_*_scenario.py   # 業務シナリオのテスト
```

**配置の指針**:
- **src/**: 1ファイル1クラス、責務明確化
- **tests/**: ユニットテスト（クラス・メソッド単位）
- **tests-it/**: 結合テスト（エンドツーエンドシナリオ）
- **lambroll/**: Lambda関数設定（Lambda関数の場合のみ）

## 計画

### 開発フロー設計

標準的な開発フローを以下の順序で実施：

#### 従来の開発フロー

1. **設計**: 要件分析、アーキテクチャ設計
2. **実装**: コード実装
3. **テスト**: ユニットテスト作成・実行
4. **品質チェック**: コード品質確認、結合テスト

#### TDD開発フロー（推奨）

1. **設計**: 要件分析、インターフェース設計
2. **ユニットテスト作成**: 失敗するテストを先に書く（Red）
3. **実装＆リファクタリング**: テストを通す最小実装（Green）→改善（Refactor）
4. **結合テスト**: システム全体の動作確認

#### テスト駆動開発の詳細

理想的な開発では、設計・テスト・実装を段階的に進める：

**1. 設計フェーズ**

ファイル構成とクラス設計の明確化：

```bash
# 設計ドキュメントの作成
mkdir -p docs/design
cat > docs/design/<feature_name>_design.md << 'EOF'
# <機能名> 設計書

# ファイル構成
- src/<module_name>.py: <責務の説明>
- tests/test_<module_name>.py: <テスト内容>

# クラス設計
### <ClassName>
- 責務: <単一責任の説明>
- 主要メソッド:
  - <method_name>(args) -> return_type: <処理概要>

# 外部依存
- <依存サービス>: <使用目的とモック方針>
EOF
```

設計時の考慮事項：
- **単一責任の原則**: 1クラス1責務を明確に定義
- **依存関係の整理**: 外部サービス（AWS、Slack API等）の依存を特定
- **インターフェース設計**: メソッドのシグネチャと戻り値を明確化
- **エラーケースの想定**: 各メソッドで想定される例外を事前定義

**2. テスト設計・実装フェーズ**

ユニットテストの実装：

```python
# tests/test_<module_name>.py
import pytest
from unittest.mock import Mock, patch
from src.<module_name> import <ClassName>

class Test<ClassName>:
    """<ClassName>のユニットテスト"""
    
    def setup_method(self):
        """各テストメソッド実行前の準備"""
        self.target = <ClassName>()
    
    @patch('src.<module_name>.external_service')
    def test_<method_name>_正常系(self, mock_service):
        """<method_name>の正常系テスト"""
        # Given (準備)
        mock_service.return_value = "expected_response"
        input_data = {"key": "value"}
        
        # When (実行)
        result = self.target.<method_name>(input_data)
        
        # Then (検証)
        assert result == "expected_result"
        mock_service.assert_called_once_with(input_data)
    
    @patch('src.<module_name>.external_service')
    def test_<method_name>_例外系_接続エラー(self, mock_service):
        """<method_name>の例外系テスト: 接続エラー"""
        # Given
        mock_service.side_effect = ConnectionError("接続失敗")
        
        # When & Then
        with pytest.raises(ServiceUnavailableError):
            self.target.<method_name>({"key": "value"})
```

モックとスタブの設計指針：

```python
# conftest.py - 共通フィクスチャ
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_aws_client():
    """AWS クライアントのモック"""
    mock = Mock()
    mock.invoke_model.return_value = {
        'body': Mock(read=Mock(return_value='{"content": [{"text": "AI response"}]}'))
    }
    return mock

@pytest.fixture
def mock_slack_client():
    """Slack クライアントのモック"""
    mock = Mock()
    mock.conversations_replies.return_value = {
        "ok": True,
        "messages": [{"text": "test message", "user": "U123"}]
    }
    return mock

@pytest.fixture
def sample_slack_event():
    """Slackイベントのサンプルデータ"""
    return {
        "type": "app_mention",
        "text": "<@U123> こんにちは",
        "user": "U456",
        "channel": "C789",
        "ts": "1234567890.123"
    }
```

**3. 実装フェーズ**

テストを満たす最小実装：

```python
# src/<module_name>.py
import logging
from typing import Dict, Any
from .exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)

class <ClassName>:
    """<責務の説明>"""
    
    def __init__(self):
        """初期化処理"""
        pass
    
    def <method_name>(self, input_data: Dict[str, Any]) -> str:
        """<処理概要>"""
        try:
            # テストで期待される最小限の実装
            result = self._process_data(input_data)
            logger.info(f"処理完了: {type(result).__name__}")
            return result
        except ConnectionError as e:
            logger.error(f"接続エラー: {e}")
            raise ServiceUnavailableError("サービスが一時的に利用できません") from e
    
    def _process_data(self, data: Dict[str, Any]) -> str:
        """内部処理 - プライベートメソッドとして分離"""
        # 具体的な処理実装
        pass
```

**4. 統合テスト実装**

エンドツーエンドテストの設計：

```python
# tests-it/test_<feature_name>_scenario.py
import pytest
from unittest.mock import patch, Mock
from src.lambda_function import lambda_handler

class TestSlackBotScenario:
    """Slack Bot全体のシナリオテスト"""
    
    @patch('src.slack.handler.WebClient')
    @patch('src.ai.bedrock_client.boto3.client')
    def test_slack_mention_to_ai_response_正常フロー(self, mock_boto3, mock_slack):
        """Slackメンション → AI応答の正常フロー"""
        # Given (準備)
        mock_slack.return_value.conversations_replies.return_value = {
            "ok": True, "messages": []
        }
        mock_boto3.return_value.invoke_model.return_value = {
            'body': Mock(read=Mock(return_value='{"content": [{"text": "こんにちは！"}]}'))
        }
        
        event = {
            "httpMethod": "POST",
            "headers": {"X-Slack-Signature": "valid_signature"},
            "body": '{"type": "event_callback", "event": {"type": "app_mention", "text": "<@U123> hello"}}'
        }
        
        # When (実行)
        response = lambda_handler(event, {})
        
        # Then (検証)
        assert response["statusCode"] == 200
        mock_slack.return_value.chat_postMessage.assert_called_once()
```

#### テスト実行フロー

段階的なテスト実行（詳細なコマンドは「## 品質保証」→「テスト実行コマンド」を参照）：

1. **単体テスト**: `uv run pytest tests/test_<module_name>.py`
2. **カバレッジ確認**: `uv run pytest --cov=src --cov-fail-under=80`
3. **統合テスト**: `uv run pytest tests-it/`
4. **全テスト実行**: `uv run pytest tests/ tests-it/ --cov=src`

**6. TDDサイクルの実践**

Red-Green-Refactor サイクル：

1. **Red**: 失敗するテストを書く
   ```bash
   uv run pytest tests/test_new_feature.py::test_new_method -v
   # FAILED - まだ実装されていないためテスト失敗
   ```

2. **Green**: テストを通す最小限の実装
   ```bash
   # 最小実装後
   uv run pytest tests/test_new_feature.py::test_new_method -v
   # PASSED - テスト成功
   ```

3. **Refactor**: 実装の改善とテストの追加
   ```bash
   # リファクタリング後、全テストが通ることを確認
   uv run pytest tests/ -v
   # 全テストがPASSであることを確認
   ```

**テスト実装の優先順位**

コアビジネスロジック優先：

1. **最優先**: Lambda関数エントリーポイント（`lambda_function.py`）
2. **高優先**: Slackイベント処理（`slack/handler.py`）
3. **高優先**: AI処理（`ai/bedrock_client.py`, `ai/strands_agent.py`）
4. **中優先**: 設定管理（`config/settings.py`）
5. **低優先**: ユーティリティ（`utils/`, `slack/message_parser.py`等）

**外部依存のテスト戦略**

| 外部サービス | モック対象 | テスト観点 |
|-------------|-----------|-----------|
| AWS Bedrock | `boto3.client("bedrock-runtime")` | レスポンス形式、エラーハンドリング |
| Slack API | `slack_sdk.WebClient` | API呼び出し、認証、制限対応 |
| Secrets Manager | `boto3.client("secretsmanager")` | シークレット取得、権限エラー |
| 環境変数 | `os.environ` | 設定値の読み込み、デフォルト値 |

**エラーケースの網羅**

必須テストケース：
- **認証エラー**: 無効なトークン、権限不足
- **ネットワークエラー**: タイムアウト、接続失敗
- **API制限**: Rate limit、一時的な利用制限
- **データ形式エラー**: 不正なJSON、予期しない形式
- **ビジネスロジックエラー**: 入力検証、状態不整合

#### 命名規則

**ファイル名**:
- **Pythonファイル**: snake_case（例: `issue_creator.py`）
- **テストファイル**: `test_`プレフィックス（例: `test_issue_creator.py`）

**コード内**:
- **クラス名**: PascalCase（例: `IssueCreator`）
- **メソッド・関数名**: snake_case（例: `create_issue`）
- **定数**: UPPER_SNAKE_CASE（例: `MAX_RETRY_COUNT`）
- **変数**: snake_case（例: `issue_title`）

#### ディレクトリ構成

```
src/
├── clients/               # 外部接続層
│   ├── aws_client.py     # AWS SDK接続
│   └── api_client.py     # 外部API接続
├── services/              # ビジネスロジック層
│   └── main_service.py   # 主要ビジネスロジック
└── main.py               # エントリーポイント
```

#### 実装パターン

**外部接続クラス（clients層）**:

```python
# src/clients/aws_client.py
import boto3

class AWSClient:
    """AWS SDK専用クライアント"""
    
    def __init__(self, region_name: str = "ap-northeast-1"):
        self._client = boto3.client("service-name", region_name=region_name)
    
    def call_service(self, params: dict) -> dict:
        """AWS サービス呼び出し"""
        return self._client.some_method(**params)
```

**サービスクラス（services層）**:

```python
# src/services/main_service.py
from typing import Optional
from clients.aws_client import AWSClient

class MainService:
    """ビジネスロジック層"""
    
    def __init__(self, aws_client: Optional[AWSClient] = None):
        """
        Args:
            aws_client: AWSClient実装（テスト時はモック注入）
        """
        self._aws_client = aws_client or AWSClient()
    
    def process_data(self, data: dict) -> str:
        """データ処理のビジネスロジック"""
        # 外部サービス呼び出し（注入されたクライアント使用）
        result = self._aws_client.call_service(data)
        
        # ビジネスロジック処理
        return self._format_result(result)
```

**エントリーポイント**:

```python
# src/main.py
from services.main_service import MainService

def main():
    """本番環境では実際のクライアントを使用（デフォルト引数）"""
    service = MainService()  # 実際のAWSクライアントが注入される
    result = service.process_data({"key": "value"})
    return result
```

#### テスト実装

**ユニットテスト（モック注入）**:

```python
# tests/test_main_service.py
from unittest.mock import Mock
from src.services.main_service import MainService

def test_process_data_正常系():
    # Given - モックを注入
    mock_aws_client = Mock()
    mock_aws_client.call_service.return_value = {"result": "success"}
    
    service = MainService(aws_client=mock_aws_client)
    
    # When
    result = service.process_data({"input": "test"})
    
    # Then
    assert "success" in result
    mock_aws_client.call_service.assert_called_once_with({"input": "test"})
```

**統合テスト（@patch使用）**:

```python
# tests/test_integration.py
from unittest.mock import patch
from src.main import main

@patch('src.clients.aws_client.boto3.client')
def test_main_統合フロー(mock_boto3):
    # Given
    mock_client = Mock()
    mock_boto3.return_value = mock_client
    mock_client.some_method.return_value = {"result": "integration_success"}
    
    # When
    result = main()
    
    # Then
    assert "integration_success" in result
```

#### テスト戦略

| テスト種別 | 対象層 | モック方法 | 目的 |
|-----------|--------|-----------|------|
| **ユニットテスト** | services/ | コンストラクタ注入 | ビジネスロジック検証 |
| **統合テスト** | エントリーポイント | @patch | エンドツーエンド確認 |

**利点**:
- **テストの容易さ**: 外部依存を簡単にモック化
- **実装の交換性**: 本番・テスト・開発環境で異なる実装を使用可能
- **保守性**: 外部API変更の影響を局所化
- **段階的導入**: 既存コードを大幅に変更せずに適用可能

### 実装規則

#### コード実装規則

**コード構成・可読性**:

- **1ファイル1クラス**: ファイルごとに一つのクラスを定義し、責務を明確化
- **クラス責務の明示**: ファイルの先頭にクラスの責務をコメントで記載
- **単一責任の原則**: 同じクラスに複数の責務がある場合はクラスを分割
- **メソッドの説明**: 各メソッドには処理内容を説明する日本語の一行コメントを付与
- **処理目的の明示**: 複雑あるいは直感的に理解しにくい処理では目的や背景をコメントで記載

**import文の管理**:

- import文の順序は`uv run ruff format`で自動整形（手動調整不要）

**コード品質・保守性**:

- **型ヒント必須**: Python型ヒントを付与して型安全性を確保
- **ruffフォーマット**: `uv run ruff format`による自動フォーマット適用
- **ruffリント**: `uv run ruff check`によるリント実行
- **型チェック**: `uv run mypy src`による静的型チェック実行

**実装時の考慮事項**:

- **入出力仕様**: アプリケーションの要件に基づいて明確に定義
- **デプロイ設定**: Lambda関数の場合はlambroll/function.jsonに適切な設定を記載
- **テスト設計**: アプリケーションの処理フローに基づいて結合テストシナリオを作成

### エラーハンドリングとロギング

#### エラーハンドリング

**基本方針**:

- **具体的な例外型を使用**: `Exception`や`BaseException`ではなく、具体的な例外型を使用
- **tryブロックの最小化**: エラーが発生する可能性のある最小限のコードのみをtryブロックに含める
- **機密情報の保護**: エラーメッセージに機密情報（パスワード、APIキー、内部パス等）を含めない
- **適切なエラー伝播**: 下位レイヤーの詳細なエラーは上位レイヤーで適切に変換

**実装例**:

```python
# 良い例
try:
    response = external_api_call()
except ConnectionError as e:
    logger.error(f"API接続エラー", extra={"error": str(e), "endpoint": "api.example.com"})
    raise ServiceUnavailableError("一時的に利用できません") from e

# 悪い例
try:
    # 大量のコード...
    response = external_api_call()
    # さらに大量のコード...
except Exception as e:  # 広すぎる例外キャッチ
    print(f"エラー: {e}")  # ログではなくprint使用
    pass  # エラーを握りつぶす
```

**カスタム例外の定義**:

```python
class ApplicationError(Exception):
    """アプリケーション基底例外"""
    pass

class ValidationError(ApplicationError):
    """入力検証エラー"""
    pass

class ServiceUnavailableError(ApplicationError):
    """外部サービス利用不可エラー"""
    pass
```

#### ロギング戦略

**ログレベルの使い分け**:

- **DEBUG**: 開発時の詳細なデバッグ情報（変数の値、処理の流れ等）
- **INFO**: 正常動作の確認（処理開始・終了、重要な状態遷移等）
- **WARNING**: 潜在的な問題（非推奨機能の使用、リトライ発生等）
- **ERROR**: エラー発生（例外捕捉、処理失敗等）※CRITICALは使用しない

**ロギング設定例**:

```python
import logging
import json
from datetime import datetime

# 構造化ログのフォーマッター
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # extraフィールドの追加
        if hasattr(record, "extra_fields"):
            log_obj.update(record.extra_fields)
            
        return json.dumps(log_obj, ensure_ascii=False)

# ロガーの設定
def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    
    return logger
```

**ロギングのベストプラクティス**:

```python
logger = setup_logger(__name__)

def process_data(data: dict) -> dict:
    # 処理開始のログ
    logger.info("データ処理開始", extra={"data_size": len(data)})
    
    try:
        # 処理実行
        result = transform_data(data)
        
        # 成功ログ
        logger.info("データ処理完了", extra={"result_size": len(result)})
        return result
        
    except ValidationError as e:
        # エラーログ（機密情報は含めない）
        logger.error(
            "データ検証エラー",
            extra={"error_type": type(e).__name__, "field": e.field}
        )
        raise
```

**機密情報の扱い**:

```python
# 悪い例
logger.error(f"認証失敗: password={password}")  # パスワードをログ出力

# 良い例
logger.error("認証失敗", extra={"username": username})  # ユーザー名のみ記録
```

## 品質保証

### テスト実装

#### テスト実装規則

**テスト構成**:

- **ユニットテスト**: tests/ディレクトリ、クラス・メソッド単位
- **結合テスト**: tests-it/ディレクトリ、シナリオ単位
- **フィクスチャ**: conftest.pyで共通テストデータ・モックを定義

**テスト実装方針**:

- **1テストメソッド1アサーション**: 単一の観点のみをテストし、失敗原因を明確化
- **Given-When-Then構造**: テストケースを3段階で構造化（準備・実行・検証）
- **テスト名**: `test_<対象メソッド名>_<前提条件>_<期待結果>`形式で命名
- **日本語コメント**: テストの意図・背景を明記
- **フィクスチャ活用**: pytest.fixtureでテストデータ・モックオブジェクトを共通化

## 運用管理

### デプロイ管理

#### Lambda関数のデプロイ

**デプロイスクリプト**: `deploy.sh`を作成してデプロイプロセスを自動化

**参考スクリプト例**:

```bash
#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
PACKAGE_NAME="lambda-package.zip"
TEMP_DIR=$(mktemp -d)

cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# 必要ツールの確認
command -v lambroll >/dev/null || { echo "Error: lambroll not found"; exit 1; }
[[ -f "$SCRIPT_DIR/requirements.txt" ]] || { echo "Error: requirements.txt not found"; exit 1; }
[[ -d "$SCRIPT_DIR/src" ]] || { echo "Error: src directory not found"; exit 1; }
[[ -f "$SCRIPT_DIR/lambroll/function.json" ]] || { echo "Error: lambroll/function.json not found"; exit 1; }

echo "Building Lambda package..."

# ビルドディレクトリの作成
mkdir -p "$BUILD_DIR"
cp -r "$SCRIPT_DIR/src"/* "$TEMP_DIR/"

# 依存関係のインストール（Lambdaランタイム用）
python -m pip install \
    --no-cache-dir \
    --no-deps \
    -r <(uv export --format requirements-txt --no-dev --no-hashes) \
    --target "$TEMP_DIR/" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.13 \
    --only-binary=:all:

# 不要ファイルの削除
find "$TEMP_DIR" -type f -name "*.pyc" -delete
find "$TEMP_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

# ZIPファイルの作成
cd "$TEMP_DIR"
zip -r "$BUILD_DIR/$PACKAGE_NAME" . -x "*__pycache__*" -q

echo "Built: $BUILD_DIR/$PACKAGE_NAME"

# lambrollでデプロイ
echo "Deploying with lambroll..."
cd "$SCRIPT_DIR"
lambroll deploy --src "$BUILD_DIR/$PACKAGE_NAME"

echo "Deployment completed successfully!"
```

#### デプロイワークフロー

1. **コード品質チェック**: ruff format/check、mypy、pytestを実行
2. **依存関係の准備**: `uv export`でrequirements.txtを生成
3. **デプロイ実行**: `./deploy.sh`を実行
4. **動作確認**: テスト実行とログ確認（詳細は下記「テスト実行とログ確認」参照）

**スクリプトのポイント**:

- **プラットフォーム指定**: Lambda環境にmanylinux2014_x86_64を指定
- - **ファイルサイズ最適化**: *.pyc、__pycache__、*.dist-infoなどの不要ファイルを削除
- **エラーハンドリング**: set -euo pipefailでエラー時に即座に停止

#### lambroll設定

**function.jsonの例**:

```json
{
  "FunctionName": "my-function",
  "Runtime": "python3.13",
  "Handler": "main.lambda_handler",
  "Timeout": 30,
  "MemorySize": 512,
  "Environment": {
    "Variables": {
      "LOG_LEVEL": "INFO"
    }
  }
}
```

**lambrollコマンド**:

```bash
# デプロイ
lambroll deploy --src package.zip       # zipファイル指定でデプロイ
lambroll deploy --dry-run               # デプロイ内容の確認

# 管理
lambroll rollback                       # 前のバージョンにロールバック
lambroll delete                         # Lambda関数を削除

# 基本的なログ確認
lambroll logs                           # 最新のログを表示
lambroll logs --follow                  # ログをリアルタイム監視
lambroll logs --filter-pattern ERROR   # エラーログのみ表示
```

### 運用監視

#### テスト実行とログ確認

**デプロイ後の動作確認フロー**:

```bash
# 1. テスト実行（ログ付き）
lambroll invoke --payload '{"test": true}' --log-type Tail
# 実行結果とログが同時に表示される

# 2. 直近のログ確認
lambroll logs --since 5m                # 直近5分のログを表示
lambroll logs --since 1m --follow       # 1分前からリアルタイム監視

# 3. エラーログの確認
lambroll logs --filter-pattern "ERROR" --since 10m  # 10分以内のエラーのみ
lambroll logs --filter-pattern "[ERROR]" --since 30m # 別形式のエラーログ

# 4. 特定の実行を追跡
# invokeコマンドの出力にあるRequestIdを使用
lambroll logs --filter-pattern "RequestId: abc123-..."  # 特定リクエストのログ

# 5. 複数条件でのフィルタリング
lambroll logs --filter-pattern "user_id=12345" --since 1h  # 特定ユーザーの処理
lambroll logs --filter-pattern "?ERROR ?WARN" --since 30m  # エラーまたは警告
```

**ログ確認のベストプラクティス**:

1. **デプロイ直後**: `lambroll invoke`でテストペイロードを送信し、即座に動作確認
2. **継続的監視**: 別ターミナルで`lambroll logs --follow`を実行し、リアルタイム監視
3. **問題調査**: `--since`と`--filter-pattern`を組み合わせて効率的に調査
4. **本番確認**: CloudWatch Logsでより詳細な分析（メトリクス連携、Insights利用）

### コード品質管理

#### コード品質チェック

**自動フォーマット**:

```bash
uv run ruff format         # 全ファイルを自動フォーマット
uv run ruff format --check # フォーマット違反の確認のみ
```

**リントチェック**:

```bash
uv run ruff check                      # リントエラーの検出
uv run ruff check --fix               # 自動修正可能なエラーを修正
uv run ruff check --select E,F,I      # 特定ルールのみチェック
```

**型チェック**:

```bash
uv run mypy src                        # srcディレクトリの型チェック
uv run mypy src --strict              # 厳密モードで型チェック
uv run mypy src --ignore-missing-imports  # 外部ライブラリの型情報不足を無視
```

#### テスト実行コマンド

**ユニットテスト**:

```bash
uv run pytest                          # 全ユニットテスト実行
uv run pytest -v                      # 詳細出力
uv run pytest tests/test_issue_creator.py  # 特定ファイルのみ
uv run pytest -k "test_create"        # 特定のテストメソッドのみ
```

**カバレッジ測定**:

```bash
uv run pytest --cov=src               # カバレッジ測定
uv run pytest --cov=src --cov-report=html  # HTMLレポート生成
uv run pytest --cov=src --cov-fail-under=80  # カバレッジ80%未満でエラー
```

**結合テスト**:

```bash
uv run pytest tests-it/                # 全結合テスト実行
uv run pytest tests-it/ -v            # 詳細出力付き
```

#### 開発完了チェックリスト

デプロイ前に以下の項目を確認：

- [ ] **コード品質**: ruff format/check、mypy が全てパス
- [ ] **ユニットテスト**: 全テストパス、カバレッジ80%以上
- [ ] **結合テスト**: 全シナリオパス
- [ ] **仕様準拠**: 入出力仕様・処理フローが要件と一致
- [ ] **デプロイ設定**: lambroll/function.jsonが適切に設定されている（Lambda関数の場合）
- [ ] **依存関係**: uv.lockがコミットされ最新状態
