terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "slack-bot"
      ManagedBy   = "terraform"
    }
  }
}

module "slack_bot" {
  source = "../../modules/slack-bot"
  
  function_name               = var.function_name
  environment                = var.environment
  slack_bot_token_secret_name = var.slack_bot_token_secret_name
  slack_signing_secret_name   = var.slack_signing_secret_name
  log_retention_days         = var.log_retention_days
  lambda_timeout             = var.lambda_timeout
  lambda_memory_size         = var.lambda_memory_size
  
  tags = var.tags
}