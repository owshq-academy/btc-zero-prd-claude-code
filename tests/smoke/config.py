"""Configuration loader for smoke test framework."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class EnvironmentConfig(BaseModel):
    """GCP environment configuration."""

    project: str
    bucket: str
    dataset: str
    region: str = "us-central1"


class StageConfig(BaseModel):
    """Configuration for a single stage."""

    timeout_seconds: int = 30
    folder: str | None = None
    poll_interval_seconds: int | None = None
    folders_to_check: list[str] | None = None
    critical_fields: list[str] | None = None
    table: str | None = None
    lookback_minutes: int | None = None
    severity_threshold: str | None = None


class SmokeConfig(BaseModel):
    """Complete smoke test configuration."""

    environments: dict[str, EnvironmentConfig]
    stages: dict[str, StageConfig]
    vendors: dict[str, dict[str, str]] = Field(default_factory=dict)

    def get_env(self, env: str) -> EnvironmentConfig:
        """Get configuration for a specific environment."""
        if env not in self.environments:
            raise ValueError(f"Unknown environment: {env}")
        return self.environments[env]

    def get_stage(self, stage_name: str) -> StageConfig:
        """Get configuration for a specific stage."""
        return self.stages.get(stage_name, StageConfig())


def load_config(env: str | None = None) -> SmokeConfig:
    """Load configuration from YAML file.

    Args:
        env: Optional environment name to validate exists

    Returns:
        Parsed SmokeConfig object
    """
    config_path = Path(__file__).parent / "config" / "smoke_config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    config = SmokeConfig(**data)

    if env and env not in config.environments:
        raise ValueError(f"Unknown environment: {env}")

    return config
