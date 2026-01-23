#!/usr/bin/env python3
"""
Test script for Webots UDP controller.
Sends control commands to the Webots C-based drone controller.

Usage:
    python tools/test_webots_udp.py              # Interactive test with menu
    python tools/test_webots_udp.py --demo       # Run automated demo sequence
    python tools/test_webots_udp.py --stats      # Show statistics only
"""

import sys
import time
import argparse
from pathlib import Path

# Add repo root to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from drone.webots_udp_control import WebotsUDPController


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_status(controller: WebotsUDPController):
    """Print current controller status."""
    stats = controller.get_stats()
    status = controller.get_status()

    print("\n📊 Controller Status:")
    print(f"   Connected: {stats['connected']}")
    print(f"   Running: {stats['running']}")
    print(f"   Update Rate: {stats['update_rate_hz']} Hz")
    print(f"   Packets Sent: {stats['packets_sent']}")
    print(f"   Packets Failed: {stats['packets_failed']}")

    if stats["time_since_last_send"] is not None:
        print(f"   Last Send: {stats['time_since_last_send']:.3f}s ago")

    print(f"\n🎮 Current Control Values:")
    roll, pitch, yaw, throttle = stats["current_control"]
    print(f"   Roll:     {roll:+.3f}")
    print(f"   Pitch:    {pitch:+.3f}")
    print(f"   Yaw:      {yaw:+.3f}")
    print(f"   Throttle: {throttle:+.3f}")

    print(f"\n🚁 Simulated Drone State:")
    print(f"   Mode: {status['mode']}")
    print(f"   Armed: {status['armed']}")
    print(f"   Altitude: {status['altitude']:.1f}m")


def run_demo_sequence(controller: WebotsUDPController):
    """Run an automated demo sequence."""
    print_header("Running Automated Demo Sequence")

    sequences = [
        (
            "Neutral position",
            {"roll": 0.0, "pitch": 0.0, "yaw": 0.0, "throttle": 0.0},
            2,
        ),
        ("Hover throttle", {"throttle": 0.6}, 3),
        ("Roll left", {"roll": -1.0, "throttle": 0.6}, 2),
        ("Roll right", {"roll": 1.0, "throttle": 0.6}, 2),
        ("Center roll", {"roll": 0.0, "throttle": 0.6}, 2),
        ("Pitch forward", {"pitch": 1.0, "throttle": 0.6}, 2),
        ("Pitch backward", {"pitch": -1.0, "throttle": 0.6}, 2),
        ("Center pitch", {"pitch": 0.0, "throttle": 0.6}, 2),
        ("Yaw left", {"yaw": -1.0, "throttle": 0.6}, 2),
        ("Yaw right", {"yaw": 1.0, "throttle": 0.6}, 2),
        ("Center yaw", {"yaw": 0.0, "throttle": 0.6}, 2),
        ("Descend", {"throttle": 0.3}, 2),
        ("Stop all", {"roll": 0.0, "pitch": 0.0, "yaw": 0.0, "throttle": 0.0}, 1),
    ]

    for i, (description, values, duration) in enumerate(sequences, 1):
        print(f"\n[{i}/{len(sequences)}] {description}...")
        controller.set_control(**values)
        time.sleep(duration)

    print("\n✅ Demo sequence complete!")


def run_interactive_mode(controller: WebotsUDPController):
    """Run interactive control mode."""
    print_header("Interactive Control Mode")

    print("\nCommands:")
    print("  1. Neutral (all zeros)")
    print("  2. Hover (throttle 0.6)")
    print("  3. Takeoff sequence")
    print("  4. Landing sequence")
    print("  5. Roll left")
    print("  6. Roll right")
    print("  7. Pitch forward")
    print("  8. Pitch backward")
    print("  9. Yaw left")
    print("  0. Yaw right")
    print("  c. Custom values")
    print("  s. Show status")
    print("  q. Quit")

    while True:
        try:
            cmd = input("\n> ").strip().lower()

            if cmd == "q":
                break
            elif cmd == "1":
                print("→ Neutral position")
                controller.set_control(0, 0, 0, 0)
            elif cmd == "2":
                print("→ Hover")
                controller.set_control(0, 0, 0, 0.6)
            elif cmd == "3":
                print("→ Takeoff sequence")
                controller.arm_and_takeoff(10)
            elif cmd == "4":
                print("→ Landing sequence")
                controller.land()
            elif cmd == "5":
                print("→ Roll left")
                controller.set_control(-1.0, 0, 0, 0.6)
            elif cmd == "6":
                print("→ Roll right")
                controller.set_control(1.0, 0, 0, 0.6)
            elif cmd == "7":
                print("→ Pitch forward")
                controller.set_control(0, 1.0, 0, 0.6)
            elif cmd == "8":
                print("→ Pitch backward")
                controller.set_control(0, -1.0, 0, 0.6)
            elif cmd == "9":
                print("→ Yaw left")
                controller.set_control(0, 0, -1.0, 0.6)
            elif cmd == "0":
                print("→ Yaw right")
                controller.set_control(0, 0, 1.0, 0.6)
            elif cmd == "c":
                try:
                    print("Enter values (press Enter to keep current):")
                    roll_str = input("  Roll [-2.0 to 2.0]: ").strip()
                    pitch_str = input("  Pitch [-2.0 to 2.0]: ").strip()
                    yaw_str = input("  Yaw [-2.0 to 2.0]: ").strip()
                    throttle_str = input("  Throttle [-1.0 to 1.0]: ").strip()

                    roll = float(roll_str) if roll_str else 0.0
                    pitch = float(pitch_str) if pitch_str else 0.0
                    yaw = float(yaw_str) if yaw_str else 0.0
                    throttle = float(throttle_str) if throttle_str else 0.0

                    controller.set_control(roll, pitch, yaw, throttle)
                    print("→ Custom values set")
                except ValueError:
                    print("❌ Invalid input")
            elif cmd == "s":
                print_status(controller)
            else:
                print("❌ Unknown command")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test Webots UDP controller")
    parser.add_argument(
        "--demo", action="store_true", help="Run automated demo sequence"
    )
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    parser.add_argument(
        "--host", default="127.0.0.1", help="UDP host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=9000, help="UDP port (default: 9000)"
    )
    parser.add_argument(
        "--rate", type=int, default=30, help="Update rate in Hz (default: 30)"
    )
    args = parser.parse_args()

    # Create controller
    print_header("Webots UDP Controller Test")
    print(f"\n🔧 Configuration:")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Rate: {args.rate} Hz")

    controller = WebotsUDPController(
        host=args.host, port=args.port, update_rate_hz=args.rate
    )

    try:
        # Connect
        print(f"\n🔌 Connecting to Webots simulator...")
        if not controller.connect():
            print("❌ Failed to connect")
            return 1

        print("✅ Connected! UDP packets are being sent continuously.")
        print("   (It's OK if Webots is not running yet - packets will be sent anyway)")

        # Run appropriate mode
        if args.stats:
            time.sleep(2)  # Let some packets send
            print_status(controller)
        elif args.demo:
            run_demo_sequence(controller)
            print_status(controller)
        else:
            run_interactive_mode(controller)

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        print("\n🔌 Disconnecting...")
        controller.disconnect()
        print("✅ Test complete")


if __name__ == "__main__":
    sys.exit(main())
