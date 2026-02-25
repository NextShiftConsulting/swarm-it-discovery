# CodeBuild for Swarm-It API container

resource "aws_s3_bucket" "codebuild" {
  bucket = "swarmit-codebuild-${data.aws_caller_identity.current.account_id}"
}

data "aws_caller_identity" "current" {}

resource "aws_codebuild_project" "api" {
  name          = "swarmit-api-build"
  description   = "Build Swarm-It API container with yrsn/PyTorch"
  build_timeout = 30
  service_role  = aws_iam_role.codebuild.arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_MEDIUM"
    image                       = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
    privileged_mode             = true  # Required for Docker

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = data.aws_caller_identity.current.account_id
    }

    environment_variable {
      name  = "AWS_REGION"
      value = var.aws_region
    }

    environment_variable {
      name  = "IMAGE_REPO_NAME"
      value = "swarmit-api"
    }

    environment_variable {
      name  = "ECR_REPO_URI"
      value = aws_ecr_repository.api.repository_url
    }
  }

  source {
    type     = "S3"
    location = "${aws_s3_bucket.codebuild.bucket}/swarmit-api-source.zip"
    buildspec = <<-EOF
      version: 0.2
      phases:
        pre_build:
          commands:
            - echo Logging in to Amazon ECR...
            - aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URI
        build:
          commands:
            - echo Building Docker image...
            - cd sidecar
            - docker build -t swarmit-api:latest .
            - docker tag swarmit-api:latest $ECR_REPO_URI:latest
        post_build:
          commands:
            - echo Pushing to ECR...
            - docker push $ECR_REPO_URI:latest
            - echo Done!
    EOF
  }

  logs_config {
    cloudwatch_logs {
      group_name  = "/codebuild/swarmit-api"
      stream_name = "build"
    }
  }
}

resource "aws_iam_role" "codebuild" {
  name = "swarmit-codebuild-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "codebuild.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "codebuild" {
  name = "swarmit-codebuild-policy"
  role = aws_iam_role.codebuild.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ]
        Resource = "${aws_s3_bucket.codebuild.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = aws_ecr_repository.api.arn
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "codebuild" {
  name              = "/codebuild/swarmit-api"
  retention_in_days = 7
}

output "codebuild_project" {
  value = aws_codebuild_project.api.name
}

output "codebuild_s3_bucket" {
  value = aws_s3_bucket.codebuild.bucket
}
