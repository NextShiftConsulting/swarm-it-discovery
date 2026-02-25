# Swarmit Keys & Configuration

This directory stores sensitive configuration and credentials.

**⚠️ DO NOT COMMIT THIS DIRECTORY TO GIT ⚠️**

---

## Credential Priority (3-Tier)

Credentials are loaded in this order (first found wins):

1. **Environment variables** (highest priority)
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - `OPENAI_API_KEY`

2. **Config file** (medium priority)
   - `aws_config.yaml` in this directory

3. **Standard files** (lowest priority, automatic fallback)
   - `~/.aws/credentials` (read via boto3)
   - `~/.aws/config` (read via boto3)

---

## Setup

### Option 1: Use AWS CLI Config (Recommended)

```bash
aws configure
```

Then leave `aws_config.yaml` credentials empty - they'll be found automatically.

### Option 2: Direct Config File

Create `aws_config.yaml`:

```yaml
aws:
  access_key_id: "AKIA..."
  secret_access_key: "..."
  region: "us-east-1"

openai:
  api_key: "sk-..."

environment: "prod"
```

**Never commit this file!**

---

## Security

- This directory is gitignored
- Pre-commit hook blocks credential patterns
- Use IAM roles in production (Lambda)
