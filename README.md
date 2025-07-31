# 🚁 DeepDrone - AI-Powered Drone Control Terminal

A powerful terminal-based application for controlling drones using various AI models including OpenAI, Anthropic, Hugging Face, and local Ollama models. Built with DroneKit integration for real drone control.

## ✨ Features

### 🤖 Multi-Model AI Support
- **OpenAI**: GPT-3.5, GPT-4, and other OpenAI models
- **Anthropic**: Claude 3 models
- **Ollama**: Local models (Llama 3.1, Codestral, etc.)
- **Hugging Face**: Any model available through their API
- **LiteLLM**: Unified interface for all providers

### 🚁 Drone Control & Operations
- **Real Drone Control**: Connect to and control real drones using DroneKit
- **Flight Operations**: Take off, land, navigate to GPS coordinates
- **Mission Planning**: Execute complex waypoint missions
- **Safety Features**: Return to home, emergency stop
- **Telemetry**: Monitor battery, location, and flight status

### 💻 Terminal Interface
- **Rich CLI**: Beautiful command-line interface with colors and formatting
- **Interactive Chat**: Natural language conversation with AI models
- **Model Management**: Easy switching between different AI models
- **Configuration**: Persistent settings and API key management

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd deepdrone
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the interactive session**
   ```bash
   python main.py
   ```

### Interactive Setup

When you run `python main.py`, DeepDrone will guide you through:

1. **🔮 Provider Selection** - Choose from OpenAI, Anthropic, Google, Meta, Mistral, or Ollama
2. **🤖 Model Selection** - Pick from popular models or enter your own
3. **🔑 API Key Entry** - Securely enter your API credentials (Ollama skips this)
4. **✅ Connection Test** - Verify everything works
5. **🚁 Simulator Setup** - Instructions for drone connection
6. **💬 Chat Interface** - Start controlling your drone with natural language

### Command Line Usage (Advanced)

For advanced users who prefer command-line options:

```bash
# List available models
python main.py models list

# Add API keys for cloud models
python main.py models set-key gpt-3.5-turbo

# Start a specific chat session
python main.py chat -m gpt-3.5-turbo

# Check Ollama models (for local AI)
python main.py ollama check

# View configuration
python main.py config
```

## 🛠️ Configuration

### Setting Up AI Models

#### OpenAI Models
```bash
# Add your OpenAI API key
python main.py models set-key gpt-3.5-turbo
# Get API key from: https://platform.openai.com/api-keys
```

#### Anthropic Models
```bash
# Add your Anthropic API key
python main.py models set-key claude-3-sonnet
# Get API key from: https://console.anthropic.com/
```

#### Local Ollama Models
```bash
# First install and run Ollama: https://ollama.ai
ollama pull llama3.1
ollama pull codestral

# Check available models
python main.py ollama check
```

### Drone Connection

#### Using the Built-in Simulator

**🎯 Quick Start:**
1. Open a new terminal and run:
   ```bash
   python simulate_drone.py
   ```
2. The simulator will display a connection string like `udp:127.0.0.1:14550`
3. In DeepDrone chat, use that connection string to connect

#### Real Drone Connections

For real drones:
- **Serial**: `/dev/ttyACM0` (Linux) or `COM3` (Windows)
- **TCP**: `tcp:192.168.1.100:5760`
- **UDP**: `udp:127.0.0.1:14550`

#### Professional Simulation

For advanced simulation, install ArduPilot SITL:
```bash
# Get installation help
python simulate_drone.py --install-help
```

## 🎯 Usage Examples

### Basic Chat
```bash
# Start chat with GPT-3.5
python main.py chat -m gpt-3.5-turbo

# Start chat with local Ollama model
python main.py chat -m llama3.1
```

### Interactive Chat Session

Once in the chat interface, you can control your drone with natural language:

```
╭─────────────── DeepDrone Control Center ───────────────╮
│ 🚁 DEEPDRONE CHAT INTERFACE                           │
│                                                        │
│ AI Model: claude-3-5-sonnet (anthropic)               │
│ Drone Connection: udp:127.0.0.1:14550                 │
│ Status: Ready for commands                             │
╰────────────────────────────────────────────────────────╯

🚁 DeepDrone> Connect to the drone simulator and take off to 30 meters

🤖 DeepDrone AI: I'll connect to the simulator and take off to 30 meters...
[Executes Python code to control drone]
✅ Connected and airborne at 30 meters!

🚁 DeepDrone> Fly in a square pattern with 50 meter sides

🤖 DeepDrone AI: I'll create a square flight pattern...
[Plans and executes waypoint mission]
✅ Square pattern completed!

🚁 DeepDrone> Return home and land

🤖 DeepDrone AI: Returning to launch point and landing safely...
✅ Mission complete, drone landed safely!
```

### Model Management
```bash
# Add a custom model
python main.py models add my-gpt4 openai gpt-4 --max-tokens 4096

# Remove a model
python main.py models remove my-gpt4

# View configuration
python main.py config
```

## 🛡️ DroneKit Integration

### Python 3.10+ Compatibility

If you're using Python 3.10 or newer, run the patch script:

```bash
python drone/dronekit_patch.py
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

## Last updated: Mon May 19 17:50:00 EEST 2025
