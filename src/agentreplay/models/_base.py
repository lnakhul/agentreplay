"""Shared configuration for AgentReplay domain models."""

from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    """Base configuration shared by immutable AgentReplay domain models."""

    model_config = ConfigDict(extra="forbid", frozen=True)
