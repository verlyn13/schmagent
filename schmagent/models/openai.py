# schmagent/models/openai.py

import logging
import asyncio
from typing import Dict, List, Any, Optional
import aiohttp
from .chat_model import ChatModel, Message

logger = logging.getLogger(__name__)

class OpenAIModel(ChatModel):
    """OpenAI API implementation of the ChatModel interface."""
    
    def __init__(self, config):
        """Initialize the OpenAI model."""
        self.provider_name = "openai"
        super().__init__(config)
        
    def setup(self) -> None:
        """Set up the OpenAI model with configuration."""
        self.api_key = self.config.get_api_key("openai")
        if not self.api_key:
            logger.warning("OpenAI API key not found. Model will not work correctly.")
            
        self.model_config = self.config.get_model_details("openai")
        self.model_name = self.model_config.get("model", "gpt-4-turbo")
        self.temperature = self.model_config.get("temperature", 0.7)
        self.max_tokens = self.model_config.get("max_tokens", 2048)
        self.timeout = self.model_config.get("timeout", 60)
        self.cache_enabled = self.model_config.get("cache_enabled", True)
        
        logger.debug(f"OpenAI model initialized with model: {self.model_name}")
        
    async def generate_response(self, messages: List[Message]) -> str:
        """
        Generate a response from the OpenAI API.
        
        Args:
            messages: List of Message objects
            
        Returns:
            String response from the model
        """
        if not self.api_key:
            return "Error: OpenAI API key not configured. Please set up your API key."
        
        # Prepare the full message list
        full_messages = self.prepare_messages(messages)
        message_dicts = [message.to_dict() for message in full_messages]
        
        # Prepare the API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model_name,
            "messages": message_dicts,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        return f"Error: API request failed with status {response.status}"
                    
                    data = await response.json()
                    
                    # Extract the assistant's message
                    if "choices" in data and data["choices"]:
                        return data["choices"][0]["message"]["content"]
                    else:
                        logger.error(f"Unexpected API response format: {data}")
                        return "Error: Unexpected response format from API"
        
        except asyncio.TimeoutError:
            logger.error(f"OpenAI API request timed out after {self.timeout} seconds")
            return "Error: Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return f"Error: {str(e)}"