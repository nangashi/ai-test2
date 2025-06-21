variable "aws_region" {
  description = "AWSリージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "environment" {
  description = "環境名"
  type        = string
  default     = "dev"
}

variable "function_name" {
  description = "Lambda関数名"
  type        = string
  default     = "slack-bot"
}

variable "slack_bot_token_secret_name" {
  description = "Slack Bot TokenのSecrets Manager名"
  type        = string
  default     = "slack-bot-token"
}

variable "slack_signing_secret_name" {
  description = "Slack Signing SecretのSecrets Manager名"
  type        = string
  default     = "slack-signing-secret"
}

variable "log_retention_days" {
  description = "CloudWatch Logsの保持日数"
  type        = number
  default     = 14
}

variable "lambda_timeout" {
  description = "Lambda関数のタイムアウト（秒）"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda関数のメモリサイズ（MB）"
  type        = number
  default     = 256
}

variable "tags" {
  description = "リソースに付与するタグ"
  type        = map(string)
  default = {
    Project = "slack-bot"
  }
}