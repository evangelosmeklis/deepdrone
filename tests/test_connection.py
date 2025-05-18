#!/usr/bin/env python3
"""
Basic connection test for DroneKit to ArduPilot SITL
"""

import time
import sys
from dronekit import connect, APIException

# Connect to the Vehicle using a different port to avoid conflicts
print("Connecting to vehicle on udp:127.0.0.1:14550...")
try:
    vehicle = connect('udp:127.0.0.1:14550', wait_ready=True, timeout=60)
except APIException as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

# Get some vehicle attributes (state)
print("Connection successful!")
print("Get some vehicle attribute values:")
print(f" GPS: {vehicle.gps_0}")
print(f" Battery: {vehicle.battery}")
print(f" Last Heartbeat: {vehicle.last_heartbeat}")
print(f" Is Armable?: {vehicle.is_armable}")
print(f" System status: {vehicle.system_status.state}")
print(f" Mode: {vehicle.mode.name}")

# Close vehicle object
vehicle.close()
print("Test complete.") 