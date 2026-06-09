resource "aws_iam_role" "workflow_lambda" {
  name = "${var.project_name}-workflow-lambda-role"

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
}

resource "aws_iam_policy" "workflow_lambda_logs" {
  name        = "${var.project_name}-workflow-lambda-logs"
  description = "Allow Lambda functions to write CloudWatch Logs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_policy" "workflow_lambda_dynamodb" {
  name        = "${var.project_name}-workflow-dynamodb"
  description = "Least-privilege DynamoDB access for workflow persistence"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:TransactWriteItems",
          "dynamodb:DescribeTable",
        ]
        Resource = [
          aws_dynamodb_table.workflow.arn,
          "${aws_dynamodb_table.workflow.arn}/index/*",
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "workflow_lambda_logs" {
  role       = aws_iam_role.workflow_lambda.name
  policy_arn = aws_iam_policy.workflow_lambda_logs.arn
}

resource "aws_iam_role_policy_attachment" "workflow_lambda_dynamodb" {
  role       = aws_iam_role.workflow_lambda.name
  policy_arn = aws_iam_policy.workflow_lambda_dynamodb.arn
}
