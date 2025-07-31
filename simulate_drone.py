#!/usr/bin/env python3
"""
Drone SITL (Software In The Loop) Simulator
Starts a virtual drone for testing DeepDrone commands.
"""

import subprocess
import sys
import time
import socket
import threading
from pathlib import Path

def check_mavproxy_installed():
    """Check if MAVProxy is installed."""
    try:
        result = subprocess.run(['mavproxy.py', '--help'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def check_ardupilot_installed():
    """Check if ArduPilot SITL is available."""
    try:
        result = subprocess.run(['sim_vehicle.py', '--help'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def find_available_port(start_port=14550):
    """Find an available UDP port starting from start_port."""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def start_simple_sitl(port=14550):
    """Start a simple SITL simulation using ArduPilot."""
    print(f"🚁 Starting ArduPilot SITL on port {port}...")
    
    try:
        # Try to start ArduPilot SITL
        cmd = [
            'sim_vehicle.py',
            '-v', 'ArduCopter',
            '--out', f'udp:127.0.0.1:{port}',
            '--map',
            '--console'
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return process, port
        
    except FileNotFoundError:
        print("❌ ArduPilot SITL not found. Please install ArduPilot.")
        return None, None

def start_mavproxy_sitl(port=14550):
    """Start SITL using MAVProxy."""
    print(f"🚁 Starting MAVProxy SITL on port {port}...")
    
    try:
        cmd = [
            'mavproxy.py',
            '--master', 'tcp:127.0.0.1:5760',
            '--out', f'udp:127.0.0.1:{port}',
            '--aircraft', 'test'
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return process, port
        
    except FileNotFoundError:
        print("❌ MAVProxy not found.")
        return None, None

def create_basic_simulator(port=14550):
    """Create a very basic drone simulator for testing."""
    print(f"🚁 Starting basic drone simulator on port {port}...")
    print("⚠️  This is a minimal simulator for testing purposes only.")
    
    # Create a simple UDP server that responds to basic MAVLink messages
    import socket
    import struct
    
    def simulator_thread():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('127.0.0.1', port))
        sock.settimeout(1.0)
        
        print(f"✅ Basic simulator listening on 127.0.0.1:{port}")
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                # Echo back a simple response
                sock.sendto(data, addr)
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                break
        
        sock.close()
    
    thread = threading.Thread(target=simulator_thread, daemon=True)
    thread.start()
    
    return thread, port

def print_connection_info(port):
    """Print connection information."""
    connection_string = f"udp:127.0.0.1:{port}"
    
    print("\n" + "="*60)
    print("🚁 DRONE SIMULATOR STARTED")
    print("="*60)
    print(f"📡 Connection String: {connection_string}")
    print(f"🌐 IP Address: 127.0.0.1")
    print(f"🔌 Port: {port}")
    print("="*60)
    print("\n💡 To connect DeepDrone:")
    print(f"   1. Run: python main.py")
    print(f"   2. Choose your AI provider")
    print(f"   3. In chat, say: 'Connect to {connection_string}'")
    print("\n🎯 Example commands once connected:")
    print("   • 'Take off to 30 meters'")
    print("   • 'Fly in a square pattern'")
    print("   • 'Show battery status'")
    print("   • 'Return home and land'")
    print("\n⚠️  Press Ctrl+C to stop the simulator")
    print("="*60)

def main():
    """Main function to start the drone simulator."""
    print("🚁 DeepDrone Simulator Starting...")
    print("Checking for available drone simulation software...\n")
    
    # Find available port
    port = find_available_port()
    if not port:
        print("❌ No available ports found. Please check your network configuration.")
        return
    
    simulator_process = None
    simulator_thread = None
    
    try:
        # Try ArduPilot SITL first
        if check_ardupilot_installed():
            print("✅ ArduPilot SITL found. Starting professional simulation...")
            simulator_process, port = start_simple_sitl(port)
            
            if simulator_process:
                print_connection_info(port)
                simulator_process.wait()
            
        elif check_mavproxy_installed():
            print("✅ MAVProxy found. Starting MAVProxy simulation...")
            simulator_process, port = start_mavproxy_sitl(port)
            
            if simulator_process:
                print_connection_info(port)
                simulator_process.wait()
        
        else:
            print("⚠️  No professional drone simulation software found.")
            print("Installing ArduPilot SITL is recommended for full simulation.")
            print("Falling back to basic simulator for testing...")
            
            simulator_thread, port = create_basic_simulator(port)
            print_connection_info(port)
            
            # Keep the basic simulator running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping drone simulator...")
    
    finally:
        if simulator_process:
            simulator_process.terminate()
            try:
                simulator_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                simulator_process.kill()
        
        print("✅ Drone simulator stopped.")

def install_instructions():
    """Print installation instructions for drone simulation software."""
    print("\n📋 To install professional drone simulation:")
    print("\n🔧 ArduPilot SITL (Recommended):")
    print("   git clone https://github.com/ArduPilot/ardupilot.git")
    print("   cd ardupilot")
    print("   git submodule update --init --recursive")
    print("   ./Tools/environment_install/install-prereqs-ubuntu.sh -y")
    print("   . ~/.profile")
    print("   ./waf configure --board sitl")
    print("   ./waf copter")
    print("   echo 'export PATH=$PATH:$HOME/ardupilot/Tools/autotest' >> ~/.bashrc")
    print("   source ~/.bashrc")
    
    print("\n🔧 MAVProxy (Alternative):")
    print("   pip install MAVProxy")
    
    print("\n💡 For now, you can use the basic simulator for testing.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install-help":
        install_instructions()
    else:
        main()