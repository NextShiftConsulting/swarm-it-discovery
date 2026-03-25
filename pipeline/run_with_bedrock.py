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

# Add swarm-it-auth to path for credential management (P18)
sys.path.insert(0, str(Path.home() / "GitHub" / "swarm-it-auth"))

# Add swarm-it-adk client to path for real API access
adk_client_path = Path.home() / "GitHub" / "swarm-it-adk" / "clients" / "python"
if adk_client_path.exists():
    sys.path.insert(0, str(adk_client_path))

# P18 compliant credential check
def _check_aws_credentials():
    """Check for AWS credentials via swarm-it-auth (P18 compliant)."""
    try:
        from swarm_auth.adapters import EnvCredentialAdapter
        adapter = EnvCredentialAdapter()
        aws_key = adapter.retrieve("AWS_ACCESS_KEY_ID")
        if aws_key:
            return True
    except ImportError:
        pass

    # Fall back to ~/.aws/credentials
    try:
        import boto3
        session = boto3.Session()
        creds = session.get_credentials()
        return creds is not None
    except:
        pass

    return False

if not _check_aws_credentials():
    print("Warning: AWS credentials not found.")
    print("Set via swarm-it-auth EnvCredentialAdapter (SWARM_AWS_ACCESS_KEY_ID)")
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
from run import main

if __name__ == "__main__":
    main()
