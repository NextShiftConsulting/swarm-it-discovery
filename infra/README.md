# Infrastructure

AWS + Cloudflare infrastructure for swarms.network.

## Architecture

```
                    CLOUDFLARE DNS
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
   swarms.network   api.swarms.network   swarmit.nextshiftconsulting.com
         │               │               │
         ▼               ▼               ▼
    CloudFront      API Gateway      CloudFront
         │               │               │
         ▼               ▼               ▼
    S3 (landing)     Lambda          S3 (gatsby)
                         │
                         ▼
                   Lambda (pipeline)
                   [daily cron]
```

## Prerequisites

1. **AWS Account** with credentials configured
2. **Cloudflare Account** with swarms.network zone
3. **ACM Certificates** (must be in us-east-1 for CloudFront):
   - `*.swarms.network` and `swarms.network`
   - `*.nextshiftconsulting.com`

## Setup

### 1. Create terraform.tfvars

```hcl
# Cloudflare
cloudflare_api_token    = "your-api-token"
cloudflare_zone_id      = "your-zone-id"

# AWS ACM certificates (us-east-1)
swarms_network_cert_arn = "arn:aws:acm:us-east-1:ACCOUNT:certificate/XXX"
acm_certificate_arn     = "arn:aws:acm:us-east-1:ACCOUNT:certificate/YYY"
api_certificate_arn     = "arn:aws:acm:us-east-1:ACCOUNT:certificate/ZZZ"
```

**Never commit terraform.tfvars!**

### 2. Initialize and Apply

```bash
cd infra
terraform init
terraform plan
terraform apply
```

### 3. Deploy Landing Page

```bash
# Build (just static files, no build step needed)
cd ../landing/src

# Upload to S3
aws s3 sync . s3://swarms-network-landing --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw landing_cloudfront_id) \
  --paths "/*"
```

### 4. Deploy Gatsby Site

```bash
cd ../site
npm run build

aws s3 sync public/ s3://swarmit-nextshift-site --delete

aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

### 5. Deploy Lambda Functions

```bash
# Package pipeline Lambda
cd ../pipeline
zip -r ../infra/lambda_pipeline.zip .

# Package API Lambda
cd ../api
zip -r ../infra/lambda_api.zip .

# Update Lambda
aws lambda update-function-code \
  --function-name swarmit-paper-pipeline \
  --zip-file fileb://../infra/lambda_pipeline.zip

aws lambda update-function-code \
  --function-name swarmit-api \
  --zip-file fileb://../infra/lambda_api.zip
```

## Domains

| Domain | Purpose | Backend |
|--------|---------|---------|
| `swarms.network` | Landing page | CloudFront → S3 |
| `api.swarms.network` | RSCT API | API Gateway → Lambda |
| `swarmit.nextshiftconsulting.com` | Research discovery | CloudFront → S3 |

## Secrets Management

Store sensitive values in AWS Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name swarmit/openai \
  --secret-string '{"api_key":"sk-..."}'
```

Lambda functions retrieve secrets at runtime.

## Costs

Estimated monthly costs (low traffic):
- CloudFront: ~$1-5
- S3: ~$1
- Lambda: ~$1-5
- API Gateway: ~$1-3
- **Total: ~$5-15/month**
