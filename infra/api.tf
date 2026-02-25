# Swarm-It API Infrastructure - swarms.network
# Hosts the RSCT certification API

# API Gateway
resource "aws_apigatewayv2_api" "swarmit" {
  name          = "swarmit-api"
  protocol_type = "HTTP"
  description   = "Swarm-It RSCT Certification API"

  cors_configuration {
    allow_origins = [
      "https://swarmit.nextshiftconsulting.com",
      "https://nextshiftconsulting.com",
      "https://swarms.network",
      "http://localhost:8000"
    ]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization", "X-API-Key"]
    max_age       = 3600
  }
}

# Custom domain for API
resource "aws_apigatewayv2_domain_name" "api" {
  domain_name = var.api_domain

  domain_name_configuration {
    certificate_arn = var.api_certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

variable "api_certificate_arn" {
  description = "ACM certificate ARN for api.swarms.network"
}

resource "aws_apigatewayv2_api_mapping" "api" {
  api_id      = aws_apigatewayv2_api.swarmit.id
  domain_name = aws_apigatewayv2_domain_name.api.id
  stage       = aws_apigatewayv2_stage.default.id
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.swarmit.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      method         = "$context.httpMethod"
      path           = "$context.path"
      status         = "$context.status"
      responseLength = "$context.responseLength"
    })
  }
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/apigateway/swarmit-api"
  retention_in_days = 14
}

# Lambda for API endpoints
resource "aws_lambda_function" "api" {
  filename         = "lambda_api.zip"
  function_name    = "swarmit-api"
  role             = aws_iam_role.api_lambda_role.arn
  handler          = "handler.main"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      ENVIRONMENT = var.environment
      LOG_LEVEL   = "INFO"
    }
  }
}

resource "aws_iam_role" "api_lambda_role" {
  name = "swarmit-api-lambda-role"

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

resource "aws_iam_role_policy_attachment" "api_lambda_basic" {
  role       = aws_iam_role.api_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# API Routes
resource "aws_apigatewayv2_integration" "api" {
  api_id                 = aws_apigatewayv2_api.swarmit.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "certify" {
  api_id    = aws_apigatewayv2_api.swarmit.id
  route_key = "POST /api/v1/certify"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.swarmit.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

resource "aws_apigatewayv2_route" "statistics" {
  api_id    = aws_apigatewayv2_api.swarmit.id
  route_key = "GET /api/v1/statistics"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.swarmit.execution_arn}/*/*"
}

# DNS managed by Cloudflare - see cloudflare.tf

# Outputs
output "api_endpoint" {
  value = "https://${var.api_domain}"
}

output "api_gateway_id" {
  value = aws_apigatewayv2_api.swarmit.id
}
