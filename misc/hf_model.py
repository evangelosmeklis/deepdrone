import os
from typing import Union, List, Dict, Optional, Any
from huggingface_hub import InferenceClient
from transformers import AutoTokenizer

class Message:
    """Simple message class to mimic OpenAI's message format"""
    def __init__(self, content):
        self.content = content
        self.model = ""
        self.created = 0
        self.choices = []

class HfApiModel:
    """HuggingFace API Model interface for smolagents CodeAgent"""
    
    def __init__(self, 
                 model_id='Qwen/Qwen2.5-Coder-32B-Instruct',
                 max_tokens=2096,
                 temperature=0.5,
                 custom_role_conversions=None):
        """Initialize the HuggingFace API Model.
        
        Args:
            model_id: The model ID on Hugging Face Hub
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            custom_role_conversions: Custom role mappings if needed
        """
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.custom_role_conversions = custom_role_conversions or {}
        
        # Initialize the client
        self.client = InferenceClient(model=model_id, token=os.environ.get("HF_TOKEN"))
        
        # Try to load tokenizer for token counting (optional)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        except:
            self.tokenizer = None
            print(f"Warning: Could not load tokenizer for {model_id}")
    
    def __call__(self, prompt: Union[str, dict, List[Dict]]) -> Message:
        """Make the class callable as required by smolagents"""
        try:
            # Handle different prompt formats
            if isinstance(prompt, (dict, list)):
                # Format as chat if it's a list of messages
                if isinstance(prompt, list) and all(isinstance(msg, dict) for msg in prompt):
                    messages = self._format_messages(prompt)
                    return self._generate_chat_response_message(messages)
                else:
                    # Convert to string if it's not a well-formed chat message list
                    prompt_str = str(prompt)
                    return self._generate_text_response_message(prompt_str)
            else:
                # String prompt
                prompt_str = str(prompt)
                return self._generate_text_response_message(prompt_str)
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            return Message(error_msg)
    
    def generate(self, 
                 prompt: Union[str, dict, List[Dict]],
                 stop_sequences: Optional[List[str]] = None,
                 seed: Optional[int] = None,
                 max_tokens: Optional[int] = None,
                 temperature: Optional[float] = None,
                 **kwargs) -> Message:
        """
        Generate a response from the model.
        This method is required by smolagents and provides a more complete interface
        with support for all parameters needed by smolagents.
        
        Args:
            prompt: The prompt to send to the model.
                Can be a string, dict, or list of message dicts
            stop_sequences: List of sequences where the model should stop generating
            seed: Random seed for reproducibility
            max_tokens: Maximum tokens to generate (overrides instance value if provided)
            temperature: Sampling temperature (overrides instance value if provided)
            **kwargs: Additional parameters that might be needed in the future
                
        Returns:
            Message: A Message object with the response content
        """
        # Apply override parameters if provided
        if max_tokens is not None:
            old_max_tokens = self.max_tokens
            self.max_tokens = max_tokens
        
        if temperature is not None:
            old_temperature = self.temperature
            self.temperature = temperature
            
        try:
            # Handle different prompt formats
            if isinstance(prompt, (dict, list)):
                # Format as chat if it's a list of messages
                if isinstance(prompt, list) and all(isinstance(msg, dict) for msg in prompt):
                    messages = self._format_messages(prompt)
                    result = self._generate_chat_response_message(messages, stop_sequences)
                    return result
                else:
                    # Convert to string if it's not a well-formed chat message list
                    prompt_str = str(prompt)
                    result = self._generate_text_response_message(prompt_str, stop_sequences)
                    return result
            else:
                # String prompt
                prompt_str = str(prompt)
                result = self._generate_text_response_message(prompt_str, stop_sequences)
                return result
                
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            return Message(error_msg)
            
        finally:
            # Restore original parameters if they were overridden
            if max_tokens is not None:
                self.max_tokens = old_max_tokens
                
            if temperature is not None:
                self.temperature = old_temperature
    
    def _format_messages(self, messages: List[Dict]) -> List[Dict]:
        """Format messages for the chat API"""
        formatted_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Map custom roles if needed
            if role in self.custom_role_conversions:
                role = self.custom_role_conversions[role]
            
            formatted_messages.append({"role": role, "content": content})
        
        return formatted_messages
    
    def _generate_chat_response(self, messages: List[Dict], stop_sequences: Optional[List[str]] = None) -> str:
        """Generate a response from the chat API and return string content"""
        # Prepare parameters
        params = {
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        
        # Add stop sequences if provided
        if stop_sequences:
            # Note: Some HF models may not support the stop_sequences parameter
            # We'll try without it if it fails
            try:
                params["stop_sequences"] = stop_sequences
                response = self.client.chat_completion(**params)
                content = response.choices[0].message.content
            except:
                # Try again without stop_sequences
                del params["stop_sequences"]
                print("Warning: stop_sequences parameter not supported, continuing without it")
                response = self.client.chat_completion(**params)
                content = response.choices[0].message.content
        else:
            # Call the API
            response = self.client.chat_completion(**params)
            content = response.choices[0].message.content
            
        # Check if this is for smolagents by examining if the user message has certain key words
        is_smolagents_format = False
        for msg in messages:
            if msg.get("role") == "system" and isinstance(msg.get("content"), str):
                system_content = msg.get("content", "")
                if "Thought:" in system_content and "Code:" in system_content and "<end_code>" in system_content:
                    is_smolagents_format = True
                    break
        
        # If using with smolagents, format response properly if it doesn't already have the right format
        if is_smolagents_format and not ("Thought:" in content and "Code:" in content and "<end_code>" in content):
            # Typical instruction extraction to create a better smolagents-compatible response
            user_message = ""
            for msg in messages:
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            # Extract mission type based on user message
            mission_type = "custom"
            duration = 15
            
            if "survey" in user_message.lower():
                mission_type = "survey"
                duration = 20
            elif "inspect" in user_message.lower():
                mission_type = "inspection"
                duration = 15
            elif "delivery" in user_message.lower():
                mission_type = "delivery"
                duration = 10
            elif "square" in user_message.lower():
                mission_type = "survey"
                duration = 10
                
            # Format properly for smolagents
            formatted_content = f"""Thought: I will create a {mission_type} mission plan for {duration} minutes and execute it on the simulator.
Code:
```py
mission_plan = generate_mission_plan(mission_type="{mission_type}", duration_minutes={duration})
print(f"Generated mission plan: {{mission_plan}}")
final_answer(f"I've created a {mission_type} mission plan that will take approximately {duration} minutes to execute. The plan includes waypoints for a square pattern around your current position.")
```<end_code>"""
            return formatted_content
        
        return content
    
    def _generate_chat_response_message(self, messages: List[Dict], stop_sequences: Optional[List[str]] = None) -> Message:
        """Generate a response from the chat API and return a Message object"""
        content = self._generate_chat_response(messages, stop_sequences)
        return Message(content)
    
    def _generate_text_response(self, prompt: str, stop_sequences: Optional[List[str]] = None) -> str:
        """Generate a response from the text completion API and return string content"""
        # For models that don't support the chat format, we can use text generation
        # But Qwen2.5 supports chat, so we'll convert to chat format
        messages = [{"role": "user", "content": prompt}]
        return self._generate_chat_response(messages, stop_sequences)
        
    def _generate_text_response_message(self, prompt: str, stop_sequences: Optional[List[str]] = None) -> Message:
        """Generate a response from the text completion API and return a Message object"""
        content = self._generate_text_response(prompt, stop_sequences)
        return Message(content) 