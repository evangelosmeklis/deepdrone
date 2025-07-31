"""
LLM Interface for DeepDrone supporting LiteLLM and Ollama.
"""

import os
from typing import List, Dict, Any, Optional
import json
import logging

from .config import ModelConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for interacting with various LLM providers."""
    
    def __init__(self, model_config: ModelConfig):
        self.model_config = model_config
        self._setup_client()
    
    def _setup_client(self):
        """Set up the appropriate client based on model provider."""
        if self.model_config.provider == "ollama":
            self._setup_ollama()
        else:
            self._setup_litellm()
    
    def _setup_ollama(self):
        """Set up Ollama client."""
        try:
            import ollama
            self.client = ollama
            self.client_type = "ollama"
            
            # Test connection
            try:
                models = self.client.list()
                available_models = models.models if hasattr(models, 'models') else []
                logger.info(f"Connected to Ollama. Available models: {len(available_models)}")
                
                # Check if the requested model is available
                model_names = [model.model for model in available_models]
                if self.model_config.model_id not in model_names:
                    logger.warning(f"Model '{self.model_config.model_id}' not found locally. Available models: {model_names}")
                    
            except Exception as e:
                logger.warning(f"Could not connect to Ollama: {e}")
                logger.info("Make sure Ollama is running: ollama serve")
                
        except ImportError:
            raise ImportError("Ollama package not installed. Install with: pip install ollama")
    
    def _setup_litellm(self):
        """Set up LiteLLM client."""
        try:
            import litellm
            
            # Set API key in environment if provided (skip for local/placeholder keys)
            if self.model_config.api_key and self.model_config.api_key != "local":
                if self.model_config.provider == "openai":
                    os.environ["OPENAI_API_KEY"] = self.model_config.api_key
                elif self.model_config.provider == "anthropic":
                    os.environ["ANTHROPIC_API_KEY"] = self.model_config.api_key
                elif self.model_config.provider == "huggingface":
                    os.environ["HUGGINGFACE_API_KEY"] = self.model_config.api_key
                elif self.model_config.provider == "mistral":
                    os.environ["MISTRAL_API_KEY"] = self.model_config.api_key
                elif self.model_config.provider == "vertex_ai":
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.model_config.api_key
            
            # Set base URL if provided
            if self.model_config.base_url:
                litellm.api_base = self.model_config.base_url
            
            self.client = litellm
            self.client_type = "litellm"
            
            logger.info(f"Set up LiteLLM for {self.model_config.provider}")
            
        except ImportError:
            raise ImportError("LiteLLM package not installed. Install with: pip install litellm")
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat messages and get response."""
        try:
            if self.client_type == "ollama":
                return self._chat_ollama(messages)
            else:
                return self._chat_litellm(messages)
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"Error communicating with {self.model_config.provider}: {str(e)}"
    
    def _chat_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Chat using Ollama."""
        try:
            # Convert messages to Ollama format
            prompt = self._messages_to_prompt(messages)
            
            response = self.client.generate(
                model=self.model_config.model_id,
                prompt=prompt,
                options={
                    'temperature': self.model_config.temperature,
                    'num_predict': self.model_config.max_tokens,
                }
            )
            
            return response['response']
            
        except Exception as e:
            error_str = str(e).lower()
            
            if "model not found" in error_str or "model does not exist" in error_str:
                available_models = []
                try:
                    models = self.client.list()
                    available_models = [m.model for m in models.models] if hasattr(models, 'models') else []
                except:
                    pass
                
                error_msg = f"❌ Model '{self.model_config.model_id}' not found in Ollama.\n\n"
                
                if available_models:
                    error_msg += f"📋 Available local models:\n"
                    for model in available_models:
                        error_msg += f"  • {model}\n"
                    error_msg += f"\n💡 To install {self.model_config.model_id}, run:\n"
                    error_msg += f"   ollama pull {self.model_config.model_id}\n"
                else:
                    error_msg += "📭 No models found locally.\n\n"
                    error_msg += f"💡 To install {self.model_config.model_id}, run:\n"
                    error_msg += f"   ollama pull {self.model_config.model_id}\n\n"
                    error_msg += "🎯 Popular models to try:\n"
                    error_msg += "   • ollama pull llama3.1\n"
                    error_msg += "   • ollama pull codestral\n"
                    error_msg += "   • ollama pull qwen2.5-coder\n"
                
                return error_msg
            
            elif "connection" in error_str or "refused" in error_str:
                return "❌ Cannot connect to Ollama.\n\n💡 Make sure Ollama is running:\n   ollama serve\n\n📥 Download Ollama from: https://ollama.com/download"
            
            return f"❌ Ollama error: {str(e)}"
    
    def _chat_litellm(self, messages: List[Dict[str, str]]) -> str:
        """Chat using LiteLLM."""
        try:
            response = self.client.completion(
                model=self.model_config.model_id,
                messages=messages,
                max_tokens=self.model_config.max_tokens,
                temperature=self.model_config.temperature,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            if "api key" in str(e).lower():
                return f"API key error for {self.model_config.provider}. Please set your API key with: deepdrone models set-key {self.model_config.name}"
            elif "quota" in str(e).lower() or "billing" in str(e).lower():
                return f"Billing/quota error for {self.model_config.provider}. Please check your account."
            elif "model" in str(e).lower() and "not found" in str(e).lower():
                return f"Model '{self.model_config.model_id}' not found for {self.model_config.provider}."
            
            raise e
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to a single prompt for models that don't support chat format."""
        prompt_parts = []
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant: ")
        
        return "\n\n".join(prompt_parts)
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the LLM service."""
        try:
            test_messages = [
                {"role": "user", "content": "Hello, please respond with 'Connection test successful'"}
            ]
            
            response = self.chat(test_messages)
            
            return {
                "success": True,
                "response": response,
                "provider": self.model_config.provider,
                "model": self.model_config.model_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": self.model_config.provider,
                "model": self.model_config.model_id
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        info = {
            "name": self.model_config.name,
            "provider": self.model_config.provider,
            "model_id": self.model_config.model_id,
            "max_tokens": self.model_config.max_tokens,
            "temperature": self.model_config.temperature,
            "client_type": self.client_type,
        }
        
        if self.model_config.base_url:
            info["base_url"] = self.model_config.base_url
        
        return info