"""
Adapter to make WebotsUDPController compatible with DroneController interface.
This allows seamless switching between DroneKit (real drone/SITL) and Webots simulation.
"""

import time
import logging
from typing import Dict, List, Optional
from .webots_udp_control import WebotsUDPController

logger = logging.getLogger('webots_adapter')


class WebotsDroneAdapter:
    """
    Adapter that wraps WebotsUDPController to provide the same interface as DroneController.
    This allows the rest of the application to work with both real drones and Webots simulation.
    """
    
    def __init__(self, connection_string: str = None):
        """
        Initialize the Webots drone adapter.
        
        Args:
            connection_string: Format "udp:host:port" or just "webots" for defaults
                              e.g., "udp:127.0.0.1:9000" or "webots"
        """
        # Parse connection string
        host = "127.0.0.1"
        port = 9000
        
        if connection_string and connection_string != "webots":
            parts = connection_string.replace("udp:", "").split(":")
            if len(parts) >= 1 and parts[0]:
                host = parts[0]
            if len(parts) >= 2:
                try:
                    port = int(parts[1])
                except ValueError:
                    logger.warning(f"Invalid port in connection string: {parts[1]}, using default 9000")
        
        self.controller = WebotsUDPController(host=host, port=port, update_rate_hz=30.0)
        self.connection_string = connection_string or "webots"
        self.connected = False
        
        # Simulated vehicle state for compatibility
        self.vehicle = None
        self._create_mock_vehicle()
    
    def _create_mock_vehicle(self):
        """Create a mock vehicle object with minimal attributes for compatibility."""
        class MockVehicle:
            def __init__(self, adapter):
                self.adapter = adapter
                
            @property
            def mode(self):
                class Mode:
                    def __init__(self, name):
                        self.name = name
                return Mode(self.adapter.controller.simulated_mode)
            
            @mode.setter
            def mode(self, value):
                # Accept VehicleMode objects or strings
                mode_name = value.name if hasattr(value, 'name') else str(value)
                self.adapter.controller.simulated_mode = mode_name
            
            @property
            def armed(self):
                return self.adapter.controller.simulated_armed
            
            @armed.setter
            def armed(self, value):
                self.adapter.controller.simulated_armed = value
            
            @property
            def is_armable(self):
                return self.adapter.connected
            
            @property
            def location(self):
                adapter = self.adapter  # Capture adapter reference
                
                class Frame:
                    def __init__(self, alt=0.0, lat=0.0, lon=0.0):
                        self.alt = alt
                        self.lat = lat
                        self.lon = lon
                
                class Location:
                    def __init__(self, altitude):
                        self._altitude = altitude
                    
                    @property
                    def global_relative_frame(self):
                        return Frame(alt=self._altitude)
                    
                    @property
                    def global_frame(self):
                        return Frame(lat=0.0, lon=0.0, alt=self._altitude)
                
                return Location(adapter.controller.simulated_altitude)
            
            @property
            def battery(self):
                class Battery:
                    voltage = 12.6
                    level = 100.0
                    current = 5.0
                return Battery()
            
            @property
            def airspeed(self):
                return 0.0
            
            @property
            def groundspeed(self):
                return 0.0
            
            @property
            def heading(self):
                return 0
            
            @property
            def system_status(self):
                class Status:
                    state = "ACTIVE" if self.adapter.connected else "STANDBY"
                return Status()
            
            @property
            def gps_0(self):
                class GPS:
                    fix_type = 3  # 3D fix
                    satellites_visible = 10
                    eph = 100
                    epv = 100
                return GPS()
            
            @property
            def home_location(self):
                class Home:
                    lat = 0.0
                    lon = 0.0
                return Home()
            
            def simple_takeoff(self, altitude):
                """Mock simple_takeoff for compatibility."""
                pass
            
            def simple_goto(self, location):
                """Mock simple_goto for compatibility."""
                pass
            
            def close(self):
                """Mock close for compatibility."""
                self.adapter.disconnect()
            
            def flush(self):
                """Mock flush for compatibility."""
                pass
        
        self.vehicle = MockVehicle(self)
    
    def connect_to_drone(self, connection_string: str = None, timeout: int = 10) -> bool:
        """
        Connect to the Webots simulator.
        
        Args:
            connection_string: Optional connection string override
            timeout: Ignored for UDP (kept for compatibility)
            
        Returns:
            bool: True if connection successful
        """
        if connection_string:
            self.connection_string = connection_string
            # Re-parse and create new controller if needed
            self.__init__(connection_string)
        
        logger.info(f"Connecting to Webots simulator via UDP...")
        success = self.controller.connect()
        
        if success:
            self.connected = True
            logger.info("✅ Connected to Webots simulator")
            logger.info(f"📡 UDP packets sending at {self.controller.update_rate_hz} Hz to {self.controller.host}:{self.controller.port}")
        else:
            self.connected = False
            logger.error("❌ Failed to connect to Webots simulator")
        
        return success
    
    def disconnect(self) -> None:
        """Disconnect from the Webots simulator."""
        if self.connected:
            logger.info("Disconnecting from Webots simulator...")
            self.controller.disconnect()
            self.connected = False
            logger.info("✅ Disconnected from Webots simulator")
    
    def arm_and_takeoff(self, target_altitude: float) -> bool:
        """
        Arms the drone and takes off to the specified altitude.
        
        Args:
            target_altitude: Target altitude in meters
            
        Returns:
            bool: True if takeoff successful
        """
        if not self.connected:
            logger.error("Not connected to Webots simulator")
            return False
        
        logger.info(f"🚁 Webots: Arm and takeoff to {target_altitude}m")
        return self.controller.arm_and_takeoff(target_altitude)
    
    def land(self) -> bool:
        """
        Land the drone.
        
        Returns:
            bool: True if land command sent successfully
        """
        if not self.connected:
            logger.error("Not connected to Webots simulator")
            return False
        
        logger.info("🛬 Webots: Landing")
        return self.controller.land()
    
    def return_to_launch(self) -> bool:
        """
        Return to launch location.
        
        Returns:
            bool: True if RTL command sent successfully
        """
        if not self.connected:
            logger.error("Not connected to Webots simulator")
            return False
        
        logger.info("🏠 Webots: Return to launch")
        return self.controller.return_to_launch()
    
    def goto_location(self, latitude: float, longitude: float, altitude: float) -> bool:
        """
        Go to the specified GPS location.
        
        Args:
            latitude: Target latitude in degrees
            longitude: Target longitude in degrees
            altitude: Target altitude in meters
            
        Returns:
            bool: True if goto command sent successfully
        """
        if not self.connected:
            logger.error("Not connected to Webots simulator")
            return False
        
        logger.info(f"🧭 Webots: Goto location ({latitude}, {longitude}) at {altitude}m")
        return self.controller.goto_location(latitude, longitude, altitude)
    
    def get_current_location(self) -> Dict[str, float]:
        """
        Get the current GPS location of the drone.
        
        Returns:
            Dict containing latitude, longitude, and altitude
        """
        if not self.connected:
            return {"error": "Not connected to Webots simulator"}
        
        status = self.controller.get_status()
        return {
            "latitude": status["gps"]["lat"],
            "longitude": status["gps"]["lon"],
            "altitude": status["altitude"]
        }
    
    def get_battery_status(self) -> Dict[str, float]:
        """
        Get the current battery status.
        
        Returns:
            Dict containing battery voltage and remaining percentage
        """
        if not self.connected:
            return {"error": "Not connected to Webots simulator"}
        
        return {
            "voltage": 12.6,
            "level": 100.0,
            "current": 5.0
        }
    
    def get_airspeed(self) -> float:
        """Get the current airspeed."""
        return 0.0
    
    def get_groundspeed(self) -> float:
        """Get the current ground speed."""
        return 0.0
    
    def upload_mission(self, waypoints: List[Dict[str, float]]) -> bool:
        """
        Upload a mission with multiple waypoints.
        Note: Basic implementation - Webots controller needs to handle this.
        
        Args:
            waypoints: List of dictionaries with lat, lon, alt for each waypoint
            
        Returns:
            bool: True if mission upload successful
        """
        if not self.connected:
            logger.error("Not connected to Webots simulator")
            return False
        
        logger.info(f"📝 Webots: Upload mission with {len(waypoints)} waypoints")
        logger.warning("⚠️  Mission upload requires implementation in Webots controller")
        # Store waypoints for later execution
        self._mission_waypoints = waypoints
        return True
    
    def execute_mission(self) -> bool:
        """
        Execute the uploaded mission.
        
        Returns:
            bool: True if mission started successfully
        """
        if not self.connected:
            logger.error("Not connected to Webots simulator")
            return False
        
        logger.info("▶️  Webots: Execute mission")
        logger.warning("⚠️  Mission execution requires implementation in Webots controller")
        return True
    
    def set_airspeed(self, speed: float) -> bool:
        """
        Set the target airspeed.
        
        Args:
            speed: Target airspeed in m/s
            
        Returns:
            bool: True if command sent successfully
        """
        if not self.connected:
            logger.error("Not connected to Webots simulator")
            return False
        
        logger.info(f"💨 Webots: Set airspeed to {speed} m/s")
        # Webots controller would need to implement this
        return True


def create_webots_controller(connection_string: str = "webots") -> WebotsDroneAdapter:
    """
    Factory function to create a Webots drone controller.
    
    Args:
        connection_string: Connection string (e.g., "udp:127.0.0.1:9000" or "webots")
        
    Returns:
        WebotsDroneAdapter instance
    """
    return WebotsDroneAdapter(connection_string)

