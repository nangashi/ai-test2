output "lambda_function_name" {
  description = "Lambda関数名"
  value       = module.slack_bot.lambda_function_name
}

output "lambda_function_arn" {
  description = "Lambda関数ARN"
  value       = module.slack_bot.lambda_function_arn
}

output "lambda_function_url" {
  description = "Lambda Function URL"
  value       = module.slack_bot.lambda_function_url
}

output "lambda_role_arn" {
  description = "Lambda実行ロールARN"
  value       = module.slack_bot.lambda_role_arn
}

output "slack_bot_token_secret_arn" {
  description = "Slack Bot Token Secret ARN"
  value       = module.slack_bot.slack_bot_token_secret_arn
}

output "slack_signing_secret_arn" {
  description = "Slack Signing Secret ARN"
  value       = module.slack_bot.slack_signing_secret_arn
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch Log Group名"
  value       = module.slack_bot.cloudwatch_log_group_name
}