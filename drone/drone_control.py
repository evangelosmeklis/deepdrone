"""
DroneKit-Python interface for DeepDrone - Real Drone Control Module
This module provides functions for controlling real drones using DroneKit-Python.
"""

import time
import math
# Import compatibility fix for collections.MutableMapping
from . import compatibility_fix
from dronekit import connect, VehicleMode, LocationGlobalRelative, Command
from pymavlink import mavutil
from typing import Dict, List, Optional, Tuple, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('drone_control')

class DroneController:
    """Class to handle real drone control operations using DroneKit."""
    
    def __init__(self, connection_string: str = None):
        """
        Initialize the drone controller.
        
        Args:
            connection_string: Connection string for the drone (e.g., 'udp:127.0.0.1:14550' for SITL,
                              '/dev/ttyACM0' for serial, or 'tcp:192.168.1.1:5760' for remote connection)
        """
        self.vehicle = None
        self.connection_string = connection_string
        self.connected = False
    
    def connect_to_drone(self, connection_string: str = None, timeout: int = 30) -> bool:
        """
        Connect to the drone using DroneKit.
        
        Args:
            connection_string: Connection string for the drone (overrides the one provided in __init__)
            timeout: Connection timeout in seconds
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        if connection_string:
            self.connection_string = connection_string
            
        if not self.connection_string:
            logger.error("No connection string provided")
            return False
            
        try:
            logger.info(f"Connecting to drone on {self.connection_string}...")
            # Connect without wait_ready to avoid iteration issues
            self.vehicle = connect(self.connection_string, wait_ready=False, timeout=timeout)
            
            # Wait for basic attributes to be available
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Try to access basic vehicle info safely
                    if hasattr(self.vehicle, 'version') and self.vehicle.version:
                        break
                except:
                    pass
                time.sleep(0.1)
            
            self.connected = True
            logger.info("Connected to drone successfully")
            
            # Log basic vehicle info safely
            try:
                if hasattr(self.vehicle, 'version'):
                    logger.info(f"Vehicle Version: {self.vehicle.version}")
                if hasattr(self.vehicle, 'system_status') and hasattr(self.vehicle.system_status, 'state'):
                    logger.info(f"Vehicle Status: {self.vehicle.system_status.state}")
            except Exception as e:
                logger.warning(f"Could not read vehicle info: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to drone: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the drone."""
        if self.vehicle and self.connected:
            logger.info("Disconnecting from drone...")
            self.vehicle.close()
            self.connected = False
            logger.info("Disconnected from drone")
    
    def arm_and_takeoff(self, target_altitude: float) -> bool:
        """
        Arms the drone and takes off to the specified altitude.
        
        Args:
            target_altitude: Target altitude in meters
            
        Returns:
            bool: True if takeoff successful, False otherwise
        """
        if not self._ensure_connected():
            return False
            
        logger.info("Arming motors...")
        # Switch to GUIDED mode
        self.vehicle.mode = VehicleMode("GUIDED")
        
        # Wait until mode change is verified
        timeout = 10  # seconds
        start = time.time()
        while self.vehicle.mode.name != "GUIDED":
            if time.time() - start > timeout:
                logger.error("Failed to enter GUIDED mode")
                return False
            time.sleep(0.5)
        
        # Arm the drone
        self.vehicle.armed = True
        
        # Wait for arming
        timeout = 10  # seconds
        start = time.time()
        while not self.vehicle.armed:
            if time.time() - start > timeout:
                logger.error("Failed to arm")
                return False
            time.sleep(0.5)
        
        logger.info("Taking off!")
        # Take off to target altitude
        self.vehicle.simple_takeoff(target_altitude)
        
        # Wait until target altitude reached
        while True:
            current_altitude = self.vehicle.location.global_relative_frame.alt
            logger.info(f"Altitude: {current_altitude}")
            
            # Break and return when we're close enough to target altitude
            if current_altitude >= target_altitude * 0.95:
                logger.info("Reached target altitude")
                break
            time.sleep(1)
        
        return True
    
    def land(self) -> bool:
        """
        Land the drone.
        
        Returns:
            bool: True if land command sent successfully, False otherwise
        """
        if not self._ensure_connected():
            return False
            
        logger.info("Landing...")
        self.vehicle.mode = VehicleMode("LAND")
        return True
    
    def return_to_launch(self) -> bool:
        """
        Return to launch location.
        
        Returns:
            bool: True if RTL command sent successfully, False otherwise
        """
        if not self._ensure_connected():
            return False
            
        logger.info("Returning to launch location...")
        self.vehicle.mode = VehicleMode("RTL")
        return True
    
    def goto_location(self, latitude: float, longitude: float, altitude: float) -> bool:
        """
        Go to the specified GPS location.
        
        Args:
            latitude: Target latitude in degrees
            longitude: Target longitude in degrees
            altitude: Target altitude in meters (relative to home position)
            
        Returns:
            bool: True if goto command sent successfully, False otherwise
        """
        if not self._ensure_connected():
            return False
            
        logger.info(f"Going to location: Lat: {latitude}, Lon: {longitude}, Alt: {altitude}")
        
        # Make sure vehicle is in GUIDED mode
        if self.vehicle.mode.name != "GUIDED":
            self.vehicle.mode = VehicleMode("GUIDED")
            # Wait for mode change
            timeout = 5
            start = time.time()
            while self.vehicle.mode.name != "GUIDED":
                if time.time() - start > timeout:
                    logger.error("Failed to enter GUIDED mode")
                    return False
                time.sleep(0.5)
        
        # Create LocationGlobalRelative object and send command
        target_location = LocationGlobalRelative(latitude, longitude, altitude)
        self.vehicle.simple_goto(target_location)
        
        logger.info(f"Going to location: Lat: {latitude}, Lon: {longitude}, Alt: {altitude}")
        return True
    
    def get_current_location(self) -> Dict[str, float]:
        """
        Get the current GPS location of the drone.
        
        Returns:
            Dict containing latitude, longitude, and altitude
        """
        if not self._ensure_connected():
            return {"error": "Not connected to drone"}
            
        location = self.vehicle.location.global_relative_frame
        return {
            "latitude": location.lat,
            "longitude": location.lon, 
            "altitude": location.alt
        }
    
    def get_battery_status(self) -> Dict[str, float]:
        """
        Get the current battery status.
        
        Returns:
            Dict containing battery voltage and remaining percentage
        """
        if not self._ensure_connected():
            return {"error": "Not connected to drone"}
            
        return {
            "voltage": self.vehicle.battery.voltage,
            "level": self.vehicle.battery.level,
            "current": self.vehicle.battery.current
        }
        
    def get_airspeed(self) -> float:
        """
        Get the current airspeed.
        
        Returns:
            Current airspeed in m/s
        """
        if not self._ensure_connected():
            return -1.0
            
        return self.vehicle.airspeed
        
    def get_groundspeed(self) -> float:
        """
        Get the current ground speed.
        
        Returns:
            Current ground speed in m/s
        """
        if not self._ensure_connected():
            return -1.0
            
        return self.vehicle.groundspeed
    
    def upload_mission(self, waypoints: List[Dict[str, float]]) -> bool:
        """
        Upload a mission with multiple waypoints to the drone.
        
        Args:
            waypoints: List of dictionaries with lat, lon, alt for each waypoint
            
        Returns:
            bool: True if mission upload successful, False otherwise
        """
        if not self._ensure_connected():
            return False
            
        logger.info(f"Uploading mission with {len(waypoints)} waypoints...")
        
        # Create list of commands
        cmds = self.vehicle.commands
        cmds.clear()
        
        # Add home location as first waypoint
        cmds.add(Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, 
                         mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, 
                         self.vehicle.home_location.lat, 
                         self.vehicle.home_location.lon, 
                         0))
        
        # Add mission waypoints
        for idx, wp in enumerate(waypoints):
            # Add delay at waypoint (0 = no delay)
            delay = wp.get("delay", 0)
            
            # Add waypoint command
            cmds.add(Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, 
                             mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, delay, 0, 0, 0, 
                             wp["lat"], wp["lon"], wp["alt"]))
        
        # Upload the commands to the vehicle
        cmds.upload()
        logger.info("Mission uploaded successfully")
        return True
    
    def execute_mission(self) -> bool:
        """
        Execute the uploaded mission.
        
        Returns:
            bool: True if mission started successfully, False otherwise
        """
        if not self._ensure_connected():
            return False
            
        logger.info("Executing mission...")
        self.vehicle.mode = VehicleMode("AUTO")
        
        # Wait for mode change
        timeout = 5
        start = time.time()
        while self.vehicle.mode.name != "AUTO":
            if time.time() - start > timeout:
                logger.error("Failed to enter AUTO mode")
                return False
            time.sleep(0.5)
        
        logger.info("Mission execution started")
        return True
    
    def set_airspeed(self, speed: float) -> bool:
        """
        Set the target airspeed.
        
        Args:
            speed: Target airspeed in m/s
            
        Returns:
            bool: True if command sent successfully, False otherwise
        """
        if not self._ensure_connected():
            return False
            
        logger.info(f"Setting airspeed to {speed} m/s")
        self.vehicle.airspeed = speed
        return True
    
    def _ensure_connected(self) -> bool:
        """
        Ensure drone is connected before executing a command.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.vehicle or not self.connected:
            logger.error("Not connected to a drone. Call connect_to_drone() first.")
            return False
        return True


# Convenience functions for using the controller without creating an instance

_controller = None

def connect_drone(connection_string: str, timeout: int = 30) -> bool:
    """
    Connect to a drone using the specified connection string.
    
    Args:
        connection_string: Connection string for the drone
        timeout: Connection timeout in seconds
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    global _controller
    if _controller is None:
        _controller = DroneController()
    
    return _controller.connect_to_drone(connection_string, timeout)

def disconnect_drone() -> None:
    """Disconnect from the drone."""
    global _controller
    if _controller:
        _controller.disconnect()

def takeoff(altitude: float) -> bool:
    """
    Arm and take off to the specified altitude.
    
    Args:
        altitude: Target altitude in meters
        
    Returns:
        bool: True if takeoff successful, False otherwise
    """
    global _controller
    if _controller:
        return _controller.arm_and_takeoff(altitude)
    return False

def land() -> bool:
    """
    Land the drone.
    
    Returns:
        bool: True if land command sent successfully, False otherwise
    """
    global _controller
    if _controller:
        return _controller.land()
    return False

def return_home() -> bool:
    """
    Return to launch/home location.
    
    Returns:
        bool: True if RTL command sent successfully, False otherwise
    """
    global _controller
    if _controller:
        return _controller.return_to_launch()
    return False

def fly_to(lat: float, lon: float, alt: float) -> bool:
    """
    Go to the specified GPS location.
    
    Args:
        lat: Target latitude in degrees
        lon: Target longitude in degrees
        alt: Target altitude in meters (relative to home position)
        
    Returns:
        bool: True if goto command sent successfully, False otherwise
    """
    global _controller
    if _controller:
        return _controller.goto_location(lat, lon, alt)
    return False

def get_location() -> Dict[str, float]:
    """
    Get the current GPS location of the drone.
    
    Returns:
        Dict containing latitude, longitude, and altitude
    """
    global _controller
    if _controller:
        return _controller.get_current_location()
    return {"error": "Not connected to drone"}

def get_battery() -> Dict[str, float]:
    """
    Get the current battery status.
    
    Returns:
        Dict containing battery voltage and remaining percentage
    """
    global _controller
    if _controller:
        return _controller.get_battery_status()
    return {"error": "Not connected to drone"}

def execute_mission_plan(waypoints: List[Dict[str, float]]) -> bool:
    """
    Upload and execute a mission with multiple waypoints.
    
    Args:
        waypoints: List of dictionaries with lat, lon, alt for each waypoint
        
    Returns:
        bool: True if mission started successfully, False otherwise
    """
    global _controller
    if _controller:
        if _controller.upload_mission(waypoints):
            return _controller.execute_mission()
    return False 