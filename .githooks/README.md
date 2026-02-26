# Git Hooks

Automated security and policy enforcement for commits.

## Installed Hooks

### `pre-commit`
**Purpose:** Prevents committing credentials and AI attribution

**Blocks commits containing:**

#### 1. Credentials & Secrets
- AWS Access Keys (`AKIA...`)
- OpenAI API Keys (`sk-...`)
- Anthropic API Keys (`sk-ant-...`)
- GitHub Personal Access Tokens
- Private SSH keys
- Generic secrets (passwords, API keys, tokens)

#### 2. AI Attribution (CLAUDE.md Policy)
- "Generated with Claude"
- "Co-Authored-By: Claude"
- Claude Code references
- Anthropic/AI attribution

#### 3. Sensitive Files
- `.env`, `.env.local`, `.env.production`
- `credentials.json`, `secrets.json`
- SSH keys (`id_rsa`, `id_ed25519`, etc.)
- Files in `/keys/` directory (except templates)

### `prepare-commit-msg`
**Purpose:** Automatically strips AI attribution from commit messages

**Removes:**
- 🤖 emojis
- "Generated with Claude/ChatGPT/Copilot"
- "Co-Authored-By: Claude" lines
- Any AI references

## Installation

Already configured! Git is set to use `.githooks/` directory:

```bash
git config core.hooksPath .githooks
```

## Usage

The hooks run automatically:

```bash
git commit -m "Your commit message"
# ✅ Security and policy checks passed.
```

If blocked:

```bash
git commit -m "Your commit message"
# ❌ COMMIT BLOCKED: Credentials detected
# [details shown here]
```

## Bypassing Hooks (Emergency Only)

**NOT RECOMMENDED** - Only for false positives:

```bash
git commit --no-verify -m "Message"
```

## Testing the Hooks

Test credential detection:

```bash
echo "AKIAIOSFODNN7EXAMPLE" > test.txt
git add test.txt
git commit -m "Test"
# Should be blocked
rm test.txt
```

Test AI attribution detection:

```bash
echo "Generated with Claude Code" > test.txt
git add test.txt
git commit -m "Test"
# Should be blocked
rm test.txt
```

## Troubleshooting

### Hooks not running

```bash
# Verify hooks path is configured
git config --get core.hooksPath
# Should output: .githooks

# Make hooks executable (Linux/Mac)
chmod +x .githooks/pre-commit
chmod +x .githooks/prepare-commit-msg
```

### False positives

1. Check if file should be in `.gitignore`
2. Remove the sensitive-looking pattern
3. As last resort: `git commit --no-verify`

## Patterns Detected

See the hook files for complete pattern lists:
- `.githooks/pre-commit` - All credential and attribution patterns
- `.githooks/prepare-commit-msg` - Commit message patterns

## Policy Enforcement

These hooks enforce:
- **P17 (YRSN Project):** Config Manager as credential gateway
- **CLAUDE.md:** No AI attribution in commits
- **Security Best Practices:** Never commit secrets

## Copyright

Copyright (C) 2025 Next Shift Consulting LLC
