#!/usr/bin/env python3
"""
DeepDrone Terminal Application - AI-Powered Drone Control System

A terminal-based application for controlling drones using various AI models
including OpenAI, Anthropic, Hugging Face, and local Ollama models.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Main entry point for the DeepDrone terminal application."""
    try:
        # Load environment variables if .env file exists
        env_file = current_dir / ".env"
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
        
        # If no arguments provided, start interactive mode
        if len(sys.argv) == 1:
            from drone.interactive_setup import start_interactive_session
            start_interactive_session()
        else:
            # Run the Typer CLI application for other commands
            from drone.cli import app
            app()
        
    except KeyboardInterrupt:
        print("\n🚁 DeepDrone session interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting DeepDrone: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 