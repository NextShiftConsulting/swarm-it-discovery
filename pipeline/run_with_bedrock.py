#!/usr/bin/env python3
"""
Run discovery pipeline with AWS Bedrock + Swarm-It API.

Uses:
- AWS Bedrock Titan for semantic matching
- api.swarms.network for RSCT certification

Prerequisites:
    Set AWS credentials via environment variables or keys/aws_credentials.sh:

    export AWS_ACCESS_KEY_ID=your-key
    export AWS_SECRET_ACCESS_KEY=your-secret
    export AWS_DEFAULT_REGION=us-east-1

Usage:
    python3 pipeline/run_with_bedrock.py --days 1 --min-score 0.35
"""

import os
import sys
from pathlib import Path

# Change to project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# Add swarm-it-adk client to path for real API access
adk_client_path = Path.home() / "GitHub" / "swarm-it-adk" / "clients" / "python"
if adk_client_path.exists():
    sys.path.insert(0, str(adk_client_path))

# Check for AWS credentials
if not os.environ.get("AWS_ACCESS_KEY_ID"):
    # Try to load from keys file (gitignored)
    keys_file = project_root / "keys" / "aws_credentials.sh"
    if keys_file.exists():
        print(f"Loading AWS credentials from {keys_file}")
        import subprocess
        result = subprocess.run(
            f"source {keys_file} && env",
            shell=True, capture_output=True, text=True
        )
        for line in result.stdout.split("\n"):
            if line.startswith("AWS_"):
                key, _, value = line.partition("=")
                os.environ[key] = value
    else:
        print("Warning: AWS credentials not found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("Or create keys/aws_credentials.sh with exports")

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
