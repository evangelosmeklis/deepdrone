"""
Configuration management for DeepDrone terminal application.
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    name: str
    provider: str  # 'openai', 'anthropic', 'ollama', 'huggingface', etc.
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_id: str
    max_tokens: int = 2048
    temperature: float = 0.7

class DroneConfig(BaseModel):
    """Configuration for drone connection."""
    default_connection_string: str = "udp:127.0.0.1:14550"
    timeout: int = 30
    default_altitude: float = 30.0
    max_altitude: float = 100.0

class AppSettings(BaseSettings):
    """Main application settings."""
    
    # File paths
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".deepdrone")
    models_file: Path = Field(default_factory=lambda: Path.home() / ".deepdrone" / "models.json")
    
    # Default model
    default_model: str = "gpt-3.5-turbo"
    
    # Drone settings
    drone: DroneConfig = Field(default_factory=DroneConfig)
    
    # Terminal settings
    show_thinking: bool = True
    auto_save_chat: bool = True
    chat_history_limit: int = 100
    
    class Config:
        env_prefix = "DEEPDRONE_"
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables

class ConfigManager:
    """Manages application configuration and model settings."""
    
    def __init__(self):
        self.settings = AppSettings()
        self.models: Dict[str, ModelConfig] = {}
        self._ensure_config_dir()
        self._load_models()
    
    def _ensure_config_dir(self):
        """Ensure configuration directory exists."""
        self.settings.config_dir.mkdir(exist_ok=True)
    
    def _load_models(self):
        """Load model configurations from file."""
        if self.settings.models_file.exists():
            try:
                with open(self.settings.models_file, 'r') as f:
                    models_data = json.load(f)
                    self.models = {
                        name: ModelConfig(**config)
                        for name, config in models_data.items()
                    }
            except Exception as e:
                print(f"Error loading models config: {e}")
                self.models = {}
        else:
            # Create default models
            self._create_default_models()
    
    def _create_default_models(self):
        """Create default model configurations."""
        self.models = {
            "gpt-3.5-turbo": ModelConfig(
                name="gpt-3.5-turbo",
                provider="openai",
                model_id="gpt-3.5-turbo",
                max_tokens=2048,
                temperature=0.7
            ),
            "gpt-4": ModelConfig(
                name="gpt-4",
                provider="openai", 
                model_id="gpt-4",
                max_tokens=2048,
                temperature=0.7
            ),
            "claude-3-sonnet": ModelConfig(
                name="claude-3-sonnet",
                provider="anthropic",
                model_id="claude-3-sonnet-20240229",
                max_tokens=2048,
                temperature=0.7
            ),
            "llama3.1": ModelConfig(
                name="llama3.1",
                provider="ollama",
                model_id="llama3.1:latest",
                base_url="http://localhost:11434",
                max_tokens=2048,
                temperature=0.7
            ),
            "codestral": ModelConfig(
                name="codestral",
                provider="ollama",
                model_id="codestral:latest",
                base_url="http://localhost:11434",
                max_tokens=2048,
                temperature=0.7
            )
        }
        self.save_models()
    
    def save_models(self):
        """Save model configurations to file."""
        try:
            models_data = {
                name: config.model_dump()
                for name, config in self.models.items()
            }
            with open(self.settings.models_file, 'w') as f:
                json.dump(models_data, f, indent=2)
        except Exception as e:
            print(f"Error saving models config: {e}")
    
    def add_model(self, config: ModelConfig):
        """Add a new model configuration."""
        self.models[config.name] = config
        self.save_models()
    
    def remove_model(self, name: str) -> bool:
        """Remove a model configuration."""
        if name in self.models:
            del self.models[name]
            self.save_models()
            return True
        return False
    
    def get_model(self, name: str) -> Optional[ModelConfig]:
        """Get a model configuration by name."""
        return self.models.get(name)
    
    def list_models(self) -> List[str]:
        """List all available model names."""
        return list(self.models.keys())
    
    def set_api_key(self, model_name: str, api_key: str) -> bool:
        """Set API key for a model."""
        if model_name in self.models:
            self.models[model_name].api_key = api_key
            self.save_models()
            return True
        return False
    
    def get_ollama_models(self) -> List[str]:
        """Get list of available Ollama models."""
        ollama_models = []
        for name, config in self.models.items():
            if config.provider == "ollama":
                ollama_models.append(name)
        return ollama_models
    
    def get_api_models(self) -> List[str]:
        """Get list of models that require API keys."""
        api_models = []
        for name, config in self.models.items():
            if config.provider in ["openai", "anthropic", "huggingface"]:
                api_models.append(name)
        return api_models

# Global config manager instance
config_manager = ConfigManager()