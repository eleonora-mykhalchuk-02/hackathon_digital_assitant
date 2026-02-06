"""Configuration management for the application."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # AWS Bedrock Configuration
    aws_region: str = Field(default="us-east-1", description="AWS region for Bedrock")
    aws_access_key_id: str = Field(default="", description="AWS access key ID")
    aws_secret_access_key: str = Field(default="", description="AWS secret access key")
    aws_session_token: Optional[str] = Field(default=None, description="AWS session token (optional)")

    # Model Configuration
    chatbot_model: str = Field(
        default="anthropic.claude-sonnet-4-5-v1:0",
        description="AWS Bedrock model ID for chatbot"
    )
    judge_model: str = Field(
        default="anthropic.claude-sonnet-4-5-v1:0",
        description="AWS Bedrock model ID for judge"
    )

    # Feature Flags
    enable_input_critique: bool = Field(default=True, description="Enable judge critique of user input")
    enable_feedback_loop: bool = Field(default=True, description="Enable iterative refinement")
    max_refinement_iterations: int = Field(default=2, description="Maximum refinement iterations")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=True, description="Debug mode")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="CORS allowed origins"
    )


class CriteriaConfig:
    """Manages judge criteria configuration from YAML file."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize criteria configuration.

        Args:
            config_path: Path to criteria.yaml file. If None, uses default location.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "criteria.yaml"

        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load criteria configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Criteria config not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            self._config = yaml.safe_load(f)

    def reload(self) -> None:
        """Reload criteria configuration (hot reload support)."""
        self.load()

    @property
    def criteria(self) -> List[Dict[str, Any]]:
        """Get all criteria definitions (output criteria by default for backwards compatibility)."""
        return self._config.get("output_criteria", self._config.get("criteria", []))

    @property
    def input_criteria(self) -> List[Dict[str, Any]]:
        """Get criteria for evaluating user input."""
        return self._config.get("input_criteria", [])

    @property
    def output_criteria(self) -> List[Dict[str, Any]]:
        """Get criteria for evaluating chatbot output."""
        return self._config.get("output_criteria", self._config.get("criteria", []))

    @property
    def enabled_criteria(self) -> List[Dict[str, Any]]:
        """Get only enabled output criteria."""
        return [c for c in self.output_criteria if c.get("enabled", True)]

    @property
    def enabled_input_criteria(self) -> List[Dict[str, Any]]:
        """Get only enabled input criteria."""
        return [c for c in self.input_criteria if c.get("enabled", True)]

    @property
    def profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all quality profiles."""
        return self._config.get("profiles", {})

    @property
    def settings(self) -> Dict[str, Any]:
        """Get application settings from criteria config."""
        return self._config.get("settings", {})

    @property
    def active_profile(self) -> str:
        """Get active profile name."""
        return self.settings.get("active_profile", "moderate")

    @property
    def overall_threshold(self) -> float:
        """Get overall quality threshold from active profile."""
        profile = self.profiles.get(self.active_profile, {})
        return profile.get("overall_threshold", 60)

    @property
    def traffic_light_thresholds(self) -> Dict[str, int]:
        """Get traffic light display thresholds."""
        return self.settings.get("traffic_light", {
            "green_threshold": 70,
            "orange_threshold": 40
        })

    def get_criterion(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific criterion by name.

        Args:
            name: Criterion name

        Returns:
            Criterion dict or None if not found
        """
        for criterion in self.criteria:
            if criterion.get("name") == name:
                return criterion
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Export full configuration as dictionary."""
        return self._config.copy()


# Global configuration instances
settings = Settings()
criteria_config = CriteriaConfig()
