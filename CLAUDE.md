# Swarmit-Site Project Instructions

## Git Commits

**NEVER add Claude attribution of any kind.** This includes:
- No "Generated with Claude Code" messages
- No "Co-Authored-By: Claude" lines
- No references to Claude, Anthropic, or AI assistance in commit messages
- No AI attribution in code comments or documentation

## Patent Notice

This project includes patented technology. See [PATENT_NOTICE.md](PATENT_NOTICE.md).

All production code must properly attribute the patent-pending status in user-facing documentation.

## Security

### Credential Management

All credentials must be stored in environment variables or the `/keys/` directory (which is gitignored).

**Never commit:**
- AWS credentials
- API keys (OpenAI, etc.)
- .env files
- Service account files

### Pre-commit Hooks

Security hooks are installed in `.githooks/`. Configure with:
```bash
git config core.hooksPath .githooks
```

## Architecture

```
swarmit-site/
├── site/           # Gatsby + TypeScript frontend
├── pipeline/       # Python paper discovery pipeline
├── landing/        # swarms.network landing page
├── infra/          # Terraform AWS infrastructure
└── keys/           # Local credentials (gitignored)
```

## Deployment

### Static Site (S3 + CloudFront)

```bash
cd site
npm run build
./scripts/deploy.sh
```

### Environment Variables

Required for pipeline:
- `OPENAI_API_KEY` - For LLM analysis
- `AWS_ACCESS_KEY_ID` - For S3/CloudFront deployment
- `AWS_SECRET_ACCESS_KEY` - For AWS services
