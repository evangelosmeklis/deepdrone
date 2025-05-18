"""
Drone control and interface module.

This package contains all the drone-related functionality including:
- DroneKit integration
- Drone control and mission planning
- Chat interface for natural language interactions with the drone
"""

# Import main components for easier access
from .drone_control import DroneController, connect_drone, disconnect_drone, takeoff, land, return_home
from .drone_chat import DroneAssistant, generate_mission_plan 