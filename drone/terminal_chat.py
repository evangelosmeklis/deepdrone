"""
Terminal-based chat interface for DeepDrone with LiteLLM and Ollama support.
"""

import asyncio
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import message_dialog
from prompt_toolkit.styles import Style
import json
import time

from .config import ModelConfig
from .llm_interface import LLMInterface
from .drone_tools import DroneToolsManager

class TerminalDroneChat:
    """Terminal-based chat interface for drone control."""
    
    def __init__(self, model_config: ModelConfig, connection_string: Optional[str] = None):
        self.console = Console()
        self.model_config = model_config
        self.connection_string = connection_string
        self.chat_history: List[Dict[str, str]] = []
        
        # Initialize LLM interface
        self.llm = LLMInterface(model_config)
        
        # Initialize drone tools
        self.drone_tools = DroneToolsManager(connection_string)
        
        # Chat settings
        self.show_thinking = True
        self.max_history = 50
        
        # Style for prompt
        self.prompt_style = Style.from_dict({
            'prompt': '#00ff00 bold',
            'input': '#ffffff',
        })
    
    def start(self):
        """Start the interactive chat session."""
        self._show_welcome()
        
        try:
            while True:
                user_input = self._get_user_input()
                
                if not user_input.strip():
                    continue
                
                # Handle special commands
                if user_input.startswith('/'):
                    if self._handle_command(user_input):
                        continue
                    else:
                        break
                
                # Process user message
                self._process_message(user_input)
                
        except KeyboardInterrupt:
            self._show_goodbye()
        except EOFError:
            self._show_goodbye()
    
    def _show_welcome(self):
        """Show welcome message and model info."""
        welcome_text = f"""
[bold green]🚁 DEEPDRONE TERMINAL ACTIVE[/bold green]

[bold]Model:[/bold] {self.model_config.name} ({self.model_config.provider})
[bold]Connection:[/bold] {self.connection_string or 'Not connected'}
[bold]Status:[/bold] Ready for commands

[dim]Type your commands or questions. Use /help for available commands.[/dim]
[dim]Type /quit to exit.[/dim]
        """
        
        self.console.print(Panel(
            welcome_text.strip(),
            border_style="bright_green",
            padding=(1, 2)
        ))
    
    def _show_goodbye(self):
        """Show goodbye message."""
        self.console.print("\n[yellow]🚁 DeepDrone session ended. Fly safe![/yellow]")
        
        # Disconnect from drone if connected
        if self.drone_tools.is_connected():
            self.console.print("[dim]Disconnecting from drone...[/dim]")
            self.drone_tools.disconnect()
    
    def _get_user_input(self) -> str:
        """Get user input with custom prompt."""
        try:
            return prompt(
                [('class:prompt', '🚁 DeepDrone> ')],
                style=self.prompt_style
            )
        except (KeyboardInterrupt, EOFError):
            return '/quit'
    
    def _handle_command(self, command: str) -> bool:
        """Handle special commands. Returns True to continue, False to quit."""
        cmd_parts = command[1:].split()
        if not cmd_parts:
            return True
        
        cmd = cmd_parts[0].lower()
        
        if cmd in ['quit', 'exit', 'q']:
            return False
        
        elif cmd == 'help':
            self._show_help()
        
        elif cmd == 'clear':
            self.console.clear()
            self._show_welcome()
        
        elif cmd == 'history':
            self._show_history()
        
        elif cmd == 'status':
            self._show_status()
        
        elif cmd == 'connect':
            if len(cmd_parts) > 1:
                self._connect_drone(cmd_parts[1])
            else:
                self.console.print("[red]Usage: /connect <connection_string>[/red]")
        
        elif cmd == 'disconnect':
            self._disconnect_drone()
        
        elif cmd == 'models':
            self._show_model_info()
        
        else:
            self.console.print(f"[red]Unknown command: {command}[/red]")
            self.console.print("Type /help for available commands")
        
        return True
    
    def _process_message(self, user_message: str):
        """Process user message and generate response."""
        # Add user message to history
        self.chat_history.append({"role": "user", "content": user_message})
        
        # Show user message
        self.console.print(Panel(
            user_message,
            title="[bold blue]You[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        ))
        
        # Check if this requires drone tools
        requires_tools = self._message_requires_tools(user_message)
        
        # Generate response
        with Live(
            Spinner("dots", text="[green]DeepDrone is thinking...[/green]"),
            console=self.console,
            transient=True
        ) as live:
            
            try:
                if requires_tools:
                    response = self._process_with_tools(user_message, live)
                else:
                    response = self._process_simple_chat(user_message)
                
                live.stop()
                
                # Show response
                self._show_response(response)
                
                # Add to history
                self.chat_history.append({"role": "assistant", "content": response})
                
                # Trim history if too long
                if len(self.chat_history) > self.max_history:
                    self.chat_history = self.chat_history[-self.max_history:]
                
            except Exception as e:
                live.stop()
                self.console.print(f"[red]Error: {e}[/red]")
    
    def _message_requires_tools(self, message: str) -> bool:
        """Check if message requires drone tools."""
        tool_keywords = [
            'connect', 'takeoff', 'land', 'fly', 'goto', 'mission',
            'battery', 'location', 'status', 'arm', 'disarm', 'rtl',
            'return', 'home', 'altitude', 'waypoint', 'navigate'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in tool_keywords)
    
    def _process_with_tools(self, message: str, live: Live) -> str:
        """Process message that may require drone tools."""
        # Update status
        live.update(Spinner("dots", text="[green]Analyzing command and planning actions...[/green]"))
        
        # Create system prompt with tool information
        system_prompt = self._create_system_prompt_with_tools()
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.chat_history[-10:])  # Last 10 messages for context
        messages.append({"role": "user", "content": message})
        
        # Get LLM response
        response = self.llm.chat(messages)
        
        # Check if response contains tool calls
        if self._response_has_tool_calls(response):
            live.update(Spinner("dots", text="[yellow]Executing drone operations...[/yellow]"))
            response = self._execute_tool_calls(response)
        
        return response
    
    def _process_simple_chat(self, message: str) -> str:
        """Process simple chat message without tools."""
        system_prompt = """You are DeepDrone, an AI assistant specialized in drone operations and flight control.
        
You help users with:
- Drone flight planning and mission design
- Understanding drone systems and components
- Troubleshooting flight issues
- Safety protocols and regulations
- Data analysis from drone flights

Be concise, helpful, and focus on drone-related topics. If asked about your identity, 
clearly state that you are DeepDrone, a specialized drone AI assistant."""
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.chat_history[-10:])
        messages.append({"role": "user", "content": message})
        
        return self.llm.chat(messages)
    
    def _create_system_prompt_with_tools(self) -> str:
        """Create system prompt with tool information."""
        return """You are DeepDrone, an AI assistant that can control real drones through Python code.

Available drone control functions:
- connect_drone(connection_string): Connect to drone
- disconnect_drone(): Disconnect from drone
- takeoff(altitude): Take off to specified altitude in meters
- land(): Land the drone
- return_home(): Return to launch point
- fly_to(lat, lon, alt): Fly to GPS coordinates
- get_location(): Get current GPS position
- get_battery(): Get battery status
- execute_mission(waypoints): Execute mission with list of waypoints

When user requests drone operations, write Python code using these functions.
Always explain what you're doing and provide status updates.

Example:
```python
# Connect to drone simulator
connect_drone('udp:127.0.0.1:14550')

# Take off to 30 meters
takeoff(30)

# Fly to a specific location
fly_to(37.7749, -122.4194, 30)

# Return home
return_home()

# Disconnect
disconnect_drone()
```

Be safety-conscious and explain each operation."""
    
    def _response_has_tool_calls(self, response: str) -> bool:
        """Check if response contains Python code blocks."""
        return "```python" in response or "```" in response
    
    def _execute_tool_calls(self, response: str) -> str:
        """Execute tool calls found in response."""
        # Extract Python code blocks
        code_blocks = self._extract_code_blocks(response)
        
        results = []
        for code in code_blocks:
            try:
                result = self._execute_code_block(code)
                results.append(f"✅ Executed: {result}")
            except Exception as e:
                results.append(f"❌ Error: {e}")
        
        # Append execution results to response
        if results:
            response += "\n\n**Execution Results:**\n" + "\n".join(results)
        
        return response
    
    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract Python code blocks from markdown text."""
        code_blocks = []
        lines = text.split('\n')
        in_code_block = False
        current_block = []
        
        for line in lines:
            if line.strip().startswith('```python') or line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    if current_block:
                        code_blocks.append('\n'.join(current_block))
                        current_block = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
            elif in_code_block:
                current_block.append(line)
        
        return code_blocks
    
    def _execute_code_block(self, code: str) -> str:
        """Execute a code block using drone tools."""
        # Create a safe execution environment
        safe_globals = {
            'connect_drone': self.drone_tools.connect_drone,
            'disconnect_drone': self.drone_tools.disconnect_drone,
            'takeoff': self.drone_tools.takeoff,
            'land': self.drone_tools.land,
            'return_home': self.drone_tools.return_home,
            'fly_to': self.drone_tools.fly_to,
            'get_location': self.drone_tools.get_location,
            'get_battery': self.drone_tools.get_battery,
            'execute_mission': self.drone_tools.execute_mission,
        }
        
        # Capture output
        output = []
        
        def capture_print(*args, **kwargs):
            output.append(' '.join(str(arg) for arg in args))
        
        safe_globals['print'] = capture_print
        
        # Execute code
        exec(code, safe_globals)
        
        return '\n'.join(output) if output else "Command executed successfully"
    
    def _show_response(self, response: str):
        """Show AI response with formatting."""
        # Parse as markdown if it contains markdown elements
        if any(marker in response for marker in ['**', '*', '```', '#', '-', '1.']):
            content = Markdown(response)
        else:
            content = Text(response)
        
        self.console.print(Panel(
            content,
            title="[bold green]🚁 DeepDrone[/bold green]",
            border_style="green",
            padding=(0, 1)
        ))
    
    def _show_help(self):
        """Show help message."""
        help_text = """
[bold]Available Commands:[/bold]

[bold cyan]/help[/bold cyan] - Show this help message
[bold cyan]/quit[/bold cyan] - Exit the application
[bold cyan]/clear[/bold cyan] - Clear the screen
[bold cyan]/history[/bold cyan] - Show chat history
[bold cyan]/status[/bold cyan] - Show system status
[bold cyan]/connect <connection>[/bold cyan] - Connect to drone
[bold cyan]/disconnect[/bold cyan] - Disconnect from drone
[bold cyan]/models[/bold cyan] - Show current model info

[bold]Drone Commands (natural language):[/bold]
- "Connect to simulator at udp:127.0.0.1:14550"
- "Take off to 30 meters"
- "Fly to coordinates 37.7749, -122.4194 at 50 meters"
- "Show current location and battery status"
- "Execute a square flight pattern"
- "Return home and land"

[bold]Example Conversation:[/bold]
[dim]You: Connect to the drone simulator
DeepDrone: I'll connect to the simulator for you...
You: Take off to 20 meters and fly in a circle
DeepDrone: Taking off to 20 meters and executing circular pattern...[/dim]
        """
        
        self.console.print(Panel(
            help_text.strip(),
            title="[bold]DeepDrone Help[/bold]",
            border_style="cyan"
        ))
    
    def _show_history(self):
        """Show chat history."""
        if not self.chat_history:
            self.console.print("[yellow]No chat history available[/yellow]")
            return
        
        self.console.print("[bold]Chat History:[/bold]\n")
        
        for i, msg in enumerate(self.chat_history[-10:], 1):  # Last 10 messages
            role_color = "blue" if msg["role"] == "user" else "green"
            role_name = "You" if msg["role"] == "user" else "DeepDrone"
            
            self.console.print(f"[{role_color}]{i}. {role_name}:[/{role_color}] {msg['content'][:100]}...")
    
    def _show_status(self):
        """Show system status."""
        drone_status = "Connected" if self.drone_tools.is_connected() else "Disconnected"
        drone_color = "green" if self.drone_tools.is_connected() else "red"
        
        status_text = f"""
[bold]Model:[/bold] {self.model_config.name} ({self.model_config.provider})
[bold]Drone Status:[/bold] [{drone_color}]{drone_status}[/{drone_color}]
[bold]Connection:[/bold] {self.connection_string or 'None'}
[bold]Chat History:[/bold] {len(self.chat_history)} messages
        """
        
        if self.drone_tools.is_connected():
            try:
                location = self.drone_tools.get_location()
                battery = self.drone_tools.get_battery()
                status_text += f"""
[bold]Location:[/bold] {location}
[bold]Battery:[/bold] {battery}
                """
            except Exception as e:
                status_text += f"\n[yellow]Could not get drone telemetry: {e}[/yellow]"
        
        self.console.print(Panel(
            status_text.strip(),
            title="[bold]System Status[/bold]",
            border_style="yellow"
        ))
    
    def _connect_drone(self, connection_string: str):
        """Connect to drone."""
        self.console.print(f"[yellow]Connecting to drone at {connection_string}...[/yellow]")
        
        try:
            if self.drone_tools.connect_drone(connection_string):
                self.connection_string = connection_string
                self.console.print("[green]✅ Connected to drone successfully[/green]")
            else:
                self.console.print("[red]❌ Failed to connect to drone[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ Connection error: {e}[/red]")
    
    def _disconnect_drone(self):
        """Disconnect from drone."""
        if self.drone_tools.is_connected():
            self.drone_tools.disconnect_drone()
            self.console.print("[yellow]Disconnected from drone[/yellow]")
        else:
            self.console.print("[yellow]No drone connection to disconnect[/yellow]")
    
    def _show_model_info(self):
        """Show current model information."""
        info_text = f"""
[bold]Name:[/bold] {self.model_config.name}
[bold]Provider:[/bold] {self.model_config.provider}
[bold]Model ID:[/bold] {self.model_config.model_id}
[bold]Max Tokens:[/bold] {self.model_config.max_tokens}
[bold]Temperature:[/bold] {self.model_config.temperature}
        """
        
        if self.model_config.base_url:
            info_text += f"\n[bold]Base URL:[/bold] {self.model_config.base_url}"
        
        self.console.print(Panel(
            info_text.strip(),
            title="[bold]Current Model[/bold]",
            border_style="magenta"
        ))