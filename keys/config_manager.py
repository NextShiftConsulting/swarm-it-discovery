"""
Configuration Manager - Single Gateway for All Credentials (P17)

Usage:
    from keys.config_manager import get_config
    config = get_config()

    # Get AWS credentials (checks env vars, config file, ~/.aws/credentials)
    access_key = config.aws_access_key_id
    secret_key = config.aws_secret_access_key
    region = config.aws_region
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class Config:
    """Configuration container with credential priority handling."""

    _config_data: dict = field(default_factory=dict)
    _config_loaded: bool = False

    def __post_init__(self):
        self._load_config()

    def _load_config(self):
        """Load config from yaml file if exists."""
        if self._config_loaded:
            return

        config_path = Path(__file__).parent / "aws_config.yaml"
        if config_path.exists() and HAS_YAML:
            with open(config_path) as f:
                self._config_data = yaml.safe_load(f) or {}
        else:
            self._config_data = {}

        self._config_loaded = True

    def _get_nested(self, *keys, default=None):
        """Get nested config value."""
        data = self._config_data
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            else:
                return default
        return data if data is not None else default

    @property
    def aws_access_key_id(self) -> Optional[str]:
        """Get AWS access key (env var > config file > None for boto3 fallback)."""
        key = os.getenv('AWS_ACCESS_KEY_ID')
        if key:
            return key
        key = self._get_nested('aws', 'access_key_id')
        if key:
            return key
        return None

    @property
    def aws_secret_access_key(self) -> Optional[str]:
        """Get AWS secret key."""
        key = os.getenv('AWS_SECRET_ACCESS_KEY')
        if key:
            return key
        key = self._get_nested('aws', 'secret_access_key')
        if key:
            return key
        return None

    @property
    def aws_region(self) -> str:
        """Get AWS region."""
        return (
            os.getenv('AWS_REGION') or
            os.getenv('AWS_DEFAULT_REGION') or
            self._get_nested('aws', 'region') or
            'us-east-1'
        )

    @property
    def s3_bucket(self) -> str:
        """Get S3 bucket name."""
        return (
            os.getenv('S3_BUCKET') or
            self._get_nested('s3', 'site_bucket') or
            'swarmit-nextshift-site'
        )

    @property
    def cloudfront_distribution_id(self) -> Optional[str]:
        """Get CloudFront distribution ID."""
        return (
            os.getenv('CLOUDFRONT_DISTRIBUTION_ID') or
            self._get_nested('cloudfront', 'distribution_id')
        )

    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key."""
        return (
            os.getenv('OPENAI_API_KEY') or
            self._get_nested('openai', 'api_key')
        )

    @property
    def environment(self) -> str:
        """Get environment (dev/staging/prod)."""
        return (
            os.getenv('ENVIRONMENT') or
            self._get_nested('environment') or
            'prod'
        )


_config: Optional[Config] = None


def get_config() -> Config:
    """Get singleton config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
