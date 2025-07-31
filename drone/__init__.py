"""
Drone control and interface module.

This package contains all the drone-related functionality including:
- DroneKit integration
- Drone control and mission planning
- Terminal interface for natural language interactions with the drone
- LiteLLM and Ollama integration for various AI models
"""

# Import main components for easier access
from .drone_control import DroneController, connect_drone, disconnect_drone, takeoff, land, return_home
from .config import config_manager
from .drone_tools import DroneToolsManager 