"""
Webots UDP Drone Controller
Sends control commands via UDP to a C-based Webots drone simulator.
Completely separate from DroneKit/MAVLink - uses only UDP.
"""

import socket
import time
import threading
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('webots_udp')


@dataclass
class ControlValues:
    """Control values for the drone."""
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    throttle: float = 0.0
    
    def clamp(self):
        """Clamp values to safe ranges."""
        self.roll = max(-2.0, min(2.0, self.roll))
        self.pitch = max(-2.0, min(2.0, self.pitch))
        self.yaw = max(-2.0, min(2.0, self.yaw))
        self.throttle = max(-1.0, min(1.0, self.throttle))
    
    def to_packet(self) -> str:
        """Convert to UDP packet format: 'roll pitch yaw throttle'"""
        return f"{self.roll:.6f} {self.pitch:.6f} {self.yaw:.6f} {self.throttle:.6f}"


class WebotsUDPController:
    """
    UDP-based controller for Webots drone simulator.
    Sends control packets continuously at a fixed rate (default 30 Hz).
    """
    
    def __init__(self, 
                 host: str = "127.0.0.1", 
                 port: int = 9000,
                 update_rate_hz: float = 30.0):
        """
        Initialize the Webots UDP controller.
        
        Args:
            host: UDP destination host (default: 127.0.0.1)
            port: UDP destination port (default: 9000)
            update_rate_hz: Control update rate in Hz (default: 30 Hz, range: 20-50)
        """
        self.host = host
        self.port = port
        self.update_rate_hz = max(20.0, min(50.0, update_rate_hz))  # Clamp between 20-50 Hz
        self.update_interval = 1.0 / self.update_rate_hz
        
        # Control state
        self.control_values = ControlValues()
        self._lock = threading.Lock()
        
        # UDP socket
        self.socket: Optional[socket.socket] = None
        
        # Control loop state
        self.running = False
        self.control_thread: Optional[threading.Thread] = None
        self.connected = False
        
        # Statistics
        self.packets_sent = 0
        self.packets_failed = 0
        self.last_send_time = 0.0
        
        # Simulated drone state (for status queries)
        self.simulated_altitude = 0.0
        self.simulated_armed = False
        self.simulated_mode = "STABILIZE"
        
    def connect(self) -> bool:
        """
        Initialize UDP socket and start the control loop.
        
        Returns:
            bool: True if connection successful
        """
        try:
            logger.info(f"Initializing UDP controller for {self.host}:{self.port}")
            
            # Create non-blocking UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setblocking(False)
            
            # Set socket options
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            
            # Test send initial packet
            test_packet = self.control_values.to_packet()
            try:
                self.socket.sendto(test_packet.encode('ascii'), (self.host, self.port))
                logger.info(f"✅ Test packet sent successfully to {self.host}:{self.port}")
            except Exception as e:
                logger.warning(f"⚠️  Test packet failed (this is OK if Webots not running): {e}")
            
            # Start control loop
            self.running = True
            self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
            self.control_thread.start()
            
            self.connected = True
            logger.info(f"✅ UDP controller started at {self.update_rate_hz} Hz")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize UDP controller: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Stop the control loop and close the socket."""
        logger.info("Disconnecting UDP controller...")
        self.running = False
        
        # Wait for control thread to stop
        if self.control_thread and self.control_thread.is_alive():
            self.control_thread.join(timeout=2.0)
        
        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.warning(f"Error closing socket: {e}")
            self.socket = None
        
        self.connected = False
        logger.info(f"✅ Disconnected. Stats: {self.packets_sent} sent, {self.packets_failed} failed")
    
    def set_control(self, roll: float = 0.0, pitch: float = 0.0, 
                    yaw: float = 0.0, throttle: float = 0.0):
        """
        Set control values (thread-safe).
        Values are automatically clamped to safe ranges.
        
        Args:
            roll: Roll angle command [-2.0, 2.0]
            pitch: Pitch angle command [-2.0, 2.0]
            yaw: Yaw rate command [-2.0, 2.0]
            throttle: Throttle command [-1.0, 1.0]
        """
        with self._lock:
            self.control_values.roll = roll
            self.control_values.pitch = pitch
            self.control_values.yaw = yaw
            self.control_values.throttle = throttle
            self.control_values.clamp()
    
    def get_control(self) -> Tuple[float, float, float, float]:
        """Get current control values (thread-safe)."""
        with self._lock:
            return (self.control_values.roll, 
                   self.control_values.pitch,
                   self.control_values.yaw,
                   self.control_values.throttle)
    
    def _control_loop(self):
        """
        Main control loop - runs in a separate thread.
        Sends UDP packets at the configured rate.
        """
        logger.info("Control loop started")
        
        while self.running:
            loop_start = time.time()
            
            try:
                # Get current control values
                with self._lock:
                    packet = self.control_values.to_packet()
                
                # Send UDP packet
                self._send_packet(packet)
                
                # Update last send time
                self.last_send_time = time.time()
                
                # Sleep to maintain update rate
                elapsed = time.time() - loop_start
                sleep_time = self.update_interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
                elif sleep_time < -0.01:  # More than 10ms behind
                    logger.warning(f"Control loop running slow: {elapsed*1000:.1f}ms (target: {self.update_interval*1000:.1f}ms)")
                    
            except Exception as e:
                logger.error(f"Error in control loop: {e}")
                time.sleep(0.1)  # Prevent tight loop on error
        
        logger.info("Control loop stopped")
    
    def _send_packet(self, packet: str):
        """
        Send a UDP packet (non-blocking).
        
        Args:
            packet: ASCII string to send
        """
        if not self.socket:
            self.packets_failed += 1
            return
        
        try:
            self.socket.sendto(packet.encode('ascii'), (self.host, self.port))
            self.packets_sent += 1
            
            # Log periodically (every 100 packets)
            if self.packets_sent % 100 == 0:
                logger.debug(f"📡 Sent {self.packets_sent} packets (rate: {self.update_rate_hz} Hz)")
                
        except BlockingIOError:
            # Socket buffer full - this is OK for non-blocking socket
            pass
        except Exception as e:
            self.packets_failed += 1
            if self.packets_failed % 50 == 0:  # Log every 50 failures
                logger.warning(f"⚠️  Packet send failed (total: {self.packets_failed}): {e}")
    
    def get_stats(self) -> Dict:
        """Get controller statistics."""
        return {
            "connected": self.connected,
            "running": self.running,
            "update_rate_hz": self.update_rate_hz,
            "packets_sent": self.packets_sent,
            "packets_failed": self.packets_failed,
            "time_since_last_send": time.time() - self.last_send_time if self.last_send_time > 0 else None,
            "current_control": self.get_control()
        }
    
    # High-level control commands for compatibility with existing code
    
    def arm_and_takeoff(self, target_altitude: float) -> bool:
        """
        Simplified takeoff for Webots.
        Gradually increases throttle to achieve takeoff, then stops at target.
        
        Args:
            target_altitude: Target altitude in meters
            
        Returns:
            bool: True if command accepted
        """
        if not self.connected:
            logger.error("Cannot takeoff: not connected")
            return False
        
        logger.info(f"🚁 Taking off to {target_altitude}m...")
        self.simulated_mode = "GUIDED"
        self.simulated_armed = True
        
        # Ramp up throttle smoothly
        for throttle in [0.2, 0.4, 0.6, 0.7]:
            self.set_control(throttle=throttle)
            time.sleep(0.5)
        
        # Climb at 0.6 m/s for calculated time
        climb_speed = 0.6  # m/s
        climb_time = target_altitude / climb_speed
        self.set_control(throttle=climb_speed)
        time.sleep(climb_time)
        
        # Stop climbing - set throttle to 0 (maintain altitude)
        self.set_control(throttle=0.0)
        self.simulated_altitude = target_altitude
        
        logger.info(f"✅ Takeoff complete - now hovering at {target_altitude}m (throttle=0)")
        return True
    
    def land(self) -> bool:
        """
        Land the drone by gradually reducing throttle.
        
        Returns:
            bool: True if command accepted
        """
        if not self.connected:
            logger.error("Cannot land: not connected")
            return False
        
        logger.info("🛬 Landing...")
        self.simulated_mode = "LAND"
        
        # Gradually descend
        # Use negative throttle to descend at controlled rate
        descent_speed = -0.3  # Descend at 0.3 m/s
        descent_time = max(self.simulated_altitude / 0.3, 5.0)  # At least 5 seconds
        
        self.set_control(throttle=descent_speed)
        time.sleep(descent_time)
        
        # Final descent
        self.set_control(throttle=-0.1)
        time.sleep(2)
        
        # Stop all movement
        self.set_control(roll=0.0, pitch=0.0, yaw=0.0, throttle=0.0)
        self.simulated_altitude = 0.0
        self.simulated_armed = False
        
        logger.info("✅ Landing complete")
        return True
    
    def goto_location(self, latitude: float, longitude: float, altitude: float) -> bool:
        """
        Simplified navigation command.
        Note: Webots controller needs to implement GPS-based navigation.
        
        Args:
            latitude: Target latitude
            longitude: Target longitude
            altitude: Target altitude in meters
            
        Returns:
            bool: True if command accepted
        """
        if not self.connected:
            logger.error("Cannot navigate: not connected")
            return False
        
        logger.info(f"🧭 Going to: lat={latitude:.6f}, lon={longitude:.6f}, alt={altitude}m")
        logger.warning("⚠️  GPS navigation requires implementation in Webots controller")
        
        # Adjust altitude if different
        altitude_diff = altitude - self.simulated_altitude
        if abs(altitude_diff) > 0.5:
            throttle = 0.5 if altitude_diff > 0 else -0.3
            climb_time = abs(altitude_diff) / abs(throttle)
            self.set_control(throttle=throttle)
            time.sleep(climb_time)
            self.set_control(throttle=0.0)
            self.simulated_altitude = altitude
        
        return True
    
    def hover(self) -> bool:
        """
        Maintain current altitude (stop all movement).
        
        Returns:
            bool: True if command accepted
        """
        if not self.connected:
            logger.error("Cannot hover: not connected")
            return False
        
        logger.info("🛸 Hovering (maintaining altitude)")
        self.set_control(roll=0.0, pitch=0.0, yaw=0.0, throttle=0.0)
        return True
    
    def return_to_launch(self) -> bool:
        """Return to launch (simplified - just land at current position)."""
        if not self.connected:
            return False
        
        logger.info("🏠 Returning to launch (landing at current position)...")
        self.simulated_mode = "RTL"
        
        # For now, just land at current position
        # Real RTL would navigate back to launch point first
        return self.land()
    
    def get_status(self) -> Dict:
        """Get simulated drone status."""
        return {
            "connected": self.connected,
            "mode": self.simulated_mode,
            "armed": self.simulated_armed,
            "altitude": self.simulated_altitude,
            "battery": 100.0,  # Simulated
            "gps": {
                "lat": 0.0,  # Simulated
                "lon": 0.0   # Simulated
            },
            "control": {
                "roll": self.control_values.roll,
                "pitch": self.control_values.pitch,
                "yaw": self.control_values.yaw,
                "throttle": self.control_values.throttle
            }
        }


# Example usage
if __name__ == "__main__":
    # Test the UDP controller
    controller = WebotsUDPController(host="127.0.0.1", port=9000, update_rate_hz=30.0)
    
    try:
        # Connect
        if controller.connect():
            print("✅ Connected to Webots simulator")
            
            # Test sequence
            print("Testing control sequence...")
            
            # Hover
            print("Setting hover throttle...")
            controller.set_control(throttle=0.6)
            time.sleep(2)
            
            # Roll left
            print("Rolling left...")
            controller.set_control(roll=-1.0, throttle=0.6)
            time.sleep(2)
            
            # Roll right
            print("Rolling right...")
            controller.set_control(roll=1.0, throttle=0.6)
            time.sleep(2)
            
            # Return to neutral
            print("Returning to neutral...")
            controller.set_control(roll=0.0, throttle=0.6)
            time.sleep(2)
            
            # Print stats
            stats = controller.get_stats()
            print(f"\n📊 Stats: {stats}")
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    finally:
        controller.disconnect()
        print("✅ Test complete")

