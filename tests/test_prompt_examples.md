# DeepDrone Test Prompts

This document contains example prompts that can be used to test the DeepDrone agent's ability to understand natural language mission requests, plan missions, and execute them.

## Running the Tests

1. Start the ArduPilot SITL simulator:
   ```bash
   cd ~/ardupilot && ./Tools/autotest/sim_vehicle.py -v ArduCopter --console --map
   ```

2. In a new terminal, run the DeepDrone application:
   ```bash
   cd ~/deepdrone && streamlit run main.py
   ```

3. Use one of the example prompts below in the chat interface to test the agent's capabilities.

## Example Prompts for Testing

### Basic Mission Planning

#### Example 1: Square Pattern Mission
```
Plan and execute a simple square pattern flight around my current position with sides of 50 meters at an altitude of 20 meters.
```

Expected behavior:
- Agent should generate a square-shaped mission plan
- Mission should include 4 waypoints forming a square
- Altitude should be set to 20 meters
- Agent will connect to the simulator and execute the mission

#### Example 2: Survey Mission
```
I need to create a survey mission for a 100x100 meter area. It should take about 15 minutes and cover the area systematically with a camera.
```

Expected behavior:
- Agent should generate a survey mission plan with grid pattern
- Mission plan should specify recommended altitude for survey (40-60 meters)
- Plan should include information about camera settings and overlap
- Agent will offer to execute the mission on the simulator

#### Example 3: Inspection Mission
```
Create an inspection mission for a tower structure. The mission should orbit around a central point at varying distances and capture detailed images.
```

Expected behavior:
- Agent should generate an inspection mission plan with orbital pattern
- Mission should recommend lower altitude (5-20 meters)
- Plan should include waypoints at different heights and distances
- Agent will offer to execute the mission on the simulator

### Specific Execution Instructions

#### Example 4: Delivery Mission with Specific Coordinates
```
Plan a delivery mission to these coordinates: 37.7749, -122.4194. Make sure to maintain at least 30 meters altitude en route and avoid populated areas.
```

Expected behavior:
- Agent should generate a delivery mission plan with the specified coordinates
- Mission should set 30+ meters as the flight altitude
- Plan should mention safety considerations
- Agent will offer to execute the mission on the simulator

#### Example 5: Custom Mission with Multiple Waypoints
```
I need a custom mission with the following waypoints:
1. Take off to 15 meters
2. Fly to 50 meters north of home position
3. Then 50 meters east
4. Then 50 meters south
5. Return to home and land
```

Expected behavior:
- Agent should generate a custom mission plan with the specified waypoints
- Plan should include exact coordinates for each waypoint
- Agent will offer to execute the mission on the simulator

## Troubleshooting

If the agent doesn't respond correctly to any of these prompts, check the following:

1. Make sure the SITL simulator is running properly
2. Verify that you have set the HF_TOKEN environment variable for the Hugging Face API
3. Check that the DroneKit connection to the simulator is working
4. Look for any error messages in the terminal

## Expected Response Format

A typical response from the agent should include:

1. Acknowledgment of the mission request
2. A detailed mission plan including:
   - Mission type
   - Duration
   - Flight pattern
   - Altitude recommendations
   - Waypoint information
3. Options to execute the mission or modify the plan

Example:
```
I'll create a survey mission plan for your 100x100 meter area.

Mission Plan:
- Type: Survey
- Duration: 15 minutes
- Flight pattern: Grid with 70% overlap
- Recommended altitude: 50 meters
- Camera settings: 4K resolution, 1 shot every 2 seconds

The plan includes 12 waypoints in a grid pattern to ensure complete coverage of the area.

Would you like me to execute this mission on the simulator?
``` 