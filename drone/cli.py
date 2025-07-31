"""
Command Line Interface for DeepDrone terminal application.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint
from typing import Optional
import getpass

from .config import config_manager, ModelConfig
# Import will be done inside functions to avoid circular imports

app = typer.Typer(
    name="deepdrone",
    help="🚁 DeepDrone - AI-Powered Drone Control Terminal",
    add_completion=False
)

console = Console()

@app.command()
def chat(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use for chat"),
    connection: Optional[str] = typer.Option(None, "--connection", "-c", help="Drone connection string")
):
    """Start interactive chat with drone AI."""
    
    # Show welcome banner
    console.print(Panel.fit(
        "[bold green]🚁 DEEPDRONE TERMINAL[/bold green]\n"
        "[dim]AI-Powered Drone Control System[/dim]",
        border_style="bright_green"
    ))
    
    # Select model if not provided
    if not model:
        model = select_model()
        if not model:
            return
    
    # Validate model exists
    model_config = config_manager.get_model(model)
    if not model_config:
        console.print(f"[red]Error: Model '{model}' not found[/red]")
        console.print("Use 'deepdrone models list' to see available models")
        return
    
    # Check if model needs API key
    if model_config.provider in ["openai", "anthropic"] and not model_config.api_key:
        console.print(f"[yellow]Model '{model}' requires an API key[/yellow]")
        if Confirm.ask("Would you like to set it now?"):
            set_api_key_interactive(model)
            # Reload model config after setting API key
            model_config = config_manager.get_model(model)
    
    # Start chat
    try:
        from .terminal_chat import TerminalDroneChat
        chat_session = TerminalDroneChat(model_config, connection)
        chat_session.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Chat session ended[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting chat: {e}[/red]")

# Create models subcommand group
models_app = typer.Typer(help="Manage AI models")
app.add_typer(models_app, name="models")

@models_app.command("list")
def list_models():
    """List all available models."""
    models = config_manager.list_models()
    
    if not models:
        console.print("[yellow]No models configured[/yellow]")
        return
    
    table = Table(title="Available Models")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Provider", style="magenta")
    table.add_column("Model ID", style="blue")
    table.add_column("API Key", style="green")
    table.add_column("Status", style="yellow")
    
    for name in models:
        config = config_manager.get_model(name)
        api_key_status = "✓" if config.api_key else "✗"
        
        # Check status
        if config.provider == "ollama":
            status = "Local"
        elif config.api_key:
            status = "Ready"
        else:
            status = "Needs API Key"
        
        table.add_row(
            name,
            config.provider,
            config.model_id,
            api_key_status,
            status
        )
    
    console.print(table)
    
    # Show usage hint
    console.print("\n[dim]Use 'deepdrone chat -m <model_name>' to start chatting[/dim]")

@models_app.command("add")
def add_model(
    name: str = typer.Argument(..., help="Name for the model"),
    provider: str = typer.Argument(..., help="Provider (openai, anthropic, ollama, etc.)"),
    model_id: str = typer.Argument(..., help="Model ID/identifier"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Base URL for API"),
    max_tokens: int = typer.Option(2048, "--max-tokens", help="Maximum tokens"),
    temperature: float = typer.Option(0.7, "--temperature", help="Temperature setting")
):
    """Add a new model configuration."""
    
    model_config = ModelConfig(
        name=name,
        provider=provider,
        model_id=model_id,
        base_url=base_url,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    config_manager.add_model(model_config)
    console.print(f"[green]Model '{name}' added successfully[/green]")
    
    # Ask for API key if needed
    if provider in ["openai", "anthropic"]:
        if Confirm.ask(f"Would you like to set the API key for '{name}' now?"):
            set_api_key_interactive(name)

@models_app.command("remove")
def remove_model(name: str = typer.Argument(..., help="Name of model to remove")):
    """Remove a model configuration."""
    
    if not config_manager.get_model(name):
        console.print(f"[red]Model '{name}' not found[/red]")
        return
    
    if Confirm.ask(f"Are you sure you want to remove model '{name}'?"):
        if config_manager.remove_model(name):
            console.print(f"[green]Model '{name}' removed successfully[/green]")
        else:
            console.print(f"[red]Failed to remove model '{name}'[/red]")

@models_app.command("set-key")
def set_api_key(
    model: str = typer.Argument(..., help="Model name"),
    key: Optional[str] = typer.Option(None, "--key", help="API key (will prompt if not provided)")
):
    """Set API key for a model."""
    set_api_key_interactive(model, key)

@app.command("config")
def show_config():
    """Show current configuration."""
    
    console.print(Panel.fit(
        f"[bold]Configuration Directory:[/bold] {config_manager.settings.config_dir}\n"
        f"[bold]Models File:[/bold] {config_manager.settings.models_file}\n"
        f"[bold]Default Model:[/bold] {config_manager.settings.default_model}\n"
        f"[bold]Default Connection:[/bold] {config_manager.settings.drone.default_connection_string}",
        title="DeepDrone Configuration",
        border_style="blue"
    ))

# Create ollama subcommand group
ollama_app = typer.Typer(help="Ollama-specific commands")
app.add_typer(ollama_app, name="ollama")

@ollama_app.command("check")
def check_ollama():
    """Check if Ollama is running and list available models."""
    try:
        import ollama
        
        # Try to connect to Ollama
        models = ollama.list()
        
        if not hasattr(models, 'models') or not models.models:
            console.print("[yellow]Ollama is running but no models are installed[/yellow]")
            console.print("Install a model with: ollama pull llama3.1")
            return
            
        table = Table(title="Ollama Models")
        table.add_column("Name", style="cyan")
        table.add_column("Size", style="blue")
        table.add_column("Modified", style="green")
        
        for model in models.models:
            table.add_row(
                model.model,
                f"{model.size / (1024**3):.1f} GB" if hasattr(model, 'size') else "Unknown",
                str(model.modified_at)[:19] if hasattr(model, 'modified_at') else 'Unknown'
            )
        
        console.print(table)
        console.print("\n[dim]Use 'deepdrone models add <name> ollama <model_name>' to add to DeepDrone[/dim]")
        
    except ImportError:
        console.print("[red]Ollama Python package not installed[/red]")
        console.print("Install with: pip install ollama")
    except Exception as e:
        console.print(f"[red]Error connecting to Ollama: {e}[/red]")
        console.print("Make sure Ollama is running: ollama serve")

def select_model() -> Optional[str]:
    """Interactive model selection."""
    models = config_manager.list_models()
    
    if not models:
        console.print("[red]No models configured[/red]")
        console.print("Use 'deepdrone models add' to add a model")
        return None
    
    console.print("\n[bold]Available Models:[/bold]")
    for i, model_name in enumerate(models, 1):
        config = config_manager.get_model(model_name)
        status = "✓" if config.api_key or config.provider == "ollama" else "⚠ (needs API key)"
        console.print(f"  {i}. {model_name} ({config.provider}) {status}")
    
    while True:
        try:
            choice = Prompt.ask(
                "\nSelect model",
                choices=[str(i) for i in range(1, len(models) + 1)] + models,
                default="1"
            )
            
            if choice.isdigit():
                return models[int(choice) - 1]
            elif choice in models:
                return choice
        except (ValueError, IndexError):
            console.print("[red]Invalid selection[/red]")

def set_api_key_interactive(model_name: str, api_key: Optional[str] = None):
    """Set API key interactively."""
    model_config = config_manager.get_model(model_name)
    if not model_config:
        console.print(f"[red]Model '{model_name}' not found[/red]")
        return
    
    if model_config.provider == "ollama":
        console.print(f"[yellow]Model '{model_name}' is an Ollama model and doesn't need an API key[/yellow]")
        return
    
    if not api_key:
        console.print(f"\n[bold]Setting API key for {model_name} ({model_config.provider})[/bold]")
        
        if model_config.provider == "openai":
            console.print("Get your OpenAI API key from: https://platform.openai.com/api-keys")
        elif model_config.provider == "anthropic":
            console.print("Get your Anthropic API key from: https://console.anthropic.com/")
        
        api_key = getpass.getpass("Enter API key (hidden): ")
    
    if api_key.strip():
        if config_manager.set_api_key(model_name, api_key.strip()):
            console.print(f"[green]API key set for '{model_name}'[/green]")
        else:
            console.print(f"[red]Failed to set API key for '{model_name}'[/red]")
    else:
        console.print("[yellow]No API key provided[/yellow]")

if __name__ == "__main__":
    app()