"""
Function calling tools for LLM to execute drone commands.
"""

import json
import math
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from .drone_control import DroneController

# Define function schemas for LLMs
FUNCTION_SCHEMAS = [
    {
        "name": "arm_and_takeoff",
        "description": "Arm the drone and take off to a specified altitude. The drone must be connected first.",
        "parameters": {
            "type": "object",
            "properties": {
                "altitude": {
                    "type": "number",
                    "description": "Target altitude in meters (e.g., 20 for 20 meters)",
                }
            },
            "required": ["altitude"],
        },
    },
    {
        "name": "land",
        "description": "Land the drone at its current location.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "return_to_launch",
        "description": "Return the drone to its launch/home location and land.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "goto_location",
        "description": "Fly the drone to a specific GPS coordinate at a given altitude.",
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {
                    "type": "number",
                    "description": "Target latitude in decimal degrees",
                },
                "longitude": {
                    "type": "number",
                    "description": "Target longitude in decimal degrees",
                },
                "altitude": {
                    "type": "number",
                    "description": "Target altitude in meters",
                },
            },
            "required": ["latitude", "longitude", "altitude"],
        },
    },
    {
        "name": "get_status",
        "description": "Get the current status of the drone including mode, armed state, altitude, battery, and GPS location.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "set_airspeed",
        "description": "Set the target airspeed of the drone.",
        "parameters": {
            "type": "object",
            "properties": {
                "speed": {"type": "number", "description": "Target airspeed in m/s"}
            },
            "required": ["speed"],
        },
    },
]


@dataclass
class SafetyLimits:
    max_altitude: float = 60.0
    min_altitude: float = 1.0
    max_speed: float = 15.0
    max_distance_m: float = 500.0


class FunctionExecutor:
    """Executes function calls from LLM on the drone."""

    def __init__(self, drone_controller: Optional[DroneController] = None):
        self.drone_controller = drone_controller
        self.safety_limits = SafetyLimits()

    def validate_waypoints(self, waypoints: List[Dict[str, float]]) -> Optional[str]:
        for waypoint in waypoints:
            altitude = waypoint.get("alt")
            if altitude is None:
                return "Waypoint missing altitude"
            altitude_error = self._validate_altitude(altitude)
            if altitude_error:
                return altitude_error

            lat = waypoint.get("lat")
            lon = waypoint.get("lon")
            if lat is None or lon is None:
                return "Waypoint missing latitude or longitude"
            distance_error = self._validate_distance(lat, lon)
            if distance_error:
                return distance_error

        return None

    def _haversine_distance_m(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        radius = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius * c

    def _get_reference_location(self) -> Optional[Dict[str, float]]:
        if not self.drone_controller:
            return None

        try:
            location = self.drone_controller.get_current_location()
            if not location or "error" in location:
                return None
            return location
        except Exception:
            return None

    def _validate_altitude(self, altitude: float) -> Optional[str]:
        if altitude < self.safety_limits.min_altitude:
            return f"Altitude must be at least {self.safety_limits.min_altitude}m"
        if altitude > self.safety_limits.max_altitude:
            return f"Altitude exceeds max of {self.safety_limits.max_altitude}m"
        return None

    def _validate_distance(self, latitude: float, longitude: float) -> Optional[str]:
        reference = self._get_reference_location()
        if not reference:
            return None

        distance = self._haversine_distance_m(
            reference["latitude"], reference["longitude"], latitude, longitude
        )
        if distance > self.safety_limits.max_distance_m:
            return f"Target location is {distance:.0f}m away, exceeds max radius of {self.safety_limits.max_distance_m}m"
        return None

    def _validate_speed(self, speed: float) -> Optional[str]:
        if speed <= 0:
            return "Speed must be greater than 0"
        if speed > self.safety_limits.max_speed:
            return f"Speed exceeds max of {self.safety_limits.max_speed} m/s"
        return None

    def _validate_safety(
        self, function_name: str, arguments: Dict[str, Any]
    ) -> Optional[str]:
        if function_name == "arm_and_takeoff":
            altitude = arguments.get("altitude")
            if altitude is None:
                return "Missing altitude parameter"
            return self._validate_altitude(altitude)

        if function_name == "goto_location":
            altitude = arguments.get("altitude")
            if altitude is None:
                return "Missing altitude parameter"
            altitude_error = self._validate_altitude(altitude)
            if altitude_error:
                return altitude_error

            latitude = arguments.get("latitude")
            longitude = arguments.get("longitude")
            if latitude is None or longitude is None:
                return "Missing latitude or longitude parameter"
            return self._validate_distance(latitude, longitude)

        if function_name == "set_airspeed":
            speed = arguments.get("speed")
            if speed is None:
                return "Missing speed parameter"
            return self._validate_speed(speed)

        return None

    def execute_function(
        self, function_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a function call and return the result."""

        if not self.drone_controller:
            return {
                "success": False,
                "error": "Drone not connected. Please connect to the drone first.",
            }

        # Check if drone is actually connected (handles both DroneKit and Webots)
        if (
            hasattr(self.drone_controller, "connected")
            and not self.drone_controller.connected
        ):
            return {
                "success": False,
                "error": "Drone not connected. Please connect to the drone first.",
            }

        safety_error = self._validate_safety(function_name, arguments)
        if safety_error:
            return {"success": False, "error": safety_error}

        try:
            if function_name == "arm_and_takeoff":
                altitude = arguments.get("altitude")
                if not altitude:
                    return {"success": False, "error": "Missing altitude parameter"}

                success = self.drone_controller.arm_and_takeoff(altitude)

                return {
                    "success": success,
                    "message": f"Successfully took off to {altitude}m! The drone is now airborne."
                    if success
                    else "Takeoff failed. The drone may need more time for GPS lock or system initialization.",
                }

            elif function_name == "land":
                success = self.drone_controller.land()
                return {
                    "success": success,
                    "message": "Landing initiated" if success else "Landing failed",
                }

            elif function_name == "return_to_launch":
                success = self.drone_controller.return_to_launch()
                return {
                    "success": success,
                    "message": "Returning to launch point"
                    if success
                    else "Return to launch failed",
                }

            elif function_name == "goto_location":
                lat = arguments.get("latitude")
                lon = arguments.get("longitude")
                alt = arguments.get("altitude")

                if lat is None or lon is None or alt is None:
                    return {"success": False, "error": "Missing location parameters"}

                success = self.drone_controller.goto_location(lat, lon, alt)
                return {
                    "success": success,
                    "message": f"Flying to ({lat}, {lon}) at {alt}m"
                    if success
                    else "Navigation failed",
                }

            elif function_name == "get_status":
                if not self.drone_controller.vehicle:
                    return {"success": False, "error": "Vehicle not available"}

                vehicle = self.drone_controller.vehicle
                status = {
                    "success": True,
                    "mode": str(vehicle.mode.name),
                    "armed": vehicle.armed,
                    "altitude": vehicle.location.global_relative_frame.alt
                    if vehicle.location
                    else None,
                    "battery": vehicle.battery.level if vehicle.battery else None,
                    "gps": {
                        "lat": vehicle.location.global_frame.lat
                        if vehicle.location
                        else None,
                        "lon": vehicle.location.global_frame.lon
                        if vehicle.location
                        else None,
                    },
                }
                return status

            elif function_name == "set_airspeed":
                speed = arguments.get("speed")
                if not speed:
                    return {"success": False, "error": "Missing speed parameter"}

                success = self.drone_controller.set_airspeed(speed)
                return {
                    "success": success,
                    "message": f"Airspeed set to {speed} m/s"
                    if success
                    else "Failed to set airspeed",
                }

            else:
                return {"success": False, "error": f"Unknown function: {function_name}"}

        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing {function_name}: {str(e)}",
            }


def format_function_schemas_for_ollama(schemas: List[Dict]) -> str:
    """Format function schemas as a string for Ollama (which doesn't support native function calling)."""
    functions_desc = "You have access to the following drone control functions:\n\n"

    for func in schemas:
        functions_desc += f"**{func['name']}**\n"
        functions_desc += f"Description: {func['description']}\n"

        if func["parameters"]["properties"]:
            functions_desc += "Parameters:\n"
            for param_name, param_info in func["parameters"]["properties"].items():
                required = (
                    " (required)"
                    if param_name in func["parameters"].get("required", [])
                    else ""
                )
                functions_desc += f"  - {param_name}: {param_info.get('description', 'No description')}{required}\n"
        else:
            functions_desc += "Parameters: None\n"

        functions_desc += "\n"

    functions_desc += """To execute a function, you MUST respond EXACTLY in this format:
EXECUTE_FUNCTION: function_name
ARGUMENTS: {"param1": value1, "param2": value2}

CRITICAL: Use the exact format above. Do NOT add extra text before or after. Do NOT explain what you're doing - just execute the function.

Example:
User: "Take off to 20 meters"
Your response:
EXECUTE_FUNCTION: arm_and_takeoff
ARGUMENTS: {"altitude": 20}

After executing the function, I will provide you with the result, and THEN you should explain it to the user in natural language.
"""

    return functions_desc
