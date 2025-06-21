# Slack Bot TokenをSecrets Managerに格納
resource "aws_secretsmanager_secret" "slack_bot_token" {
  name        = "${var.function_name}-${var.environment}-bot-token"
  description = "Slack Bot Token for ${var.function_name}"
  
  tags = merge(var.tags, {
    Name        = "${var.function_name}-${var.environment}-bot-token"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "slack_bot_token" {
  secret_id     = aws_secretsmanager_secret.slack_bot_token.id
  secret_string = "PLACEHOLDER_TOKEN" # 手動で設定する必要がある
  
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Slack Signing SecretをSecrets Managerに格納
resource "aws_secretsmanager_secret" "slack_signing_secret" {
  name        = "${var.function_name}-${var.environment}-signing-secret"
  description = "Slack Signing Secret for ${var.function_name}"
  
  tags = merge(var.tags, {
    Name        = "${var.function_name}-${var.environment}-signing-secret"
    Environment = var.environment
  })
}

resource "aws_secretsmanager_secret_version" "slack_signing_secret" {
  secret_id     = aws_secretsmanager_secret.slack_signing_secret.id
  secret_string = "PLACEHOLDER_SECRET" # 手動で設定する必要がある
  
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Bedrock用IAM権限は後述のポリシーで設定

# Lambda実行用IAMロール
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.function_name}-${var.environment}-lambda-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(var.tags, {
    Name        = "${var.function_name}-${var.environment}-lambda-role"
    Environment = var.environment
  })
}

# Lambda基本実行権限をアタッチ
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Secrets Manager読み取り権限
resource "aws_iam_role_policy" "secrets_manager_policy" {
  name = "${var.function_name}-${var.environment}-secrets-policy"
  role = aws_iam_role.lambda_execution_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.slack_bot_token.arn,
          aws_secretsmanager_secret.slack_signing_secret.arn
        ]
      }
    ]
  })
}

# Bedrock使用権限
resource "aws_iam_role_policy" "bedrock_policy" {
  name = "${var.function_name}-${var.environment}-bedrock-policy"
  role = aws_iam_role.lambda_execution_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:*:*:foundation-model/anthropic.claude-*",
          "arn:aws:bedrock:*:*:inference-profile/*"
        ]
      }
    ]
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}-${var.environment}"
  retention_in_days = var.log_retention_days
  
  tags = merge(var.tags, {
    Name        = "${var.function_name}-${var.environment}-logs"
    Environment = var.environment
  })
}

# Lambda関数
resource "aws_lambda_function" "slack_bot" {
  function_name = "${var.function_name}-${var.environment}"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size
  
  # lambrollでデプロイするため、ダミーのZIPファイルを作成
  filename         = "${path.module}/dummy.zip"
  source_code_hash = data.archive_file.dummy_zip.output_base64sha256
  
  environment {
    variables = {
      SLACK_BOT_TOKEN_SECRET_ARN     = aws_secretsmanager_secret.slack_bot_token.arn
      SLACK_SIGNING_SECRET_SECRET_ARN = aws_secretsmanager_secret.slack_signing_secret.arn
    }
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_cloudwatch_log_group.lambda_logs,
  ]
  
  tags = merge(var.tags, {
    Name        = "${var.function_name}-${var.environment}"
    Environment = var.environment
  })
}

# 現在のAWSリージョンを取得
data "aws_region" "current" {}

# ダミーZIPファイル作成用
data "archive_file" "dummy_zip" {
  type        = "zip"
  output_path = "${path.module}/dummy.zip"
  
  source {
    content  = "# Placeholder for lambroll deployment"
    filename = "dummy.py"
  }
}

# Lambda Function URL
resource "aws_lambda_function_url" "slack_bot" {
  function_name      = aws_lambda_function.slack_bot.function_name
  authorization_type = "NONE" # Slack署名で検証するため
  
  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["POST"]
    allow_headers     = ["*"]
    max_age          = 86400
  }
}

# Lambda Function URLへのInvoke権限
resource "aws_lambda_permission" "allow_function_url" {
  statement_id           = "AllowExecutionFromFunctionURL"
  action                = "lambda:InvokeFunctionUrl"
  function_name         = aws_lambda_function.slack_bot.function_name
  principal             = "*"
  function_url_auth_type = "NONE"
}