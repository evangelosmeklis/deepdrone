#!/usr/bin/env python3
"""
DeepDrone Web Server - Browser-based Chat Interface
FastAPI server with WebSocket support for real-time drone control.
"""

import os
import json
import asyncio
import subprocess
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from drone.config import ModelConfig
from drone.llm_interface import LLMInterface
from drone.drone_control import DroneController
from drone.webots_drone_adapter import WebotsDroneAdapter
from drone.function_tools import (
    FunctionExecutor,
    format_function_schemas_for_ollama,
    FUNCTION_SCHEMAS,
)

# Load environment variables
load_dotenv()

app = FastAPI(title="DeepDrone", description="AI-Powered Drone Control System")

# Global state
drone_controller: Optional[DroneController] = None
llm_interface: Optional[LLMInterface] = None
current_config: Optional[ModelConfig] = None
current_mission: List[Dict[str, float]] = []

# Session logging
SESSION_LOG_DIR = Path("logs")
SESSION_LOG_DIR.mkdir(exist_ok=True)
session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
SESSION_LOG_PATH = SESSION_LOG_DIR / f"session_{session_id}.jsonl"

TELEMETRY_PUSH_INTERVAL = 1.0
TELEMETRY_LOG_INTERVAL = 5.0


# Pydantic models for API
class ConfigRequest(BaseModel):
    provider: str  # "openai", "anthropic", "google", "ollama"
    api_key: Optional[str] = None
    model: str


class DroneConnectionRequest(BaseModel):
    connection_string: str  # e.g., "udp:127.0.0.1:14550"


class ChatMessage(BaseModel):
    message: str


class Waypoint(BaseModel):
    lat: float
    lon: float
    alt: float
    delay: Optional[float] = 0


class MissionRequest(BaseModel):
    waypoints: List[Waypoint]


def log_event(event_type: str, payload: Dict):
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": event_type,
        "payload": payload,
    }
    try:
        with SESSION_LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")
    except Exception as e:
        print(f"⚠️  Failed to write session log: {e}")


def build_telemetry_payload() -> Dict[str, object]:
    if not drone_controller or not drone_controller.connected:
        return {"connected": False}

    try:
        vehicle = drone_controller.vehicle
        if not vehicle:
            return {"connected": False, "error": "Vehicle not initialized"}

        return {
            "connected": True,
            "mode": str(vehicle.mode.name)
            if hasattr(vehicle.mode, "name")
            else str(vehicle.mode),
            "armed": vehicle.armed,
            "battery": vehicle.battery.level
            if hasattr(vehicle, "battery") and vehicle.battery
            else None,
            "altitude": vehicle.location.global_relative_frame.alt
            if hasattr(vehicle, "location") and vehicle.location
            else None,
            "gps": {
                "lat": vehicle.location.global_frame.lat
                if hasattr(vehicle, "location") and vehicle.location
                else None,
                "lon": vehicle.location.global_frame.lon
                if hasattr(vehicle, "location") and vehicle.location
                else None,
            },
        }
    except Exception as e:
        print(f"❌ Error building telemetry: {e}")
        return {"connected": False, "error": str(e)}


def list_sessions() -> List[Dict[str, object]]:
    sessions = []
    for path in sorted(SESSION_LOG_DIR.glob("session_*.jsonl"), reverse=True):
        try:
            stat = path.stat()
            sessions.append(
                {
                    "id": path.stem.replace("session_", ""),
                    "filename": path.name,
                    "updated_at": datetime.utcfromtimestamp(stat.st_mtime).isoformat()
                    + "Z",
                    "size": stat.st_size,
                }
            )
        except Exception:
            continue
    return sessions


def load_session_events(path: Path) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []
    if not path.exists():
        return events

    try:
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"⚠️  Failed reading session log: {e}")

    return events


@app.get("/")
async def read_root():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "drone_connected": drone_controller is not None and drone_controller.connected
        if drone_controller
        else False,
        "llm_configured": llm_interface is not None,
    }


@app.get("/api/ollama/models")
async def get_ollama_models():
    """Get list of locally installed Ollama models."""
    try:
        # Run ollama list command
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            return {"models": [], "error": "Ollama not installed or not running"}

        # Parse the output
        lines = result.stdout.strip().split("\n")
        if len(lines) <= 1:
            return {"models": []}

        # Skip header line and parse model names
        models = []
        for line in lines[1:]:
            parts = line.split()
            if parts:
                model_name = parts[0]
                models.append(model_name)

        return {"models": models}

    except subprocess.TimeoutExpired:
        return {"models": [], "error": "Ollama command timed out"}
    except FileNotFoundError:
        return {"models": [], "error": "Ollama not installed"}
    except Exception as e:
        return {"models": [], "error": str(e)}


@app.post("/api/config")
async def configure_ai(config: ConfigRequest):
    """Configure AI provider and model."""
    global llm_interface, current_config

    try:
        # Create model config with required fields
        model_config = ModelConfig(
            name=f"{config.provider}-{config.model.split('/')[-1]}",
            provider=config.provider,
            model_id=config.model,
            api_key=config.api_key or os.getenv(f"{config.provider.upper()}_API_KEY"),
            base_url="http://localhost:11434" if config.provider == "ollama" else None,
        )

        # Initialize LLM interface
        llm_interface = LLMInterface(model_config)
        current_config = model_config

        return {
            "status": "success",
            "message": f"Configured {config.provider} with model {config.model}",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/drone/connect")
async def connect_drone(request: DroneConnectionRequest):
    """Connect to drone (DroneKit or Webots)."""
    global drone_controller

    try:
        connection_string = request.connection_string.lower()
        print(f"🔌 Attempting to connect to drone at: {request.connection_string}")

        # Detect connection type: Webots UDP or DroneKit
        is_webots = (
            connection_string == "webots"
            or connection_string.startswith("udp:")
            and ":9000" in connection_string
            or "webots" in connection_string
        )

        if is_webots:
            print("🎮 Using Webots UDP controller")
            drone_controller = WebotsDroneAdapter(request.connection_string)
        else:
            print("🚁 Using DroneKit controller (MAVLink)")
            drone_controller = DroneController(request.connection_string)

        success = drone_controller.connect_to_drone()

        if success:
            controller_type = "Webots simulator" if is_webots else "drone"
            print(f"✅ Successfully connected to {controller_type}")
            return {
                "status": "success",
                "message": f"Connected to {controller_type} at {request.connection_string}",
                "controller_type": "webots" if is_webots else "dronekit",
            }
        else:
            error_msg = "Failed to connect to drone. Make sure the simulator is running (should be started automatically by run.py)"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

    except Exception as e:
        error_msg = f"Connection error: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback

        traceback.print_exc()

        # Provide helpful error messages
        if "Connection refused" in str(e):
            error_msg = "Connection refused. Make sure the simulator is running (should be started automatically by run.py)"
        elif "timeout" in str(e).lower():
            error_msg = (
                "Connection timeout. The simulator may not be responding. Check if it's running on "
                + request.connection_string
            )

        raise HTTPException(status_code=400, detail=error_msg)


@app.post("/api/drone/disconnect")
async def disconnect_drone():
    """Disconnect from drone."""
    global drone_controller

    if drone_controller:
        try:
            if drone_controller.vehicle:
                drone_controller.vehicle.close()
            drone_controller = None
            return {"status": "success", "message": "Disconnected from drone"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success", "message": "No drone connected"}


@app.get("/api/drone/status")
async def get_drone_status():
    """Get current drone status."""
    return build_telemetry_payload()


@app.post("/api/mission/upload")
async def upload_mission(request: MissionRequest):
    """Upload mission waypoints to the drone."""
    global current_mission

    if not drone_controller or not drone_controller.connected:
        raise HTTPException(status_code=400, detail="Drone not connected")

    waypoints = [waypoint.dict() for waypoint in request.waypoints]
    if not waypoints:
        raise HTTPException(status_code=400, detail="No waypoints provided")

    function_executor = FunctionExecutor(drone_controller)
    validation_error = function_executor.validate_waypoints(waypoints)
    if validation_error:
        raise HTTPException(status_code=400, detail=validation_error)

    current_mission = waypoints
    log_event("mission_uploaded", {"waypoints": waypoints})

    success = drone_controller.upload_mission(waypoints)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to upload mission")

    return {"status": "success", "waypoints": len(waypoints)}


@app.post("/api/mission/execute")
async def execute_mission():
    """Execute the currently uploaded mission."""
    if not drone_controller or not drone_controller.connected:
        raise HTTPException(status_code=400, detail="Drone not connected")

    if not current_mission:
        raise HTTPException(status_code=400, detail="No mission uploaded")

    success = drone_controller.execute_mission()
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start mission execution")

    log_event("mission_started", {"waypoints": len(current_mission)})
    return {"status": "success", "message": "Mission execution started"}


@app.get("/api/sessions")
async def get_sessions():
    """List available session logs."""
    return {"sessions": list_sessions()}


@app.get("/api/sessions/latest")
async def get_latest_session():
    """Get the most recent session events."""
    sessions = list_sessions()
    if not sessions:
        return {"session": None, "events": []}

    latest = sessions[0]
    filename = str(latest["filename"])
    path = SESSION_LOG_DIR / filename
    return {"session": latest, "events": load_session_events(path)}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get events for a specific session."""
    path = SESSION_LOG_DIR / f"session_{session_id}.jsonl"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    return {"session": {"id": session_id}, "events": load_session_events(path)}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    print("✅ WebSocket client connected")
    log_event("client_connected", {"client": "websocket"})

    # Create function executor
    function_executor = FunctionExecutor(drone_controller)

    async def telemetry_loop():
        last_logged = 0.0
        while True:
            payload = build_telemetry_payload()
            try:
                await websocket.send_json({"type": "telemetry", "content": payload})
            except Exception:
                break

            now = time.time()
            if payload.get("connected") and now - last_logged >= TELEMETRY_LOG_INTERVAL:
                log_event("telemetry", payload)
                last_logged = now

            await asyncio.sleep(TELEMETRY_PUSH_INTERVAL)

    telemetry_task = asyncio.create_task(telemetry_loop())

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")

            print(f"📨 Received message: {user_message}")
            log_event("user_message", {"message": user_message})

            # Send user message acknowledgment
            await websocket.send_json({"type": "user_message", "content": user_message})

            # Check if LLM is configured
            if not llm_interface:
                print("❌ LLM not configured")
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": "Please configure an AI provider first",
                    }
                )
                continue

            # Process with LLM
            try:
                print(f"🤖 Processing with LLM...")

                # Update function executor with current drone controller
                function_executor.drone_controller = drone_controller

                # Get drone context if connected
                drone_context = ""
                if drone_controller and drone_controller.connected:
                    status = await get_drone_status()
                    drone_context = (
                        f"\nCurrent Drone Status: {json.dumps(status, indent=2)}"
                    )
                    print(
                        f"🚁 Added drone context: connected={status.get('connected', False)}"
                    )
                else:
                    print(
                        f"⚠️  Drone not connected (controller exists: {drone_controller is not None}, connected: {drone_controller.connected if drone_controller else False})"
                    )

                # Add function schemas for Ollama
                functions_info = ""
                if current_config and current_config.provider == "ollama":
                    functions_info = "\n\n" + format_function_schemas_for_ollama(
                        FUNCTION_SCHEMAS
                    )

                # Create messages for LLM
                # Check connection status for better prompt
                is_connected = (
                    drone_controller and drone_controller.connected
                    if drone_controller
                    else False
                )
                connection_note = (
                    "The drone IS CONNECTED and ready for commands."
                    if is_connected
                    else "The drone is NOT CONNECTED. Tell the user to connect first."
                )

                system_prompt = f"""You are DeepDrone AI, an assistant that controls drones using natural language.

{connection_note}
{drone_context}

IMPORTANT: When the user asks you to perform a drone action (like takeoff, land, fly somewhere, etc.), you MUST execute the appropriate function immediately. Do NOT just provide instructions - actually execute the command.

{functions_info}

When executing commands:
1. ALWAYS check the drone status above - if connected is true, the drone IS ready
2. Use the functions to perform the action
3. After getting the function result, explain what happened to the user in a friendly way

Example of how to execute a function:
User: "Take off to 20 meters"
Your response:
EXECUTE_FUNCTION: arm_and_takeoff
ARGUMENTS: {{"altitude": 20}}"""

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ]

                # Get LLM response
                print(f"⏳ Calling LLM chat method...")
                response_data = await asyncio.to_thread(
                    llm_interface.chat_with_metadata, messages
                )

                print(f"✅ Got LLM response")
                print(f"Response data type: {type(response_data)}")
                print(
                    f"Response data keys: {response_data.keys() if isinstance(response_data, dict) else 'NOT A DICT'}"
                )

                # Check if response contains a function call
                response_content = (
                    response_data.get("content", "")
                    if isinstance(response_data, dict)
                    else str(response_data)
                )
                print(
                    f"Response content preview (first 200 chars): {response_content[:200]}"
                )

                # Parse function calls from response
                if "EXECUTE_FUNCTION:" in response_content:
                    print("🔧 Function call detected in response")

                    # Extract function name and arguments
                    lines = response_content.split("\n")
                    function_name = None
                    arguments = {}

                    for i, line in enumerate(lines):
                        if line.startswith("EXECUTE_FUNCTION:"):
                            function_name = line.replace(
                                "EXECUTE_FUNCTION:", ""
                            ).strip()
                        elif line.startswith("ARGUMENTS:"):
                            try:
                                args_str = line.replace("ARGUMENTS:", "").strip()
                                arguments = json.loads(args_str) if args_str else {}
                            except json.JSONDecodeError:
                                print(f"⚠️  Failed to parse arguments: {line}")

                    if function_name:
                        print(
                            f"⚡ Executing function: {function_name} with args: {arguments}"
                        )

                        # Execute the function
                        result = await asyncio.to_thread(
                            function_executor.execute_function, function_name, arguments
                        )

                        print(f"✅ Function result: {result}")

                        # Ask LLM to format the result for the user
                        follow_up_prompt = f"""The function {function_name} was executed with result: {json.dumps(result)}

Please explain this result to the user in a natural, friendly way. Be concise."""

                        messages.append(
                            {"role": "assistant", "content": response_content}
                        )
                        messages.append({"role": "user", "content": follow_up_prompt})

                        # Get formatted response
                        final_response_data = await asyncio.to_thread(
                            llm_interface.chat_with_metadata, messages
                        )

                        response_data = final_response_data

                # Send AI response
                if (
                    response_data
                    and isinstance(response_data, dict)
                    and response_data.get("content")
                ):
                    # Prepare metadata (thinking info)
                    metadata = {}
                    if response_data.get("thinking"):
                        metadata["thinking"] = response_data["thinking"]
                        metadata["thinking_time"] = response_data.get(
                            "thinking_time", 0
                        )

                    content_to_send = response_data["content"]
                    print(
                        f"📤 Sending content to client (length: {len(content_to_send)}, preview: {content_to_send[:100]})"
                    )

                    await websocket.send_json(
                        {
                            "type": "ai_message",
                            "content": content_to_send,
                            "metadata": metadata if metadata else None,
                        }
                    )
                    log_event("ai_message", {"message": content_to_send})
                    print(f"📤 Sent response to client successfully")
                else:
                    print(f"⚠️  Empty response from LLM!")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "content": "Received empty response from AI model",
                        }
                    )

            except Exception as e:
                print(f"❌ Error processing message: {str(e)}")
                import traceback

                traceback.print_exc()

                await websocket.send_json(
                    {"type": "error", "content": f"Error processing message: {str(e)}"}
                )

    except WebSocketDisconnect:
        print("🔌 Client disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback

        traceback.print_exc()
        await websocket.close()
    finally:
        telemetry_task.cancel()
        try:
            await telemetry_task
        except asyncio.CancelledError:
            pass
        log_event("client_disconnected", {"client": "websocket"})


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn

    print("🚁 Starting DeepDrone Web Server...")
    print("📡 Open your browser at: http://localhost:8000")

    uvicorn.run(app, host="0.0.0.0", port=8000)
