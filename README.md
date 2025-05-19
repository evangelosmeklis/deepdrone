# DeepDrone

A drone chat agent for drone analytics and operations, built on the smolagents framework with DroneKit integration for real drone control.

![DeepDrone Interface](media/att.1mxvX7ixOaRuDewek4Lq6JseIxapLkfUqn9ZLDUTCWk.png)
![DeepDrone Visualization](media/att.pVXoULsfT5UF13gBL3MU8gcmuYMqnwBcizz2dhry8D4.png)

## Hugging Face
This repo is hosted in a huggingface space here: 
I will regularely update it on github with the changes there

https://huggingface.co/spaces/evangelosmeklis/deepdrone

## Features

- **Drone Chat**: Interact with a drone assistant through a chat interface
- **Visualizations**: Generate flight paths and sensor readings visualizations
- **Maintenance Recommendations**: Get maintenance suggestions based on flight hours
- **Mission Planning**: Generate mission plans for various drone operations
- **Real Drone Control**: Connect to and control real drones using DroneKit
  - Take off and land
  - Navigate to GPS coordinates
  - Return to home
  - Execute waypoint missions
  - Monitor battery and location

## Getting Started

1. Clone this repository
2. Copy `.env-example` to `.env` and add your Hugging Face API token
3. Install dependencies: `pip install -r requirements.txt`
4. **For Python 3.10+ users**: Run the compatibility patch: `python dronekit_patch.py`
5. Run the application: `streamlit run main.py`

## Using DroneKit Integration

The DroneKit integration allows you to control drones running ArduPilot or PX4 firmware.

### Python 3.10+ Compatibility

If you're using Python 3.10 or newer, you need to run the patch script before using DroneKit:

```
python dronekit_patch.py
```

This script fixes the "AttributeError: module 'collections' has no attribute 'MutableMapping'" error by patching the DroneKit library to use collections.abc instead of collections.

### Simulation

To test the drone control features in simulation:

1. Install ArduPilot SITL simulator (follow instructions at https://ardupilot.org/dev/docs/setting-up-sitl-on-linux.html)
2. Start a simulated drone: `sim_vehicle.py -v ArduCopter --console --map`
3. Run the example script: `python drone_example.py`

**Note**: The simulator must be running before you attempt to connect with DeepDrone.

### Real Drone Connection

To connect to a real drone:

1. Ensure your drone is running ArduPilot or PX4 firmware
2. Connect using one of these methods:

   #### Via Terminal
   
   ```
   # For direct USB connection
   python drone_example.py --connect /dev/ttyACM0  # Linux
   python drone_example.py --connect COM3  # Windows
   
   # For WiFi/Network connection
   python drone_example.py --connect tcp:192.168.1.1:5760
   
   # For telemetry radio connection
   python drone_example.py --connect /dev/ttyUSB0
   ```

   #### Via Chat Interface
   
   Use natural language commands in the DeepDrone chat:
   
   - "Connect to drone at tcp:192.168.1.1:5760"
   - "Connect to drone using USB at /dev/ttyACM0"
   - "Connect to drone via telemetry at /dev/ttyUSB0"

Once connected, you can control the drone with commands like:
- "Take off to 10 meters"
- "Fly to latitude 37.7749, longitude -122.4194, altitude 30 meters"
- "Return to home"
- "Land now"

### Troubleshooting

- **collections.MutableMapping error**: Run `python dronekit_patch.py` to fix the DroneKit library for Python 3.10+
- **Connection refused error**: Ensure the drone or simulator is powered on and the connection string is correct
- **Import errors**: Verify that DroneKit and PyMAVLink are installed (run `pip install dronekit pymavlink`)
- **Permission errors**: For USB connections on Linux, you may need to add your user to the 'dialout' group or use `sudo`

IMPORTANT: Always follow safety guidelines when operating real drones.

## Tech Stack

- smolagents for agent functionality
- Hugging Face's Qwen2.5-Coder model for natural language understanding
- DroneKit-Python for real drone control
- Streamlit for the user interface
- Pandas, Matplotlib and Seaborn for data analysis and visualization
