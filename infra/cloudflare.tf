# Cloudflare DNS Configuration for swarms.network

terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token"
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID for swarms.network"
}

# Landing page: swarms.network
resource "cloudflare_record" "root" {
  zone_id = var.cloudflare_zone_id
  name    = "@"
  type    = "CNAME"
  value   = aws_cloudfront_distribution.landing.domain_name
  proxied = true
}

resource "cloudflare_record" "www" {
  zone_id = var.cloudflare_zone_id
  name    = "www"
  type    = "CNAME"
  value   = aws_cloudfront_distribution.landing.domain_name
  proxied = true
}

# API: api.swarms.network
resource "cloudflare_record" "api" {
  zone_id = var.cloudflare_zone_id
  name    = "api"
  type    = "CNAME"
  value   = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].target_domain_name
  proxied = false  # Don't proxy API traffic - need direct connection for WebSocket/SSL
}

# S3 bucket for landing page
resource "aws_s3_bucket" "landing" {
  bucket = "swarms-network-landing"
}

resource "aws_s3_bucket_website_configuration" "landing" {
  bucket = aws_s3_bucket.landing.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "landing" {
  bucket = aws_s3_bucket.landing.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "landing" {
  bucket = aws_s3_bucket.landing.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.landing.arn}/*"
      }
    ]
  })
}

# CloudFront for landing page
resource "aws_cloudfront_distribution" "landing" {
  origin {
    domain_name = aws_s3_bucket_website_configuration.landing.website_endpoint
    origin_id   = "S3-landing"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  aliases = ["swarms.network", "www.swarms.network"]

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-landing"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = var.swarms_network_cert_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}

variable "swarms_network_cert_arn" {
  description = "ACM certificate ARN for *.swarms.network (must be in us-east-1)"
}

# Outputs
output "landing_url" {
  value = "https://swarms.network"
}

output "landing_s3_bucket" {
  value = aws_s3_bucket.landing.bucket
}

output "landing_cloudfront_id" {
  value = aws_cloudfront_distribution.landing.id
}
