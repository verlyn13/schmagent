# schmagent/models/chat_model.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Message:
    """Representation of a chat message."""
    
    def __init__(self, role: str, content: str):
        """
        Initialize a chat message.
        
        Args:
            role: The role of the message sender (user, assistant, system)
            content: The text content of the message
        """
        self.role = role
        self.content = content
        
    def to_dict(self) -> Dict[str, str]:
        """Convert message to dictionary format."""
        return {
            "role": self.role,
            "content": self.content
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Message':
        """Create a Message from a dictionary."""
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", "")
        )

class ChatModel(ABC):
    """Abstract base class for chat model implementations."""
    
    def __init__(self, config):
        """
        Initialize the chat model with configuration.
        
        Args:
            config: The application configuration object
        """
        self.config = config
        self.provider_name = "base"
        self.context_messages = []
        self.setup()
        
    def setup(self) -> None:
        """Set up the model with provider-specific configuration."""
        pass
    
    @abstractmethod
    async def generate_response(self, messages: List[Message]) -> str:
        """
        Generate a response based on the conversation history.
        
        Args:
            messages: A list of Message objects representing the conversation
            
        Returns:
            A string containing the model's response
        """
        pass
    
    def add_context_message(self, role: str, content: str) -> None:
        """
        Add a message to the persistent context.
        
        Args:
            role: The role of the message sender
            content: The text content of the message
        """
        self.context_messages.append(Message(role, content))
    
    def set_system_prompt(self, prompt: str) -> None:
        """
        Set the system prompt for the conversation.
        
        Args:
            prompt: The system prompt text
        """
        # Remove any existing system messages
        self.context_messages = [msg for msg in self.context_messages if msg.role != "system"]
        # Add the new system prompt
        self.context_messages.insert(0, Message("system", prompt))
    
    def prepare_messages(self, user_messages: List[Message]) -> List[Message]:
        """
        Prepare the full message list including context and user messages.
        
        Args:
            user_messages: The user-specific conversation messages
            
        Returns:
            A combined list of context and user messages
        """
        return self.context_messages + user_messages
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.
        
        Returns:
            Dictionary with model details
        """
        model_config = self.config.get_model_details(self.provider_name)
        return {
            "provider": self.provider_name,
            "model": model_config.get("model", "unknown"),
            "temperature": model_config.get("temperature", 0.7),
            "max_tokens": model_config.get("max_tokens", 2048),
        }