"""
Interactive drone chat interface - similar to Claude Code environment.
"""

import os
import sys
import time
import threading
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.align import Align
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import confirm
import re

from .config import ModelConfig
from .llm_interface import LLMInterface
from .drone_tools import DroneToolsManager

class DroneChatInterface:
    """Interactive chat interface for drone control with AI."""
    
    def __init__(self, model_config: ModelConfig, connection_string: Optional[str] = None):
        self.console = Console()
        self.model_config = model_config
        self.connection_string = connection_string or "udp:127.0.0.1:14550"
        
        # Initialize components
        self.llm = LLMInterface(model_config)
        self.drone_tools = DroneToolsManager(self.connection_string)
        
        # Chat state
        self.chat_history: List[Dict[str, str]] = []
        self.session_active = True
        
        # Setup prompt components
        self.history = InMemoryHistory()
        self.completer = WordCompleter([
            'connect', 'takeoff', 'land', 'fly', 'goto', 'mission', 'status',
            'battery', 'location', 'return', 'home', 'help', 'quit', 'exit',
            'emergency', 'stop', 'altitude', 'waypoint', 'navigate'
        ])
        
        self.style = Style.from_dict({
            'prompt': '#00ff00 bold',
            'input': '#ffffff',
            'completion-menu.completion': 'bg:#333333 #ffffff',
            'completion-menu.completion.current': 'bg:#00ff00 #000000 bold',
        })
        
        # Status tracking
        self.last_status_update = time.time()
        self.status_thread = None
        self.status_running = False
    
    def start(self):
        """Start the interactive chat session."""
        self._show_welcome()
        self._start_status_monitor()
        
        try:
            while self.session_active:
                try:
                    # Get user input
                    user_input = self._get_user_input()
                    
                    if not user_input.strip():
                        continue
                    
                    # Handle special commands
                    if self._handle_special_commands(user_input):
                        continue
                    
                    # Process the message
                    self._process_message(user_input)
                    
                except KeyboardInterrupt:
                    self._handle_exit()
                    break
                except EOFError:
                    self._handle_exit()
                    break
                    
        finally:
            self._cleanup()
    
    def _show_welcome(self):
        """Show welcome message and status."""
        welcome_panel = Panel(
            f"""[bold green]🚁 DEEPDRONE CHAT INTERFACE[/bold green]

[bold]AI Model:[/bold] {self.model_config.name} ({self.model_config.provider})
[bold]Model ID:[/bold] {self.model_config.model_id}
[bold]Drone Connection:[/bold] {self.connection_string}
[bold]Status:[/bold] Ready for commands

[bold cyan]🎯 Available Commands:[/bold cyan]
• Natural language: "Connect to drone and take off to 30 meters"
• Status commands: "Show battery status", "What's my location?"
• Mission commands: "Fly in a square pattern", "Return home"
• Help: Type 'help' for more information
• Exit: Type 'quit' or 'exit' to end session

[dim]Type your commands below. The AI will interpret and execute drone operations.[/dim]""",
            title="[bold green]DeepDrone Control Center[/bold green]",
            border_style="bright_green",
            padding=(1, 2)
        )
        
        self.console.print(welcome_panel)
        self.console.print()
    
    def _get_user_input(self) -> str:
        """Get user input."""
        try:
            # Use simple input() for better compatibility
            return input("🚁 DeepDrone> ")
        except (KeyboardInterrupt, EOFError):
            return '/quit'
    
    def _handle_special_commands(self, command: str) -> bool:
        """Handle special commands. Returns True if handled."""
        cmd = command.strip().lower()
        
        if cmd in ['/quit', '/exit', 'quit', 'exit']:
            self.session_active = False
            return True
        
        elif cmd in ['/help', 'help']:
            self._show_help()
            return True
        
        elif cmd in ['/status', 'status']:
            self._show_detailed_status()
            return True
        
        elif cmd in ['/clear', 'clear']:
            self.console.clear()
            self._show_welcome()
            return True
        
        elif cmd.startswith('/connect'):
            parts = cmd.split()
            if len(parts) > 1:
                self.connection_string = parts[1]
                self._connect_drone_direct()
            else:
                self.console.print("[red]Usage: /connect <connection_string>[/red]")
            return True
        
        elif cmd in ['/disconnect', 'disconnect']:
            self._disconnect_drone_direct()
            return True
        
        elif cmd in ['/emergency', 'emergency']:
            self._emergency_stop()
            return True
        
        elif cmd in ['/ollama', 'ollama']:
            self._show_ollama_status()
            return True
        
        return False
    
    def _process_message(self, user_message: str):
        """Process user message with AI and execute drone commands."""
        # Add to history
        self.chat_history.append({"role": "user", "content": user_message})
        
        # Show user message
        self.console.print(Panel(
            user_message,
            title="[bold blue]You[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        ))
        
        # Generate AI response
        with Live(
            Spinner("dots", text="[green]🤖 AI is analyzing your request...[/green]"),
            console=self.console,
            transient=True
        ) as live:
            
            try:
                # Create system prompt for drone operations
                system_prompt = self._create_drone_system_prompt()
                
                # Prepare messages for AI
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(self.chat_history[-10:])  # Last 10 messages for context
                
                # Get AI response
                ai_response = self.llm.chat(messages)
                
                live.stop()
                
                # Process the response for drone commands
                self._process_ai_response(ai_response)
                
                # Add to history
                self.chat_history.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                live.stop()
                self.console.print(f"[red]❌ Error processing request: {e}[/red]")
    
    def _create_drone_system_prompt(self) -> str:
        """Create system prompt for drone operations."""
        return f"""You are DeepDrone AI, an advanced drone control assistant. You can control real drones through Python code.

Current drone status:
- Connected: {'Yes' if self.drone_tools.is_connected() else 'No'}
- Connection: {self.connection_string}
- Mission active: {'Yes' if self.drone_tools.mission_in_progress else 'No'}

Available drone functions (use these in Python code blocks):
- connect_drone(connection_string): Connect to drone
- takeoff(altitude): Take off to specified altitude in meters
- land(): Land the drone
- return_home(): Return to launch point
- fly_to(lat, lon, alt): Fly to GPS coordinates
- get_location(): Get current GPS position
- get_battery(): Get battery status
- execute_mission(waypoints): Execute mission with waypoints list
- disconnect_drone(): Disconnect from drone

When user asks for drone operations:
1. Explain what you'll do
2. Provide Python code in ```python code blocks
3. The code will be executed automatically
4. Provide status updates

Example response:
"I'll connect to the drone and take off to 30 meters altitude.

```python
# Connect to the drone
connect_drone('{self.connection_string}')

# Take off to 30 meters
takeoff(30)

# Get status
location = get_location()
battery = get_battery()
print(f"Location: {{location}}")
print(f"Battery: {{battery}}")
```

The drone should now be airborne at 30 meters altitude."

Always prioritize safety and explain each operation clearly."""
    
    def _process_ai_response(self, response: str):
        """Process AI response and execute any drone commands."""
        # Show AI response
        if any(marker in response for marker in ['**', '*', '```', '#', '-', '1.']):
            content = Markdown(response)
        else:
            content = Text(response)
        
        self.console.print(Panel(
            content,
            title="[bold green]🤖 DeepDrone AI[/bold green]",
            border_style="green",
            padding=(0, 1)
        ))
        
        # Extract and execute Python code blocks
        code_blocks = self._extract_code_blocks(response)
        if code_blocks:
            self.console.print(Panel(
                "[yellow]🔧 Executing drone operations...[/yellow]",
                border_style="yellow"
            ))
            
            for i, code in enumerate(code_blocks, 1):
                self.console.print(f"[dim]Executing code block {i}...[/dim]")
                try:
                    result = self._execute_drone_code(code)
                    if result:
                        self.console.print(Panel(
                            f"[green]✅ Execution Result:[/green]\n{result}",
                            border_style="green"
                        ))
                except Exception as e:
                    self.console.print(Panel(
                        f"[red]❌ Execution Error:[/red]\n{str(e)}",
                        border_style="red"
                    ))
    
    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract Python code blocks from markdown text."""
        pattern = r'```(?:python)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        return [match.strip() for match in matches if match.strip()]
    
    def _execute_drone_code(self, code: str) -> str:
        """Execute drone code safely."""
        # Create safe execution environment
        safe_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'dict': dict,
                'list': list,
                'range': range,
            },
            'connect_drone': self.drone_tools.connect_drone,
            'disconnect_drone': self.drone_tools.disconnect_drone,
            'takeoff': self.drone_tools.takeoff,
            'land': self.drone_tools.land,
            'return_home': self.drone_tools.return_home,
            'fly_to': self.drone_tools.fly_to,
            'get_location': self.drone_tools.get_location,
            'get_battery': self.drone_tools.get_battery,
            'execute_mission': self.drone_tools.execute_mission,
            'time': time,
        }
        
        # Capture output
        output_lines = []
        
        def capture_print(*args, **kwargs):
            output_lines.append(' '.join(str(arg) for arg in args))
        
        safe_globals['print'] = capture_print
        
        # Execute code
        exec(code, safe_globals)
        
        return '\n'.join(output_lines) if output_lines else "Code executed successfully"
    
    def _show_help(self):
        """Show help information."""
        help_text = """[bold cyan]🚁 DeepDrone Help[/bold cyan]

[bold]Natural Language Commands:[/bold]
• "Connect to the drone simulator"
• "Take off to 30 meters altitude"
• "Fly to coordinates 37.7749, -122.4194"
• "Show me the current battery status"
• "Execute a square flight pattern"
• "Return home and land safely"

[bold]Direct Commands:[/bold]
• [cyan]/status[/cyan] - Show detailed system status
• [cyan]/connect <connection>[/cyan] - Connect to specific drone
• [cyan]/disconnect[/cyan] - Disconnect from drone
• [cyan]/emergency[/cyan] - Emergency stop
• [cyan]/ollama[/cyan] - Show Ollama status and models
• [cyan]/clear[/cyan] - Clear screen
• [cyan]/help[/cyan] - Show this help
• [cyan]/quit[/cyan] - Exit DeepDrone

[bold]Example Session:[/bold]
[dim]🚁 DeepDrone> Connect to simulator and take off to 20 meters
🤖 AI: I'll connect to the simulator and take off to 20 meters...
🚁 DeepDrone> Fly in a circle with 50 meter radius
🤖 AI: I'll create a circular flight pattern...[/dim]

[bold]Tips:[/bold]
• Use arrow keys to navigate command history
• Tab completion available for common commands
• AI understands natural language - be conversational!
• Always prioritize safety in flight operations"""
        
        self.console.print(Panel(
            help_text,
            title="[bold]DeepDrone Help[/bold]",
            border_style="cyan",
            padding=(1, 2)
        ))
    
    def _show_detailed_status(self):
        """Show detailed system and drone status."""
        status = self.drone_tools.get_status()
        
        # Create status table
        table = Table(title="System Status", show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=20)
        table.add_column("Status", style="white")
        table.add_column("Details", style="yellow")
        
        # AI Model status
        table.add_row("AI Model", "✅ Online", f"{self.model_config.name} ({self.model_config.provider})")
        
        # Drone connection
        conn_status = "✅ Connected" if status["connected"] else "❌ Disconnected"
        table.add_row("Drone Connection", conn_status, self.connection_string)
        
        # Mission status
        mission_status = "🚁 Active" if status["mission_in_progress"] else "⏸️ Standby"
        table.add_row("Mission", mission_status, status.get("phase", "N/A"))
        
        # Current status
        table.add_row("System Status", status["status"], "")
        
        if status["connected"]:
            location = status.get("location", {})
            battery = status.get("battery", {})
            
            if not location.get("error"):
                lat = location.get("latitude", "N/A")
                lon = location.get("longitude", "N/A")
                alt = location.get("altitude", "N/A")
                table.add_row("Location", "📍 GPS Lock", f"Lat: {lat}, Lon: {lon}, Alt: {alt}m")
            
            if not battery.get("error"):
                voltage = battery.get("voltage", "N/A")
                level = battery.get("level", "N/A")
                table.add_row("Battery", "🔋 Monitoring", f"Voltage: {voltage}V, Level: {level}%")
        
        self.console.print(table)
        
        # Show recent log entries
        if status.get("log_entries"):
            self.console.print("\n[bold]Recent Activity:[/bold]")
            for entry in status["log_entries"][-5:]:
                self.console.print(f"[dim]{entry}[/dim]")
    
    def _connect_drone_direct(self):
        """Connect to drone directly."""
        with Live(
            Spinner("dots", text=f"Connecting to {self.connection_string}..."),
            console=self.console,
            transient=True
        ) as live:
            
            success = self.drone_tools.connect_drone(self.connection_string)
            live.stop()
            
            if success:
                self.console.print(f"[green]✅ Connected to drone at {self.connection_string}[/green]")
            else:
                self.console.print(f"[red]❌ Failed to connect to {self.connection_string}[/red]")
    
    def _disconnect_drone_direct(self):
        """Disconnect from drone directly."""
        if self.drone_tools.is_connected():
            self.drone_tools.disconnect_drone()
            self.console.print("[yellow]📡 Disconnected from drone[/yellow]")
        else:
            self.console.print("[yellow]No active drone connection[/yellow]")
    
    def _emergency_stop(self):
        """Emergency stop operation."""
        if self.drone_tools.is_connected():
            self.console.print("[red]🚨 EMERGENCY STOP INITIATED[/red]")
            self.drone_tools.emergency_stop()
        else:
            self.console.print("[yellow]No active drone connection for emergency stop[/yellow]")
    
    def _start_status_monitor(self):
        """Start background status monitoring."""
        self.status_running = True
        self.status_thread = threading.Thread(target=self._status_monitor_loop, daemon=True)
        self.status_thread.start()
    
    def _status_monitor_loop(self):
        """Background status monitoring loop."""
        while self.status_running and self.session_active:
            try:
                time.sleep(5)  # Update every 5 seconds
                # Could update status bar here if needed
            except Exception:
                break
    
    def _handle_exit(self):
        """Handle session exit."""
        self.console.print("\n[yellow]🚁 Shutting down DeepDrone...[/yellow]")
        
        if self.drone_tools.is_connected():
            from rich.prompt import Confirm
            if Confirm.ask("Disconnect from drone before exit?", default=True):
                self.drone_tools.disconnect_drone()
        
        self.session_active = False
    
    def _show_ollama_status(self):
        """Show Ollama status and available models."""
        try:
            import ollama
            
            # Check connection
            try:
                models_response = ollama.list()
                available_models = models_response.models if hasattr(models_response, 'models') else []
                
                self.console.print("[bold green]✅ Ollama Status: Connected[/bold green]\n")
                
                if available_models:
                    self.console.print(f"[bold]📚 Available Models ({len(available_models)}):[/bold]")
                    for model in available_models:
                        name = model.model
                        size = model.size if hasattr(model, 'size') else 0
                        size_gb = size / (1024**3) if size else 0
                        modified = str(model.modified_at)[:19] if hasattr(model, 'modified_at') else 'Unknown'
                        
                        self.console.print(f"  • [green]{name}[/green] ([blue]{size_gb:.1f} GB[/blue]) - {modified}")
                else:
                    self.console.print("[yellow]📭 No models installed[/yellow]")
                    self.console.print("\n💡 Install a model with:")
                    self.console.print("   [cyan]ollama pull llama3.1[/cyan]")
                    self.console.print("   [cyan]ollama pull codestral[/cyan]")
                    self.console.print("   [cyan]ollama pull qwen2.5-coder[/cyan]")
                
                self.console.print(f"\n[dim]Current model: {self.model_config.model_id}[/dim]")
                
            except Exception as e:
                self.console.print("[red]❌ Ollama Status: Not connected[/red]")
                self.console.print(f"[red]Error: {e}[/red]\n")
                self.console.print("💡 Make sure Ollama is running:")
                self.console.print("   [cyan]ollama serve[/cyan]\n")
                self.console.print("📥 Download Ollama from:")
                self.console.print("   [cyan]https://ollama.com/download[/cyan]")
        
        except ImportError:
            self.console.print("[red]❌ Ollama package not installed[/red]")
            self.console.print("Install with: [cyan]pip install ollama[/cyan]")
    
    def _cleanup(self):
        """Cleanup resources."""
        self.status_running = False
        if self.drone_tools.is_connected():
            self.drone_tools.disconnect_drone()
        
        self.console.print("[green]🚁 DeepDrone session ended. Fly safe![/green]")