"""
Drone tools manager for terminal interface.
Adapts the existing drone control functionality for the terminal application.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from .drone_control import DroneController

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DroneToolsManager:
    """Manages drone operations for the terminal interface."""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.controller = DroneController(connection_string)
        self.connected = False
        self.mission_in_progress = False
        
        # Status tracking
        self.status = "STANDBY"
        self.phase = ""
        self.log_entries = []
    
    def connect_drone(self, connection_string: str, timeout: int = 30) -> bool:
        """Connect to a drone."""
        try:
            self._update_status("CONNECTING", f"Connecting to {connection_string}")
            
            success = self.controller.connect_to_drone(connection_string, timeout)
            if success:
                self.connected = True
                self._update_status("CONNECTED", "Successfully connected to drone")
                
                # Get initial status
                location = self.get_location()
                battery = self.get_battery()
                
                logger.info(f"Connected to drone. Location: {location}, Battery: {battery}")
                return True
            else:
                self._update_status("ERROR", "Failed to connect to drone")
                return False
                
        except Exception as e:
            self._update_status("ERROR", f"Connection error: {str(e)}")
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect_drone(self):
        """Disconnect from the drone."""
        try:
            self._update_status("DISCONNECTING", "Disconnecting from drone")
            self.controller.disconnect()
            self.connected = False
            self.mission_in_progress = False
            self._update_status("STANDBY", "Disconnected from drone")
            logger.info("Disconnected from drone")
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
    
    def takeoff(self, altitude: float) -> bool:
        """Take off to specified altitude."""
        if not self._ensure_connected():
            return False
        
        try:
            self._update_status("TAKING OFF", f"Taking off to {altitude} meters")
            self.mission_in_progress = True
            
            success = self.controller.arm_and_takeoff(altitude)
            if success:
                self._update_status("AIRBORNE", f"Reached altitude of {altitude} meters")
                return True
            else:
                self._update_status("ERROR", "Takeoff failed")
                self.mission_in_progress = False
                return False
                
        except Exception as e:
            self._update_status("ERROR", f"Takeoff error: {str(e)}")
            self.mission_in_progress = False
            logger.error(f"Takeoff error: {e}")
            return False
    
    def land(self) -> bool:
        """Land the drone."""
        if not self._ensure_connected():
            return False
        
        try:
            self._update_status("LANDING", "Landing drone")
            
            success = self.controller.land()
            if success:
                self._update_status("LANDED", "Drone has landed")
                self.mission_in_progress = False
                return True
            else:
                self._update_status("ERROR", "Landing failed")
                return False
                
        except Exception as e:
            self._update_status("ERROR", f"Landing error: {str(e)}")
            logger.error(f"Landing error: {e}")
            return False
    
    def return_home(self) -> bool:
        """Return to launch/home location."""
        if not self._ensure_connected():
            return False
        
        try:
            self._update_status("RETURNING", "Returning to launch point")
            
            success = self.controller.return_to_launch()
            if success:
                self._update_status("RETURNING", "Drone is returning to launch point")
                return True
            else:
                self._update_status("ERROR", "Return to home failed")
                return False
                
        except Exception as e:
            self._update_status("ERROR", f"Return error: {str(e)}")
            logger.error(f"Return error: {e}")
            return False
    
    def fly_to(self, latitude: float, longitude: float, altitude: float) -> bool:
        """Fly to specific GPS coordinates."""
        if not self._ensure_connected():
            return False
        
        try:
            self._update_status(
                "NAVIGATING", 
                f"Flying to lat:{latitude:.4f}, lon:{longitude:.4f}, alt:{altitude}m"
            )
            
            success = self.controller.goto_location(latitude, longitude, altitude)
            if success:
                return True
            else:
                self._update_status("ERROR", "Navigation failed")
                return False
                
        except Exception as e:
            self._update_status("ERROR", f"Navigation error: {str(e)}")
            logger.error(f"Navigation error: {e}")
            return False
    
    def get_location(self) -> Dict[str, Any]:
        """Get current GPS location."""
        if not self._ensure_connected():
            return {"error": "Not connected to drone"}
        
        try:
            return self.controller.get_current_location()
        except Exception as e:
            logger.error(f"Location error: {e}")
            return {"error": str(e)}
    
    def get_battery(self) -> Dict[str, Any]:
        """Get battery status."""
        if not self._ensure_connected():
            return {"error": "Not connected to drone"}
        
        try:
            return self.controller.get_battery_status()
        except Exception as e:
            logger.error(f"Battery error: {e}")
            return {"error": str(e)}
    
    def execute_mission(self, waypoints: List[Dict[str, float]]) -> bool:
        """Execute a mission with multiple waypoints."""
        if not self._ensure_connected():
            return False
        
        if not waypoints:
            logger.error("No waypoints provided")
            return False
        
        try:
            self._update_status("MISSION", f"Starting mission with {len(waypoints)} waypoints")
            self.mission_in_progress = True
            
            # Upload mission
            upload_success = self.controller.upload_mission(waypoints)
            if not upload_success:
                self._update_status("ERROR", "Failed to upload mission")
                self.mission_in_progress = False
                return False
            
            # Execute mission
            execute_success = self.controller.execute_mission()
            if execute_success:
                self._update_status("EXECUTING", "Mission execution started")
                
                # Simulate mission progress updates
                for i, wp in enumerate(waypoints, 1):
                    self._update_status(
                        "EXECUTING",
                        f"Waypoint {i}/{len(waypoints)}: {wp['lat']:.4f}, {wp['lon']:.4f}"
                    )
                    time.sleep(1)  # Brief pause between waypoints
                
                self._update_status("MISSION COMPLETE", "All waypoints reached")
                return True
            else:
                self._update_status("ERROR", "Failed to start mission execution")
                self.mission_in_progress = False
                return False
                
        except Exception as e:
            self._update_status("ERROR", f"Mission error: {str(e)}")
            self.mission_in_progress = False
            logger.error(f"Mission error: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current drone and system status."""
        status_info = {
            "connected": self.connected,
            "mission_in_progress": self.mission_in_progress,
            "status": self.status,
            "phase": self.phase,
            "log_entries": self.log_entries[-5:],  # Last 5 entries
        }
        
        if self.connected:
            try:
                status_info["location"] = self.get_location()
                status_info["battery"] = self.get_battery()
                
                if hasattr(self.controller, 'vehicle') and self.controller.vehicle:
                    status_info["mode"] = str(self.controller.vehicle.mode.name)
                    status_info["armed"] = self.controller.vehicle.armed
                    status_info["system_status"] = str(self.controller.vehicle.system_status.state)
                    
            except Exception as e:
                status_info["telemetry_error"] = str(e)
        
        return status_info
    
    def is_connected(self) -> bool:
        """Check if connected to drone."""
        return self.connected
    
    def emergency_stop(self):
        """Emergency stop - immediately land or RTL."""
        if not self.connected:
            return
        
        try:
            self._update_status("EMERGENCY", "Emergency stop initiated")
            
            # Try RTL first, then land
            if not self.return_home():
                self.land()
                
            self.mission_in_progress = False
            
        except Exception as e:
            logger.error(f"Emergency stop error: {e}")
    
    def set_airspeed(self, speed: float) -> bool:
        """Set target airspeed."""
        if not self._ensure_connected():
            return False
        
        try:
            return self.controller.set_airspeed(speed)
        except Exception as e:
            logger.error(f"Airspeed error: {e}")
            return False
    
    def get_telemetry(self) -> Dict[str, Any]:
        """Get comprehensive telemetry data."""
        if not self._ensure_connected():
            return {"error": "Not connected to drone"}
        
        try:
            telemetry = {}
            
            # Basic info
            telemetry["location"] = self.get_location()
            telemetry["battery"] = self.get_battery()
            
            # Vehicle-specific data if available
            if hasattr(self.controller, 'vehicle') and self.controller.vehicle:
                vehicle = self.controller.vehicle
                
                telemetry.update({
                    "mode": str(vehicle.mode.name),
                    "armed": vehicle.armed,
                    "system_status": str(vehicle.system_status.state),
                    "airspeed": vehicle.airspeed,
                    "groundspeed": vehicle.groundspeed,
                    "heading": vehicle.heading,
                })
                
                # GPS info
                if vehicle.gps_0:
                    telemetry["gps"] = {
                        "fix_type": vehicle.gps_0.fix_type,
                        "satellites_visible": vehicle.gps_0.satellites_visible,
                        "eph": vehicle.gps_0.eph,
                        "epv": vehicle.gps_0.epv,
                    }
            
            return telemetry
            
        except Exception as e:
            logger.error(f"Telemetry error: {e}")
            return {"error": str(e)}
    
    def _ensure_connected(self) -> bool:
        """Ensure drone is connected."""
        if not self.connected:
            logger.error("Not connected to drone")
            return False
        return True
    
    def _update_status(self, status: str, phase: str = ""):
        """Update system status and log entry."""
        self.status = status
        self.phase = phase
        
        # Create log entry
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {status}: {phase}" if phase else f"[{timestamp}] {status}"
        
        self.log_entries.append(log_entry)
        
        # Keep only last 50 entries
        if len(self.log_entries) > 50:
            self.log_entries = self.log_entries[-50:]
        
        logger.info(log_entry)