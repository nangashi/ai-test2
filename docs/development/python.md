# Python開発ガイド

Python開発の標準フロー、テスト戦略、品質基準、デプロイ手順を定義します。

## 環境構築

初回プロジェクト作成時のPython開発環境のひな形構築手順。ツールのインストールと基本的なプロジェクト構造の初期化を行います。

### 必要ツール

Python開発・品質管理に必要なツールをuvとaquaで統一管理：

| ツール | 用途 | インストール方法 |
|--------|------|-----------------|
| uv | Pythonパッケージ管理・仮想環境管理 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| pytest | ユニット・結合テスト実行 | `uv add --dev pytest pytest-cov` |
| ruff | コードフォーマット・リント | `uv add --dev ruff` |
| mypy | 静的型チェック | `uv add --dev mypy` |
| lambroll | Lambda関数デプロイ | `aqua g -i fujiwara/lambroll` |

### プロジェクト初期設定

新しいPythonアプリケーションを作成する際の初期セットアップ手順：

```bash
# 1. アプリケーションディレクトリの作成
mkdir -p apps/<application_name>
cd apps/<application_name>

# 2. pyproject.tomlの配置（品質ツール設定込み）
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

# テスト設定（品質基準組み込み）
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
addopts = "-v --strict-markers --cov=src --cov-report=term-missing --cov-fail-under=80"

# コード品質設定
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

# 型チェック設定
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

# 6. デプロイファイルの作成
# ZIPデプロイ用（基本）
touch deploy.sh
chmod +x deploy.sh

# Dockerイメージデプロイする場合のみ追加
# touch Dockerfile

# 7. .gitignore設定
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
.venv/
dist/
build/
.pytest_cache/
.coverage
.mypy_cache/
.ruff_cache/
EOF
```


## 計画

実装開始前のファイル構成、クラス・インターフェース設計、開発フローに沿った作業順序の計画を行います。


### 開発フロー

本プロジェクトでは以下の5段階フローで開発を進めます：

#### 1. 設計フェーズ

**入力**: 開発要件・機能仕様  
**参照**: [設計](#設計)セクション  
**成果物**: DESIGN.md（アーキテクチャ、クラス設計、インターフェース定義含む）

**具体的な作業内容**:

1. **仕様の受け取りと明確化**
   - プロンプトまたはドキュメントで開発仕様を受け取る
   - 仕様から以下の要素を抽出・整理：
     - 機能要件（何を実現するか）
     - 非機能要件（パフォーマンス、セキュリティ等）
     - 入出力仕様（データ形式、API仕様等）
     - 外部連携（AWS サービス、外部API等）
   - 設計における不明点があれば質問して明確化する：
     - データの永続化方法（RDS、DynamoDB、S3等）
     - エラーハンドリング方針
     - 認証・認可の要件
     - スケーラビリティ要件
   - 不明点がなければ次の作業に進む

2. **ファイル・ディレクトリ構成の計画**
   - 明確化された機能要件から必要なモジュールを洗い出し
   - ディレクトリ構成標準に基づいてファイル配置を決定
   - 例: 「ユーザー管理機能」→ `src/models/user.py`, `src/services/user_service.py`, `src/repositories/user_repository.py`

3. **クラス・インターフェース設計**
   - レイヤー分離アーキテクチャに従ってクラスを配置
   - 各クラスのpublicメソッドのシグネチャを定義
   - 各メソッドの実装内容概要を記述
   - 例: `UserService.create_user(user_data: dict) -> str`
     - 実装概要: ユーザーデータのバリデーション、ユーザーID生成、リポジトリ経由でのデータ保存、作成完了通知

4. **依存関係の設計**
   - サービスが依存するリポジトリや外部サービスを特定
   - コンストラクタインジェクションで依存を受け取る設計
   - 例: `UserService.__init__(self, user_repository: UserRepository, email_service: EmailService)`

5. **アプリケーションディレクトリのDESIGN.mdへの記載**
   - アーキテクチャ概要、コンポーネント関係図
   - データフロー、API仕様、外部サービス連携
   - パフォーマンスやセキュリティ要件

**完了基準**: DESIGN.md作成完了、人によるレビュー合格（アーキテクチャ準拠、責任分離、テスタビリティ）

**仕様明確化の例**:

```
開発者: 以下の仕様について確認させてください：
1. ユーザーデータの保存先はDynamoDBでよろしいでしょうか？RDSの方が適切でしょうか？
2. 認証方式はCognitoを使用しますか？それとも独自実装でしょうか？
3. エラー時のリトライ回数に制限はありますか？
4. レスポンスタイムの目標値はありますか？

ユーザー: 
1. DynamoDBを使用してください
2. Cognitoで認証します
3. 最大3回までリトライしてください
4. 95パーセンタイルで1秒以内を目標とします

開発者: 承知しました。仕様が明確になったので設計を進めます。
```

#### 2. ユニットテスト実装フェーズ

**入力**: DESIGN.md  
**参照**: [実装](#実装)セクション  
**成果物**: ユニットテストコード（失敗状態）

**具体的な作業内容**:

1. **テスト環境の準備**
   - `tests/conftest.py`で共通フィクスチャを定義
   - モックオブジェクト、テストデータ、データベース接続の代替手段を用意

2. **正常系テストの作成**
   - 設計した各publicメソッドに対して正常ケースを作成
   - Given-When-Then形式でテストを構造化
   - 例: `test_create_user_valid_data_returns_user_id()`

3. **異常系テストの作成**
   - 入力バリデーションエラーのテスト
   - 外部サービス障害時のエラーハンドリングテスト
   - 例: `test_create_user_invalid_email_raises_validation_error()`

4. **モックの実装**
   - 外部依存（リポジトリ、APIクライアント）をモック化
   - ユニットテストが単体で実行できるようにする

**完了基準**: 設計したすべてのpublicメソッドに対するテスト作成、すべてのテストが失敗状態

#### 3. プロダクトコード実装フェーズ

**入力**: ユニットテストコード、DESIGN.md  
**参照**: [実装](#実装)セクション  
**成果物**: プロダクトコード（テスト合格状態）

**具体的な作業内容**:

1. **ビジネスロジックの実装**
   - DESIGN.mdの実装概要に基づいてビジネスロジックを実装
   - バリデーション、データ変換、外部サービス呼び出しなど
   - 例: ユーザーIDの生成、データベース保存処理
   - 実装後にユニットテストを実行して動作確認

2. **エラーハンドリングの実装**
   - カスタム例外の定義と発生処理
   - 外部サービスエラーのキャッチと適切なエラーレスポンス
   - 例: `ValidationError`, `DataAccessError`の適切な使い分け

3. **ロギングの実装**
   - 主要な処理ポイントでの情報ログ出力
   - エラー発生時のエラーログ出力（スタックトレース含む）
   - 機密情報のログ出力防止

4. **リファクタリング**
   - コード品質チェックで指摘された箇所の修正
   - 重複コードの整理、関数分割、変数名の改善
   - パフォーマンス最適化が必要な場合は実施

5. **品質チェックの実行**
   - `uv run ruff format` / `uv run ruff check`でコードスタイル統一
   - `uv run mypy`で型チェックエラーの解消
   - カバレッジテストでカバレッジ確認

**完了基準**: すべてのユニットテスト合格、カバレッジ80%以上、ruff・ mypyエラーなし

#### 4. 結合テスト実装フェーズ

**入力**: 開発要件、DESIGN.md、プロダクトコード  
**参照**: [テスト戦略](#テスト戦略)セクション  
**成果物**: 結合テストコード

**具体的な作業内容**:

1. **ユーザーシナリオベースのテスト設計**
   - 実際のユーザー操作やビジネスフローをベースにテストケースを作成
   - 例: 「ユーザー登録から通知メール送信までの一連のフロー」

2. **結合テスト環境の構築**
   - `tests-it/conftest.py`で結合テスト用のセットアップを定義
   - テスト用データベース、モック外部サービスの設定
   - テスト実行前後のクリーンアップ処理

3. **正常系シナリオテスト**
   - 複数コンポーネントが連携して動作するシナリオをテスト
   - データの正常な流れ、状態変更、外部連携を検証
   - 例: Service → Repository → Databaseの一連のデータ保存処理

4. **異常系シナリオテスト**
   - 外部サービスの障害、ネットワークエラー時の動作検証
   - リトライ、タイムアウト、フェイルオーバー機能のテスト
   - 例: データベース接続エラー時のエラーレスポンス

5. **パフォーマンステスト（必要に応じて）**
   - 大量データ処理、同時アクセス時の動作検証
   - レスポンスタイム、メモリ使用量の測定

**完了基準**: すべての結合テスト合格、本番環境での動作相当機能の検証完了（失敗時はアーキテクチャレベルの問題は設計フェーズへ、コードレベルの問題はプロダクトコード修正で対応）

#### 5. デプロイフェーズ

**入力**: プロダクトコード、結合テストコード  
**参照**: [運用・デプロイ](#運用・デプロイ)セクション  
**成果物**: 本番環境サービス

**具体的な作業内容**:

1. **デプロイ方式の選択**
   - 基本はZIPパッケージデプロイ
   - Dockerイメージでデプロイする場合は専用の`deploy.sh`を作成

2. **デプロイパッケージの作成**
   - ZIPデプロイ: Lambda関数のZIPパッケージを作成、依存関係最適化
   - Dockerデプロイ: ECRにイメージをプッシュ、Git SHAベースのタグ付け

3. **本番環境へのデプロイ**
   - lambrollを使用したLambda関数の本番環境へのデプロイ
   - 環境変数、IAMロール、トリガー設定の確認
   - バージョン公開（`--publish`オプション）でロールバック可能状態を維持

4. **デプロイ後の動作確認**
   - エラーログがないことを確認
   - 実際のリクエストでの動作テスト（手動またはスモークテスト）
   - 期待通りのレスポンスが返されることを確認

5. **監視・アラート設定**
   - CloudWatch Metricsでの実行時間、エラー率の監視設定
   - アラーム閾値の設定（エラー率、レスポンス時間など）
   - ログ分析、メトリクス可視化の設定

6. **ロールバック準備**
   - lambrollの自動ロールバック機能を活用
   - 問題発生時は`lambroll rollback`で前バージョンに即座復元

**完了基準**: 本番環境デプロイ成功、動作確認完了、監視・アラート設定完了、ロールバック手順確認済み

## 設計

アーキテクチャパターン、設計原則、依存性管理の方針を定義します。

### アーキテクチャ設計

設計作業の基盤となるアーキテクチャパターンと設計原則を確立します。

#### レイヤー分離アーキテクチャ

依存関係を上位から下位への一方向に限定し、横の層間では直接依存しない：

```
┌─────────────────┐
│   Lambda Handler │  ← エントリーポイント層：リクエスト受付・レスポンス返却
│   (Controller)   │
├─────────────────┤
│    Services      │  ← ビジネスロジック層：アプリケーションの主要処理
│ (Business Logic) │
├─────────────────┼─────────────────┐
│   Repositories   │   External       │  ← データ・外部連携層
│  (Data Access)   │   Services       │
├─────────────────┼─────────────────┤
│    Models        │     Utils        │  ← 基盤層：共通機能・データ構造
│  (Data Model)    │   (Utilities)    │
└─────────────────┴─────────────────┘
```

#### 各層の責任と配置基準

**エントリーポイント層 (Controller)**
- **責任**: リクエストの受付、レスポンスの返却、エラーハンドリング
- **配置**: `src/<main_module>.py` (Lambda handler など)

**ビジネスロジック層 (Services)**  
- **責任**: アプリケーションの主要な処理フロー、ビジネスルール
- **配置**: `src/services/`
- **例**: `UserService`, `IssueManagementService`

**データアクセス層 (Repositories)**
- **責任**: データの永続化・取得（アプリケーションの主要データソース）
- **配置**: `src/repositories/`
- **例**: `UserRepository` (DB), `IssueRepository` (GitHub API)
- **判断基準**: アプリケーションの主要な状態を管理するデータ

**外部サービス層 (External Services)**
- **責任**: 外部システムとの連携（通知、監視、補助的処理）
- **配置**: `src/external/`
- **例**: `SlackNotificationService`, `EmailService`, `MetricsClient`
- **判断基準**: 処理が失敗してもアプリケーションの主要機能に影響しない

**データモデル層 (Models)**
- **責任**: データ構造の定義、基本的なデータ操作
- **配置**: `src/models/`
- **例**: `User`, `Issue`, `ApiResponse`

**ユーティリティ層 (Utils)**
- **責任**: 共通的なヘルパー機能、設定管理
- **配置**: `src/utils/`
- **例**: `DateUtil`, `ConfigLoader`, `ValidationHelper`

#### 設計原則

**単一責任の原則**: 各クラス・メソッドは1つの責任のみを持つ

```python
# 良い例：責任分離
class UserService:
    def create_user(self, user_data: dict) -> str: pass

class EmailService:
    def send_welcome_email(self, user_email: str) -> None: pass

# 悪い例：複数責任混在
class UserService:
    def create_user_and_send_email(self, user_data: dict) -> str:
        # ユーザー作成 + メール送信（２つの責任）
        pass
```

**依存性注入**: サービス層では外部依存をコンストラクタで受け取り、テスタビリティを確保

```python
# 良い例：依存性注入を使用
class UserService:
    def __init__(self, user_repository: UserRepository, email_service: EmailService):
        self._user_repository = user_repository
        self._email_service = email_service

# 悪い例：直接インスタンス化
class UserService:
    def __init__(self):
        self._user_repository = UserRepository()  # テスト時にモック化困難
        self._email_service = EmailService()
```

### ファイル・クラス構成設計

機能要件から必要なクラスを洗い出し、ファイル配置とクラス設計を一体で行います。Pythonではファイルとクラスが基本的に一対一であることを活かし、効率的に設計します。

#### ディレクトリ構成標準

プロジェクト作成時に従うべき標準構成：

```
apps/<application_name>/
├── src/                    # メインアプリケーションコード
│   ├── <main_module>.py    # エントリーポイント
│   ├── models/             # データモデル
│   ├── services/           # ビジネスロジック
│   ├── repositories/       # データアクセス層
│   ├── external/           # 外部サービス連携
│   └── utils/              # ユーティリティ
├── tests/                  # ユニットテスト
│   ├── conftest.py         # テストフィクスチャ共通設定
│   ├── test_models/        # モデルテスト
│   ├── test_services/      # サービステスト
│   ├── test_repositories/  # リポジトリテスト
│   └── test_external/      # 外部サービステスト
├── tests-it/               # 結合テスト
│   ├── conftest.py         # 結合テスト用設定
│   └── test_integration/   # シナリオテスト
├── lambroll/               # Lambda関数デプロイ設定（該当する場合）
│   └── function.json       # Lambda関数設定
├── Dockerfile              # Dockerイメージデプロイする場合のみ
├── pyproject.toml          # プロジェクト設定・依存関係
├── uv.lock                 # 依存関係バージョン固定
├── deploy.sh               # デプロイスクリプト（実行権限付与）
└── README.md               # プロジェクト説明
```

#### 命名規則

**ファイル・ディレクトリ命名**:

- **ファイル名**: スネークケース（例: `user_service.py`, `data_repository.py`）
- **ディレクトリ名**: 複数形を使用（例: `models/`, `services/`, `tests/`）
- **テストファイル**: `test_` プレフィックス（例: `test_user_service.py`）

#### ファイル・クラス設計手順

1. **機能分析**: 開発要件から必要な機能を列挙
2. **クラス責任分類**: 各機能をレイヤー別に分類（models/services/repositories/utils）
3. **ファイル・クラス名決定**: 命名規則に従ってファイル名＝クラス名を決定
4. **インターフェース設計**: 各クラスのpublicメソッドのシグネチャと実装概要を定義
5. **テストファイル計画**: 各プロダクトファイルに対応するテストファイルを計画

**例**: 「ユーザー管理機能」の設計

```python
# src/models/user.py - Userクラス
class User:
    """責任: ユーザーデータの保持と基本操作"""
    pass

# src/services/user_service.py - UserServiceクラス  
class UserService:
    """責任: ユーザー関連のビジネスロジック"""
    def create_user(self, user_data: dict) -> str:
        """
        実装概要: ユーザーデータのバリデーション、ユーザーID生成、
        リポジトリ経由でのデータ保存、作成完了通知
        戻り値: 生成されたユーザーID
        例外: ValidationError, DataAccessError
        """
        pass
    
    def get_user(self, user_id: str) -> dict:
        """
        実装概要: ユーザーIDの検証、リポジトリからのデータ取得、
        データ形式の変換
        戻り値: ユーザー情報辞書
        例外: UserNotFoundError, DataAccessError
        """
        pass

# src/repositories/user_repository.py - UserRepositoryクラス
class UserRepository:
    """責任: ユーザーデータの永続化と取得"""
    pass
```

**対応するテストファイル**:
- `tests/test_models/test_user.py`
- `tests/test_services/test_user_service.py` 
- `tests/test_repositories/test_user_repository.py`

### 依存関係の設計

サービス間の依存関係を整理し、依存性注入パターンで設計します。

**手順**:
1. **依存関係の特定**: 各サービスが必要とする外部コンポーネントを特定
2. **コンストラクタ設計**: 依存をコンストラクタで受け取る設計
3. **インターフェース抽象化**: 具象クラスではなくインターフェースに依存する設計
4. **依存関係図の作成**: コンポーネント間の依存関係を図示

**例**: UserServiceの依存関係
```python
class UserService:
    def __init__(self, 
                 user_repository: UserRepository,
                 email_service: EmailService,
                 id_generator: IDGenerator):
        self._user_repository = user_repository
        self._email_service = email_service
        self._id_generator = id_generator
```

**依存関係図**:
```
UserService
├── UserRepository (データアクセス)
├── EmailService (通知機能)
└── IDGenerator (ID生成機能)
```

### DESIGN.mdドキュメント作成

設計内容をDESIGN.mdファイルに体系的に記録します。

**DESIGN.mdの構成例**:
```markdown
# [アプリケーション名] 設計書

## 概要
- 機能概要
- アーキテクチャ概要

## ファイル構成
- ディレクトリ構造
- 各ファイルの責任

## クラス設計
### UserService
- 責任: ユーザー管理のビジネスロジック
- publicメソッド: create_user, get_user, update_user
- 依存関係: UserRepository, EmailService

## データフロー
- 主要な処理フローの説明
- データの流れと変換

## 外部サービス連携
- API仕様
- 認証方式
- エラーハンドリング方針

## 非機能要件
- パフォーマンス要件
- セキュリティ要件
- 可用性要件
```

## 実装

コード実装規則、ユニットテスト、エラーハンドリング、ロギング、品質チェックの実施方法を定義します。

### 命名規則（実装時）

**関数・変数・定数命名**:

- **関数・変数**: スネークケース（例: `create_user`, `user_data`）
- **定数**: 大文字スネークケース（例: `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`）
- **プライベート**: アンダースコアプレフィックス（例: `_internal_method`）

### 実装手順（必須フロー）

**すべての実装依頼は以下の順序で実施：**

1. **conftest.py作成**：共通フィクスチャ・モック定義
2. **ユニットテスト実装**：正常系・例外系の網羅的テスト
3. **メインコード実装**：テストを通す実装
4. **結合テスト実装**：E2Eシナリオテスト
5. **品質チェック実行**：リント・型チェック・テスト実行

### コード実装規則

#### レイヤー分離（必須）

**サービス層**:

```python
from typing import List, Optional
from repositories.user_repository import UserRepository
from models.user import User

class UserService:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository
    
    def get_users(self, active_only: bool = True) -> List[User]:
        return self._user_repository.find_by_status("active" if active_only else None)
```

**リポジトリ層**:

```python
from typing import List, Optional
from models.user import User

class UserRepository:
    def __init__(self, database_client):
        self._db = database_client
    
    def find_by_status(self, status: Optional[str]) -> List[User]:
        # データベースアクセス実装
        pass
```

**モデル層**:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: str
    name: str
    email: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
```

#### エラーハンドリング（必須）

**カスタム例外定義**:

```python
# utils/exceptions.py
class BusinessLogicError(Exception):
    """ビジネスロジック関連のエラー"""
    pass

class DataAccessError(Exception):
    """データアクセス関連のエラー"""
    pass

class ValidationError(BusinessLogicError):
    """バリデーション関連のエラー"""
    pass
```

**例外処理パターン**:

```python
import logging
from utils.exceptions import DataAccessError, ValidationError

logger = logging.getLogger(__name__)

class UserService:
    def create_user(self, user_data: dict) -> str:
        try:
            # バリデーション
            if not user_data.get("email"):
                raise ValidationError("Email is required")
            
            # データベース操作
            return self._user_repository.create(user_data)
        
        except ValidationError:
            # バリデーションエラーはそのまま再発生
            raise
        except Exception as e:
            # 予期しないエラーはログ出力してビジネスロジックエラーに変換
            logger.error(f"Failed to create user: {e}", exc_info=True)
            raise DataAccessError(f"User creation failed: {e}")
```

#### ロギング（必須）

**ログ設定**:

```python
# utils/logging.py
import logging
import sys

def setup_logging(level: str = "INFO") -> logging.Logger:
    """ロギング設定を初期化"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )
    return logging.getLogger(__name__)
```

**ログ出力パターン**:

```python
import logging

logger = logging.getLogger(__name__)

class UserService:
    def create_user(self, user_data: dict) -> str:
        logger.info("Creating user", extra={"user_email": user_data.get("email")})
        
        try:
            user_id = self._user_repository.create(user_data)
            logger.info("User created successfully", extra={"user_id": user_id})
            return user_id
        except Exception as e:
            logger.error("Failed to create user", extra={"error": str(e)}, exc_info=True)
            raise
```

**機密情報の扱い**:

```python
# 悪い例
logger.error(f"認証失敗: password={password}")  # パスワードをログ出力

# 良い例
logger.error("認証失敗", extra={"username": username})  # ユーザー名のみ記録
```

### 実装時品質チェック（必須）

**実装完了前に必ず実行：**

```bash
# 1. コードフォーマット（自動修正）
uv run ruff format src/

# 2. リント検査（エラー修正必須）
uv run ruff check src/

# 3. 型チェック（エラー修正必須）
uv run mypy src/

# 4. テスト実行（カバレッジ80%必須）
uv run pytest tests/ --cov=src --cov-fail-under=80

# 5. 結合テスト実行
uv run pytest tests-it/
```

**品質チェック失敗時は実装未完了扱い**

#### コード品質管理

**フォーマット**:

```bash
uv run ruff format src/                 # 自動フォーマット
uv run ruff format --check src/        # フォーマット確認（修正なし）
```

**リント**:

```bash
uv run ruff check src/                  # 全ルールでチェック
uv run ruff check --fix src/            # 自動修正可能なエラーを修正
uv run ruff check --select E,F,I src/  # 特定ルールのみチェック
```

**型チェック**:

```bash
uv run mypy src/                        # srcディレクトリの型チェック
uv run mypy src/ --strict              # 厳密モードで型チェック
uv run mypy src/ --ignore-missing-imports  # 外部ライブラリの型情報不足を無視
```

## テスト戦略

結合テストの実装規則、実行方法、シナリオ設計を定義します。

### テスト実装規則（必須）

#### ユニットテスト設計

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

**1. テスト構造（必須）**
```python
def test_メソッド名_前提条件_期待結果(self):
    """
    Given: 前提条件の説明
    When: 実行する操作
    Then: 期待する結果
    """
    # Given: 前提条件設定
    
    # When: 操作実行
    
    # Then: 結果検証（1アサーションのみ）
    assert expected == actual
```

**2. 例外系テスト（必須）**
- 認証エラー
- ネットワークエラー  
- API制限エラー
- データ形式エラー
- ビジネスロジックエラー

**3. フィクスチャ設計（必須）**
```python
# tests/conftest.py
@pytest.fixture
def mock_external_service():
    """外部サービスのモック（共通）"""
    pass
```

#### 結合テスト設計

**tests-it/ディレクトリ構成（必須）**
```
tests-it/
├── conftest.py          # 結合テスト用設定
└── test_*_integration.py # E2Eシナリオテスト
```

### テスト実行フロー

**段階的テスト実行（推奨順序）：**

```bash
# 1. ユニットテスト（開発中）
uv run pytest tests/ -v

# 2. カバレッジ確認（実装完了前）
uv run pytest tests/ --cov=src --cov-report=html

# 3. 結合テスト（機能完成後）
uv run pytest tests-it/

# 4. 全テスト実行（デプロイ前）
uv run pytest tests/ tests-it/ --cov=src --cov-fail-under=80
```

#### テスト実行コマンド

**ユニットテスト**:

```bash
uv run pytest                          # 全ユニットテスト実行
uv run pytest -v                      # 詳細出力
uv run pytest tests/test_user_service.py  # 特定ファイルのみ
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

### 開発完了基準（必須チェックリスト）

**以下すべてクリアで実装完了：**

- [ ] ユニットテストカバレッジ80%以上
- [ ] 例外系テストの実装完了
- [ ] 結合テストの実装完了
- [ ] すべてのテストが通過
- [ ] `ruff check` エラーなし
- [ ] `mypy` エラーなし
- [ ] `ruff format` 適用済み

**上記未達成の場合はデプロイ不可**

## 運用・デプロイ

Lambda関数のデプロイ手順、運用時のログ確認・監視方法を定義します。

### デプロイ管理

#### デプロイ方式選択

**基本方針**:
- **ZIPパッケージ**: デフォルト方式、シンプルで高速
- **Dockerイメージ**: 指示がある場合のみ、複雑な依存関係や大容量アプリに適用

**切り替え方法**: ZIP用とDocker用でそれぞれ専用の`deploy.sh`を作成・使用

#### Lambda関数のデプロイ

##### ZIPパッケージデプロイ用スクリプト

**ZIPデプロイスクリプト**: `deploy.sh`

```bash
#!/bin/bash

set -euo pipefail

ENVIRONMENT=${1:-dev}
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
[[ -d "$SCRIPT_DIR/src" ]] || { echo "Error: src directory not found"; exit 1; }
[[ -f "$SCRIPT_DIR/lambroll/function.json" ]] || { echo "Error: lambroll/function.json not found"; exit 1; }

echo "Deploying ZIP package..."

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

# lambrollでデプロイ（バージョン公開でロールバック対応）
cd "$SCRIPT_DIR"
lambroll deploy --src "$BUILD_DIR/$PACKAGE_NAME" --publish

echo "Deployment completed successfully!"
```

##### Dockerイメージデプロイ用スクリプト

**Dockerデプロイスクリプト**: `deploy.sh` (Docker用)

```bash
#!/bin/bash

set -euo pipefail

ENVIRONMENT=${1:-dev}
AWS_REGION="ap-northeast-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 必要ツールの確認
command -v docker >/dev/null || { echo "Error: docker not found"; exit 1; }
command -v aws >/dev/null || { echo "Error: aws cli not found"; exit 1; }
command -v lambroll >/dev/null || { echo "Error: lambroll not found"; exit 1; }
[[ -f "$SCRIPT_DIR/Dockerfile" ]] || { echo "Error: Dockerfile not found"; exit 1; }
[[ -f "$SCRIPT_DIR/lambroll/function.json" ]] || { echo "Error: lambroll/function.json not found"; exit 1; }

echo "Deploying Docker image..."

ECR_REPOSITORY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/$(basename "$PWD")-${ENVIRONMENT}"
GIT_SHA=$(git rev-parse --short HEAD)
IMAGE_TAG="sha-${GIT_SHA}"

echo "Image: ${ECR_REPOSITORY}:${IMAGE_TAG}"

# ECRログイン
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REPOSITORY}

# Docker build & push
docker build -t app:build .
docker tag app:build "${ECR_REPOSITORY}:${IMAGE_TAG}"
docker push "${ECR_REPOSITORY}:${IMAGE_TAG}"

# lambroll用環境変数設定
export FUNCTION_NAME="$(basename "$PWD")-${ENVIRONMENT}"
export IMAGE_URI="${ECR_REPOSITORY}:${IMAGE_TAG}"

# lambrollデプロイ（バージョン公開でロールバック対応）
cd lambroll && lambroll deploy --publish

echo "Deployment completed successfully!"
```

#### lambroll設定ファイル

**ZIPデプロイ用設定**: `lambroll/function.json`
```json
{
  "FunctionName": "my-function-dev",
  "Runtime": "python3.13",
  "Handler": "lambda_function.lambda_handler",
  "Role": "arn:aws:iam::123456789012:role/lambda-execution-role",
  "Timeout": 300,
  "MemorySize": 512,
  "Environment": {
    "Variables": {
      "LOG_LEVEL": "INFO"
    }
  }
}
```

**Dockerイメージデプロイする場合**: 同じ`lambroll/function.json`をDocker用に変更
```json
{
  "FunctionName": "{{ must_env `FUNCTION_NAME` }}",
  "PackageType": "Image",
  "Code": {
    "ImageUri": "{{ must_env `IMAGE_URI` }}"
  },
  "Role": "arn:aws:iam::123456789012:role/lambda-execution-role",
  "Timeout": 300,
  "MemorySize": 512,
  "Environment": {
    "Variables": {
      "LOG_LEVEL": "INFO"
    }
  }
}
```

**Dockerfile例**: AWS Lambda公式イメージ使用
```dockerfile
FROM public.ecr.aws/lambda/python:3.13

# 依存関係のインストール
COPY pyproject.toml ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir uv && \
    cd ${LAMBDA_TASK_ROOT} && \
    uv pip install --system --no-cache .

# アプリケーションコードのコピー
COPY src/ ${LAMBDA_TASK_ROOT}/

# ハンドラーの指定
CMD ["lambda_function.lambda_handler"]
```

#### タグ戦略とロールバック

**Git SHAベースタグ戦略**:
- Dockerイメージタグ: `sha-{git_sha}`形式（例: `sha-a1b2c3d`）
- コミットとデプロイの1対1対応で追跡性確保
- イミュータブルなタグで一意性保証

**ロールバック手順**:
```bash
# 前バージョンに自動ロールバック
lambroll rollback

# ドライランで確認
lambroll rollback --dry-run

# 特定バージョンにロールバック
lambroll rollback --version=5
```

**ロールバック機能**:
- lambrollが自動で前バージョンを検出
- `--publish`オプションでバージョン履歴を維持
- 障害時の迅速復旧が可能

### 運用監視

#### ログ確認フロー

**CloudWatch Logs確認**:

```bash
# ログストリーム確認
aws logs describe-log-streams --log-group-name /aws/lambda/my-function

# 最新ログ確認
aws logs tail /aws/lambda/my-function --follow

# 特定時間帯のログ確認
aws logs filter-log-events --log-group-name /aws/lambda/my-function \
  --start-time 1640995200000 --end-time 1641000000000
```

**メトリクス確認**:

```bash
# Lambda関数の実行時間メトリクス確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=my-function \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Average,Maximum

# エラー率確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=my-function \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Sum
```