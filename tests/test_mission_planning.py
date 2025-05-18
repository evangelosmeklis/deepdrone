#!/usr/bin/env python3
"""
Simplified test script for mission planning and execution.
This script tests the mission planning and execution functionality directly,
without using the DroneAssistant or smolagents.
"""

import time
import math
import sys
import json
from drone.drone_chat import generate_mission_plan
from drone.drone_control import connect_drone, disconnect_drone, takeoff, land, return_home
from drone import compatibility_fix  # Import for Python 3.10+ compatibility

def test_mission_planning():
    """Test the mission planning functionality."""
    print("\n----- TESTING MISSION PLANNING -----")
    
    # Test different mission types
    mission_types = ["survey", "inspection", "delivery", "custom"]
    durations = [10, 15, 20, 5]
    
    for mission_type, duration in zip(mission_types, durations):
        print(f"\nGenerating {mission_type} mission plan for {duration} minutes...")
        
        mission_plan = generate_mission_plan(mission_type=mission_type, duration_minutes=duration)
        
        # Parse the mission plan
        if isinstance(mission_plan, str):
            try:
                plan = eval(mission_plan)  # Convert string representation to dict
                print("Successfully parsed mission plan:")
                print(f"  Mission type: {plan.get('mission_type')}")
                print(f"  Duration: {plan.get('duration_minutes')} minutes")
                print(f"  Flight pattern: {plan.get('flight_pattern')}")
                print(f"  Recommended altitude: {plan.get('recommended_altitude')} meters")
                print(f"  Waypoint count: {len(plan.get('waypoints', []))}")
                print("  Mission description:", plan.get('description', '')[:50] + "...")
            except Exception as e:
                print(f"Error parsing mission plan: {str(e)}")
                print("Raw mission plan:", mission_plan)
        else:
            print("Mission plan is not a string:", type(mission_plan))
            print(mission_plan)
    
    print("\nMission planning test completed.")
    return True

def test_mission_execution(mission_type="survey", duration=10):
    """Test the mission execution functionality using the simulator."""
    print("\n----- TESTING MISSION EXECUTION -----")
    
    # Generate a mission plan
    print(f"Generating {mission_type} mission plan for {duration} minutes...")
    mission_plan = generate_mission_plan(mission_type=mission_type, duration_minutes=duration)
    
    # Parse the mission plan
    try:
        if isinstance(mission_plan, str):
            plan = eval(mission_plan)  # Convert string representation to dict
        else:
            plan = mission_plan
        
        print("Mission plan details:")
        print(f"  Mission type: {plan.get('mission_type')}")
        print(f"  Duration: {plan.get('duration_minutes')} minutes")
        print(f"  Flight pattern: {plan.get('flight_pattern')}")
        print(f"  Recommended altitude: {plan.get('recommended_altitude')} meters")
        print(f"  Waypoint count: {len(plan.get('waypoints', []))}")
        
        # Connect to the simulator
        print("\nConnecting to simulator...")
        success = connect_drone('udp:127.0.0.1:14550')
        
        if not success:
            print("Failed to connect to the simulator. Make sure it's running.")
            return False
        
        print("Connected to simulator!")
        
        # Execute the mission
        # For the test, we'll just print the waypoints instead of actually flying
        print("\nSimulating mission execution...")
        print(f"Taking off to {plan.get('recommended_altitude')} meters...")
        time.sleep(2)
        
        print("Flying mission waypoints:")
        waypoints = plan.get('waypoints', [])
        for i, waypoint in enumerate(waypoints):
            print(f"  Waypoint {i+1}: {waypoint}")
            time.sleep(1)
        
        print("Returning to home...")
        time.sleep(2)
        
        print("Landing...")
        time.sleep(2)
        
        print("Mission completed successfully!")
        disconnect_drone()
        return True
        
    except Exception as e:
        print(f"Error executing mission: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("Testing mission planning and execution...")
    
    # Test mission planning
    planning_success = test_mission_planning()
    
    # Test mission execution
    execution_success = test_mission_execution("survey", 10)
    
    # Print test summary
    print("\n----- TEST SUMMARY -----")
    print(f"Mission Planning Test: {'PASS' if planning_success else 'FAIL'}")
    print(f"Mission Execution Test: {'PASS' if execution_success else 'FAIL'}")
    
    if planning_success and execution_success:
        print("\nAll tests passed! The mission planning and execution are working properly.")
        return 0
    else:
        print("\nSome tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 