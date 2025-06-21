output "lambda_function_name" {
  description = "Lambda関数名"
  value       = aws_lambda_function.slack_bot.function_name
}

output "lambda_function_arn" {
  description = "Lambda関数ARN"
  value       = aws_lambda_function.slack_bot.arn
}

output "lambda_function_url" {
  description = "Lambda Function URL"
  value       = aws_lambda_function_url.slack_bot.function_url
}

output "lambda_role_arn" {
  description = "Lambda実行ロールARN"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "slack_bot_token_secret_arn" {
  description = "Slack Bot Token Secret ARN"
  value       = aws_secretsmanager_secret.slack_bot_token.arn
}

output "slack_signing_secret_arn" {
  description = "Slack Signing Secret ARN"
  value       = aws_secretsmanager_secret.slack_signing_secret.arn
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch Log Group名"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}