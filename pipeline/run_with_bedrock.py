#!/usr/bin/env python3
"""
Run discovery pipeline with AWS Bedrock + Swarm-It API.

P18 Compliance: All credentials via swarm-it-auth.

Uses:
- AWS Bedrock Titan for semantic matching
- api.swarms.network for RSCT certification

Usage:
    python3 pipeline/run_with_bedrock.py --days 1 --min-score 0.35
"""

import os
import sys
from pathlib import Path

# Change to project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# P18 v3.0 - Unified credential access
from swarm_auth import has_credential  # noqa: E402

# Add swarm-it-adk client to path for real API access
adk_client_path = Path.home() / "GitHub" / "swarm-it-adk" / "clients" / "python"
if adk_client_path.exists():
    sys.path.insert(0, str(adk_client_path))


def _check_aws_credentials():
    """Check for AWS credentials via P18 gateway."""
    if has_credential("AWS_ACCESS_KEY_ID"):
        return True
    # Fall back to ~/.aws/credentials
    try:
        import boto3
        session = boto3.Session()
        creds = session.get_credentials()
        return creds is not None
    except Exception:
        pass
    return False

if not _check_aws_credentials():
    print("Warning: AWS credentials not found.")
    print("Set via swarm_auth.get_credential('AWS_ACCESS_KEY_ID')")
    print("Or configure ~/.aws/credentials")

# Set default region if not set
if not os.environ.get("AWS_DEFAULT_REGION"):
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Set Swarm-It API URL
if not os.environ.get("SWARMIT_URL"):
    os.environ["SWARMIT_URL"] = "https://api.swarms.network"

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

# Now import and run
from run import main  # noqa: E402

if __name__ == "__main__":
    main()
