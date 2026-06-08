output "workflow_table_name" {
  description = "DynamoDB application table name"
  value       = aws_dynamodb_table.workflow.name
}

output "workflow_table_arn" {
  description = "DynamoDB application table ARN"
  value       = aws_dynamodb_table.workflow.arn
}

output "workflow_lambda_role_arn" {
  description = "IAM role ARN for workflow Lambda functions"
  value       = aws_iam_role.workflow_lambda.arn
}
