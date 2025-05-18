#!/usr/bin/env python3
"""
Simplified test for the DroneAssistant with proper smolagents format support
"""

import os
import sys
from drone.drone_chat import DroneAssistant, generate_mission_plan
from drone.hf_model import Message

def final_answer(answer):
    """Final answer function for smolagents"""
    print(f"FINAL ANSWER: {answer}")
    return answer

class SimplePlaceholderModel:
    """A very simple placeholder model that always returns a properly formatted response"""
    
    def __call__(self, messages):
        """Called when used as a function"""
        return self.generate(messages)
    
    def generate(self, messages, **kwargs):
        """Generate a response with proper smolagents formatting"""
        mission_type = "survey"
        duration = 15
        
        # Format the response in the way smolagents expects with proper code formatting
        response = f"""Thought: I will create a {mission_type} mission plan for {duration} minutes and execute it on the simulator.
Code:
```py
mission_plan = generate_mission_plan(mission_type="{mission_type}", duration_minutes={duration})
print(f"Generated mission plan: {{mission_plan}}")
final_answer(f"I've created a {mission_type} mission plan that will take approximately {duration} minutes to execute. The plan includes waypoints for a square pattern around your current position.")
```<end_code>"""
        
        return Message(response)

def test_simple_agent():
    """Test the drone assistant with a simple model"""
    print("\n=== Testing Simple Agent ===")
    
    # Create placeholder model
    model = SimplePlaceholderModel()
    
    # Create drone assistant
    assistant = DroneAssistant(
        tools=[generate_mission_plan],
        model=model
    )
    
    # Test a simple mission planning request
    user_message = "Plan a simple square pattern mission around my current position."
    
    print(f"\nUser: {user_message}")
    
    try:
        response = assistant.chat(user_message)
        print(f"\nAgent response: {response}")
        return True
    except Exception as e:
        print(f"\nError: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_agent()
    if success:
        print("\nTest passed!")
        sys.exit(0)
    else:
        print("\nTest failed!")
        sys.exit(1) 