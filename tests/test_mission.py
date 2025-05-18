#!/usr/bin/env python3
"""
DroneKit-Python Mission Test Script

This script demonstrates how to connect to the ArduPilot SITL simulator,
create a simple mission (square pattern), and execute it.
"""

import time
import math
import sys
import argparse
from drone import compatibility_fix  # Import the compatibility fix for Python 3.10+
from drone.drone_control import DroneController
from dronekit import connect, VehicleMode, LocationGlobalRelative

def get_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test mission script for DeepDrone')
    parser.add_argument('--connect', 
                        help="Vehicle connection target string. If not specified, SITL automatically started.",
                        default='udp:127.0.0.1:14550')
    return parser.parse_args()

def main():
    # Parse connection string
    args = get_args()
    connection_string = args.connect
    
    print(f"Connecting to vehicle on: {connection_string}")
    
    try:
        # Connect to the Vehicle
        print("Connecting to vehicle on %s" % connection_string)
        vehicle = connect(connection_string, wait_ready=True, timeout=60)
        
        # Get some vehicle attributes (state)
        print("Get some vehicle attribute values:")
        print(" GPS: %s" % vehicle.gps_0)
        print(" Battery: %s" % vehicle.battery)
        print(" Last Heartbeat: %s" % vehicle.last_heartbeat)
        print(" Is Armable?: %s" % vehicle.is_armable)
        print(" System status: %s" % vehicle.system_status.state)
        print(" Mode: %s" % vehicle.mode.name)
        
        # Define the home position (current position where script is run)
        home_position = vehicle.location.global_relative_frame
        print("Home position: %s" % home_position)
        
        # Define a square mission
        offset = 0.0001  # Approximately 11 meters at the equator
        
        # Create a mission with a square pattern
        print("Creating mission waypoints...")
        waypoints = [
            # North
            LocationGlobalRelative(home_position.lat + offset, home_position.lon, 20),
            # Northeast
            LocationGlobalRelative(home_position.lat + offset, home_position.lon + offset, 20),
            # East
            LocationGlobalRelative(home_position.lat, home_position.lon + offset, 20),
            # Return to Launch
            LocationGlobalRelative(home_position.lat, home_position.lon, 20),
        ]
        
        # Arm the vehicle
        print("Arming motors")
        vehicle.mode = VehicleMode("GUIDED")
        vehicle.armed = True
        
        # Wait until armed
        while not vehicle.armed:
            print("Waiting for arming...")
            time.sleep(1)
        
        print("Taking off to 20 meters")
        vehicle.simple_takeoff(20)  # Take off to 20m
        
        # Wait until the vehicle reaches a safe height
        while True:
            print("Altitude: %s" % vehicle.location.global_relative_frame.alt)
            # Break and return when we reach target altitude or close to it
            if vehicle.location.global_relative_frame.alt >= 19:
                print("Reached target altitude")
                break
            time.sleep(1)
        
        # Fly through the waypoints
        for i, waypoint in enumerate(waypoints):
            print(f"Flying to waypoint {i+1}")
            vehicle.simple_goto(waypoint)
            
            # Start timer for waypoint timeout
            start_time = time.time()
            
            # Wait until we reach the waypoint
            while True:
                # Calculate distance to waypoint
                current = vehicle.location.global_relative_frame
                distance_to_waypoint = math.sqrt(
                    (waypoint.lat - current.lat)**2 + 
                    (waypoint.lon - current.lon)**2) * 1.113195e5
                
                print(f"Distance to waypoint: {distance_to_waypoint:.2f} meters")
                
                # Break if we're within 3 meters of the waypoint
                if distance_to_waypoint < 3:
                    print(f"Reached waypoint {i+1}")
                    break
                
                # Break if we've been flying to this waypoint for more than 60 seconds
                if time.time() - start_time > 60:
                    print(f"Timed out reaching waypoint {i+1}, continuing to next waypoint")
                    break
                
                time.sleep(2)
        
        # Return to home
        print("Returning to home")
        vehicle.mode = VehicleMode("RTL")
        
        # Wait for the vehicle to land
        while vehicle.armed:
            print("Waiting for landing and disarm...")
            time.sleep(2)
        
        print("Mission complete!")
        
        # Close vehicle object
        vehicle.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 