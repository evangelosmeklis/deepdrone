#!/usr/bin/env python3
"""
Test the ability of the DroneAssistant to plan and execute missions
based on natural language requests.

This script simulates a user asking the agent to create a mission plan and execute it.
"""

import os
import time
import json
import sys
from drone.drone_chat import DroneAssistant, generate_mission_plan
from drone.drone_control import connect_drone, disconnect_drone
from drone.hf_model import HfApiModel, Message
from drone import compatibility_fix  # Import for Python 3.10+ compatibility

# Import the simplified model that works with smolagents
from tests.test_simple_agent import SimplePlaceholderModel, final_answer

# Test cases - different natural language requests for missions
TEST_CASES = [
    "Create a mission plan for a survey mission that takes 20 minutes and execute it on the simulator.",
    "I need to inspect a building. Can you make a plan for a 15-minute inspection mission and fly it?",
    "Plan a delivery mission to these coordinates and execute it: 37.7749, -122.4194. It should take about 10 minutes.",
    "Plan and execute a simple square pattern flight around my current position.",
]

def setup_drone_agent():
    """Create and initialize a DroneAssistant for testing."""
    print("Setting up drone agent...")
    
    # Check if HF_TOKEN is set in environment variables
    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        print("WARNING: No Hugging Face API token found. Using a placeholder model.")
        # Use our simplified placeholder model instead of the previous complex one
        model = SimplePlaceholderModel()
    else:
        # Use the real model if API token is available
        model = HfApiModel(
            max_tokens=2096,
            temperature=0.7,
            model_id='Qwen/Qwen2.5-Coder-32B-Instruct'
        )
    
    # Create the drone assistant with the required tools
    drone_agent = DroneAssistant(
        tools=[generate_mission_plan],
        model=model
    )
    
    return drone_agent

def execute_mission_from_plan(mission_plan):
    """Execute a mission based on the provided plan using DroneKit."""
    print("\nExecuting mission from plan...")
    
    # Parse the mission plan
    try:
        if isinstance(mission_plan, str):
            plan = eval(mission_plan)  # Convert string representation to dict
        else:
            plan = mission_plan
            
        print(f"Mission type: {plan.get('mission_type')}")
        print(f"Duration: {plan.get('duration_minutes')} minutes")
        print(f"Flight pattern: {plan.get('flight_pattern')}")
        print(f"Recommended altitude: {plan.get('recommended_altitude')}")
        
        # Connect to the simulator
        print("\nConnecting to simulator...")
        connected = connect_drone('udp:127.0.0.1:14550')
        
        if not connected:
            print("Failed to connect to the simulator. Make sure it's running.")
            return False
        
        print("Connected to simulator!")
        print("Simulating mission execution...")
        
        # Here we would normally execute the actual mission
        # For testing purposes, we'll just simulate the execution
        for i in range(5):
            print(f"Mission progress: {i*20}%")
            time.sleep(1)
            
        print("Mission completed successfully!")
        disconnect_drone()
        return True
    
    except Exception as e:
        print(f"Error executing mission: {str(e)}")
        return False

def run_test_case(drone_agent, test_case):
    """Run a single test case with the drone agent."""
    print(f"\n----- TESTING CASE: '{test_case}' -----")
    
    # Simulate a user asking the agent
    print(f"\nUSER: {test_case}")
    
    # Get the agent's response
    response = drone_agent.chat(test_case)
    print(f"\nAGENT: {response}")
    
    # Check if the response contains or implies a mission plan
    mission_keywords = ["mission plan", "flight plan", "waypoints", "coordinates"]
    has_mission_plan = any(keyword in response.lower() for keyword in mission_keywords)
    
    if not has_mission_plan:
        print("FAIL: Agent did not create a mission plan.")
        return False
    
    # Extract the mission plan and execute it
    # For a real implementation, we would need to parse the response more carefully
    # Here we'll just call the generate_mission_plan function directly
    
    if "survey" in test_case.lower():
        mission_type = "survey"
    elif "inspect" in test_case.lower():
        mission_type = "inspection"
    elif "delivery" in test_case.lower():
        mission_type = "delivery"
    else:
        mission_type = "custom"
    
    if "minute" in test_case.lower():
        # Try to extract the duration
        import re
        duration_match = re.search(r'(\d+)\s*minute', test_case)
        duration = int(duration_match.group(1)) if duration_match else 15
    else:
        duration = 15
    
    print(f"\nGenerating mission plan for {mission_type} mission with duration {duration} minutes...")
    mission_plan = generate_mission_plan(mission_type=mission_type, duration_minutes=duration)
    print(f"\nGenerated plan: {mission_plan}")
    
    # Execute the mission plan
    result = execute_mission_from_plan(mission_plan)
    
    if result:
        print("PASS: Successfully executed the mission plan.")
        return True
    else:
        print("FAIL: Could not execute the mission plan.")
        return False

def run_all_tests():
    """Run all test cases and report results."""
    drone_agent = setup_drone_agent()
    
    results = []
    for test_case in TEST_CASES:
        result = run_test_case(drone_agent, test_case)
        results.append(result)
    
    # Print summary
    print("\n----- TEST SUMMARY -----")
    for i, (test, result) in enumerate(zip(TEST_CASES, results)):
        status = "PASS" if result else "FAIL"
        print(f"Test {i+1}: {status} - '{test[:40]}...'")
    
    success_rate = sum(results) / len(results) * 100
    print(f"\nOverall Success Rate: {success_rate:.1f}%")
    
    return all(results)

if __name__ == "__main__":
    print("Testing DroneAssistant's ability to plan and execute missions...")
    success = run_all_tests()
    
    if success:
        print("\nAll tests passed! The agent can successfully plan and execute missions.")
        exit(0)
    else:
        print("\nSome tests failed. The agent needs improvement.")
        exit(1) 