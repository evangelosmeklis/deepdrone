#!/usr/bin/env python3
"""
DeepDrone entrypoint.
Starts the simulator + web interface or launches CLI mode.
"""

import sys
import time
import signal
import threading
import subprocess
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

SIMULATOR_PATH = current_dir / "tools" / "simulator.py"


def open_browser():
    time.sleep(1.5)
    try:
        import webbrowser

        webbrowser.open("http://localhost:8000")
    except Exception:
        pass


def start_simulator():
    print("🚁 Starting drone simulator...")
    process = subprocess.Popen(
        [sys.executable, str(SIMULATOR_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=current_dir,
        bufsize=1,
        universal_newlines=True,
    )
    print(f"✓ Simulator started (PID: {process.pid})")
    time.sleep(2)
    return process


def cleanup_ports():
    print("🧹 Cleaning up ports...")
    subprocess.run("lsof -ti:8000 | xargs kill -9 2>/dev/null || true", shell=True)
    subprocess.run("lsof -ti:5760 | xargs kill -9 2>/dev/null || true", shell=True)
    subprocess.run("pkill -f simulator.py 2>/dev/null || true", shell=True)
    time.sleep(1)


def run_web_server():
    import uvicorn
    from drone.web_server import app

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


def run_cli():
    from drone.interactive_setup import start_interactive_session

    start_interactive_session()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_cli()
        return

    simulator_process = None

    def signal_handler(sig, frame):
        if simulator_process:
            simulator_process.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 60)
    print("🚁 DeepDrone - Complete Launch")
    print("=" * 60)

    cleanup_ports()

    try:
        simulator_process = start_simulator()
        print("📱 Opening browser at: http://localhost:8000")
        run_web_server()
    finally:
        if simulator_process:
            simulator_process.terminate()
            try:
                simulator_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                simulator_process.kill()


if __name__ == "__main__":
    main()
