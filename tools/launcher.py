#!/usr/bin/env python3
"""
DeepDrone Launcher - Starts simulator and web interface together
"""

import sys
import os
import subprocess
import time
import signal
import webbrowser
import threading
from pathlib import Path

# Add the repo root to Python path for imports
current_dir = Path(__file__).parent
repo_root = current_dir.parent
sys.path.insert(0, str(repo_root))


class DeepDroneLauncher:
    def __init__(self):
        self.simulator_process = None
        self.web_server_process = None

    def open_browser(self):
        """Open browser after a short delay."""
        time.sleep(2)  # Wait for server to start
        webbrowser.open("http://localhost:8000")

    def start_simulator(self):
        """Start the drone simulator in the background."""
        print("🚁 Starting drone simulator...")
        try:
            self.simulator_process = subprocess.Popen(
                [sys.executable, "simulator.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=current_dir,
                bufsize=1,
                universal_newlines=True,
            )
            print("✓ Simulator started (PID: {})".format(self.simulator_process.pid))
            time.sleep(2)  # Give simulator time to initialize
            return True
        except Exception as e:
            print(f"✗ Failed to start simulator: {e}")
            return False

    def start_web_server(self):
        """Start the web server."""
        print("🌐 Starting web server...")
        try:
            import uvicorn
            from drone.web_server import app

            os.chdir(repo_root)

            # Open browser in a separate thread
            browser_thread = threading.Thread(target=self.open_browser, daemon=True)
            browser_thread.start()

            # Start the server (this blocks)
            uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

        except Exception as e:
            print(f"✗ Failed to start web server: {e}")
            import traceback

            traceback.print_exc()
            return False

    def cleanup(self):
        """Clean up processes on exit."""
        print("\n\n🛑 Shutting down...")

        if self.simulator_process:
            print("   Stopping simulator...")
            self.simulator_process.terminate()
            try:
                self.simulator_process.wait(timeout=5)
                print("   ✓ Simulator stopped")
            except subprocess.TimeoutExpired:
                print("   ⚠ Force killing simulator...")
                self.simulator_process.kill()

        print("   ✓ Web server stopped")
        print("\n👋 DeepDrone shutdown complete. Goodbye!\n")

    def cleanup_ports(self):
        """Clean up ports before starting."""
        print("🧹 Cleaning up ports...")
        try:
            # Kill processes on port 8000
            subprocess.run(
                "lsof -ti:8000 | xargs kill -9 2>/dev/null || true", shell=True
            )
            # Kill processes on port 5760
            subprocess.run(
                "lsof -ti:5760 | xargs kill -9 2>/dev/null || true", shell=True
            )
            # Kill any old simulator processes
            subprocess.run("pkill -f simulator.py 2>/dev/null || true", shell=True)
            time.sleep(1)
            print("✓ Ports cleaned")
            print()
        except Exception as e:
            print(f"⚠ Warning: Could not clean ports: {e}")
            print()

    def run(self):
        """Main launcher."""

        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            self.cleanup()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Print banner
        print("=" * 70)
        print("🚁 DeepDrone - Complete Launch")
        print("=" * 70)
        print()
        print("This will start:")
        print("  1. 🛩️  Drone Simulator (background)")
        print("  2. 🌐 Web Interface (http://localhost:8000)")
        print()
        print("=" * 70)
        print()

        # Clean up ports first
        self.cleanup_ports()

        # Start simulator
        if not self.start_simulator():
            print("\n❌ Failed to start simulator. Exiting...")
            sys.exit(1)

        print()
        print("=" * 70)
        print("✓ All systems ready!")
        print("=" * 70)
        print()
        print("📱 Opening browser at: http://localhost:8000")
        print()
        print("💡 Quick Start Guide:")
        print("   1. Select an AI provider (Ollama for local/free)")
        print("   2. Connection string is pre-filled: tcp:127.0.0.1:5760")
        print("   3. Click 'Connect Drone'")
        print("   4. Start chatting with your drone!")
        print()
        print("⚠️  Press Ctrl+C to stop everything")
        print()
        print("=" * 70)
        print()

        # Start web server (this blocks until interrupted)
        try:
            self.start_web_server()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()


def main():
    launcher = DeepDroneLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
