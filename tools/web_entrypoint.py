#!/usr/bin/env python3
"""
DeepDrone Web Application - AI-Powered Drone Control System

A browser-based application for controlling drones using various AI models
including OpenAI, Anthropic, Google, and local Ollama models.
"""

import sys
import os
import webbrowser
import time
import threading
from pathlib import Path

# Add the repo root to Python path for imports
current_dir = Path(__file__).parent
repo_root = current_dir.parent
sys.path.insert(0, str(repo_root))


def open_browser():
    """Open browser after a short delay."""
    time.sleep(1.5)  # Wait for server to start
    webbrowser.open("http://localhost:8000")


def main():
    """Main entry point for the DeepDrone web application."""
    try:
        # Load environment variables if .env file exists
        env_file = repo_root / ".env"
        if env_file.exists():
            from dotenv import load_dotenv

            load_dotenv(env_file)

        # Check for CLI mode flag
        if len(sys.argv) > 1 and sys.argv[1] == "--cli":
            # Run the old terminal-based interface
            from drone.interactive_setup import start_interactive_session

            start_interactive_session()
        else:
            # Start web server
            import uvicorn
            from drone.web_server import app

            os.chdir(repo_root)

            print("=" * 60)
            print("🚁 DeepDrone - AI-Powered Drone Control")
            print("=" * 60)
            print("\n📡 Starting web server...")
            print("🌐 Opening browser at: http://localhost:8000")
            print("\n💡 Tips:")
            print("   - Configure your AI provider in the left sidebar")
            print("   - Connect to a drone (or simulator) before sending commands")
            print("   - Use natural language to control your drone")
            print("\n⚠️  Press Ctrl+C to stop the server\n")
            print("=" * 60 + "\n")

            # Open browser in a separate thread
            browser_thread = threading.Thread(target=open_browser, daemon=True)
            browser_thread.start()

            # Start the server
            uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

    except KeyboardInterrupt:
        print("\n\n🚁 DeepDrone server stopped. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting DeepDrone: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
