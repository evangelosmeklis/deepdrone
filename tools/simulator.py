#!/usr/bin/env python3
"""
Simple Drone Simulator for DeepDrone
Uses dronekit-sitl for reliable MAVLink simulation.
"""

import sys
import time

try:
    from dronekit_sitl import SITL
except ImportError:
    print("❌ dronekit-sitl not installed")
    print("📦 Installing dronekit-sitl...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "dronekit-sitl"])
    from dronekit_sitl import SITL

def main():
    """Start SITL simulator."""
    print("🚁 Starting DroneKit SITL Simulator...")
    print()

    # Start SITL
    sitl = SITL()
    sitl.download('copter', '3.3', verbose=True)

    # Launch with specific parameters
    sitl_args = [
        '--home=-35.363261,149.165230,584,353',
        '--model', 'quad'
    ]

    sitl.launch(sitl_args, verbose=True, await_ready=True, restart=True)

    connection_string = sitl.connection_string()

    print()
    print("="*60)
    print("✅ DroneKit SITL Simulator Running")
    print("="*60)
    print(f"📡 Connection String: {connection_string}")
    print("="*60)
    print()
    print("⚠️  Press Ctrl+C to stop")
    print()

    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping simulator...")
        sitl.stop()
        print("✅ Simulator stopped")

if __name__ == "__main__":
    main()
