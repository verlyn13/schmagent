"""
Configuration manager for Schmagent.

This module handles loading configuration from:
1. Default values
2. .env file (if present)
3. XDG config and secrets directories
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, cast
try:
    from dotenv import load_dotenv
except ImportError:
    # For type checking only
    def load_dotenv() -> None:
        """Stub for type checking if dotenv is not available."""
        pass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for Schmagent application."""
    
    def __init__(self):
        """Initialize configuration with default values, then load from files."""
        # Load .env file if it exists
        load_dotenv()
        
        # Set up paths
        self.config_path = Path(os.getenv("CONFIG_PATH", os.path.expanduser("~/.config/schmagent")))
        self.data_path = Path(os.getenv("DATA_PATH", os.path.expanduser("~/.local/share/schmagent")))
        self.secrets_path = Path(os.getenv("SECRETS_PATH", os.path.expanduser("~/.secrets/schmagent")))
        
        # Ensure paths exist
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.secrets_path.mkdir(parents=True, exist_ok=True)
        
        # Set permissions for secrets directory
        os.chmod(self.secrets_path, 0o700)
        
        # Define file paths
        self.config_file = self.config_path / "config.json"
        self.api_keys_file = self.secrets_path / os.getenv("API_KEYS_FILE", "api_keys.json")
        
        # Initialize configuration
        self.config = self._load_defaults()
        self._load_config_file()
        self._load_environment_variables()
        
        # Handle API keys separately for security
        self.api_keys = self._load_api_keys()
        
        # Set log level after configuration is loaded
        self._configure_logging()

    def _load_defaults(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            "app": {
                "name": "Schmagent",
                "debug": False,
                "log_level": "INFO",
            },
            "model": {
                "default": "openai",
                "openai": {
                    "model": "gpt-4-turbo",
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "cache_enabled": True,
                    "timeout": 60
                },
                "anthropic": {
                    "model": "claude-3-5-sonnet",
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "cache_enabled": True,
                    "timeout": 60
                },
                "google": {
                    "model": "gemini-pro",
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "cache_enabled": True,
                    "timeout": 60
                },
                "openrouter": {
                    "model": "openai/gpt-4-turbo",
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "cache_enabled": True,
                    "timeout": 60
                },
                "perplexity": {
                    "model": "llama-3-sonar-large-32k",
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "cache_enabled": True,
                    "timeout": 60
                },
                "elevenlabs": {
                    "voice_id": "premade/adam",
                    "model": "eleven_turbo_v2",
                    "cache_enabled": True
                },
                "local": {
                    "model_path": None,
                    "model_type": "llama",
                    "cache_enabled": True,
                    "context_window": 4096
                }
            },
            "ui": {
                "theme": "system",
                "window_width": 800,
                "window_height": 600,
                "code_highlighting": True,
                "enable_screenshots": True,
            },
            "session": {
                "persistence": True,
                "max_history_sessions": 10,
                "message_history_limit": 50,
            },
            "security": {
                "api_key_encryption": True,
                "clipboard_auto_clear": False,
                "clipboard_clear_delay": 60,
            },
            "notifications": {
                "enable": True,
                "sound": True,
            },
            "shortcuts": {
                "global": "<Super>s",
            }
        }

    def _load_config_file(self) -> None:
        """Load configuration from config.json if it exists."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    self._merge_config(user_config)
                    logger.info(f"Loaded configuration from {self.config_file}")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading config file: {e}")
        else:
            # Create empty config file if it doesn't exist
            with open(self.config_file, 'w') as f:
                json.dump({}, f, indent=2)
            logger.info(f"Created empty configuration file at {self.config_file}")

    def _load_environment_variables(self) -> None:
        """Load configuration from environment variables."""
        # App settings
        app_name = os.getenv("APP_NAME")
        if app_name:
            self.config["app"]["name"] = app_name
            
        debug_str = os.getenv("DEBUG")
        if debug_str and debug_str.lower() == "true":
            self.config["app"]["debug"] = True
            
        log_level = os.getenv("LOG_LEVEL")
        if log_level:
            self.config["app"]["log_level"] = log_level
            
        # Model settings
        default_model = os.getenv("DEFAULT_MODEL")
        if default_model:
            self.config["model"]["default"] = default_model
            
        openai_model = os.getenv("OPENAI_MODEL")
        if openai_model:
            self.config["model"]["openai"]["model"] = openai_model
            
        openai_temp_str = os.getenv("OPENAI_TEMPERATURE")
        if openai_temp_str:
            try:
                self.config["model"]["openai"]["temperature"] = float(openai_temp_str)
            except ValueError:
                logger.warning(f"Invalid OPENAI_TEMPERATURE value: {openai_temp_str}")
                
        openai_tokens_str = os.getenv("OPENAI_MAX_TOKENS")
        if openai_tokens_str:
            try:
                self.config["model"]["openai"]["max_tokens"] = int(openai_tokens_str)
            except ValueError:
                logger.warning(f"Invalid OPENAI_MAX_TOKENS value: {openai_tokens_str}")
        
        # UI settings
        theme = os.getenv("THEME")
        if theme:
            self.config["ui"]["theme"] = theme
            
        width_str = os.getenv("WINDOW_WIDTH")
        if width_str:
            try:
                self.config["ui"]["window_width"] = int(width_str)
            except ValueError:
                logger.warning(f"Invalid WINDOW_WIDTH value: {width_str}")
                
        height_str = os.getenv("WINDOW_HEIGHT")
        if height_str:
            try:
                self.config["ui"]["window_height"] = int(height_str)
            except ValueError:
                logger.warning(f"Invalid WINDOW_HEIGHT value: {height_str}")
                
        highlighting_str = os.getenv("CODE_HIGHLIGHTING")
        if highlighting_str and highlighting_str.lower() == "true":
            self.config["ui"]["code_highlighting"] = True
        elif highlighting_str and highlighting_str.lower() == "false":
            self.config["ui"]["code_highlighting"] = False
            
        screenshots_str = os.getenv("ENABLE_SCREENSHOTS")
        if screenshots_str and screenshots_str.lower() == "true":
            self.config["ui"]["enable_screenshots"] = True
        elif screenshots_str and screenshots_str.lower() == "false":
            self.config["ui"]["enable_screenshots"] = False
        
        # Session settings
        persistence_str = os.getenv("SESSION_PERSISTENCE")
        if persistence_str and persistence_str.lower() == "true":
            self.config["session"]["persistence"] = True
        elif persistence_str and persistence_str.lower() == "false":
            self.config["session"]["persistence"] = False
            
        history_sessions_str = os.getenv("MAX_HISTORY_SESSIONS")
        if history_sessions_str:
            try:
                self.config["session"]["max_history_sessions"] = int(history_sessions_str)
            except ValueError:
                logger.warning(f"Invalid MAX_HISTORY_SESSIONS value: {history_sessions_str}")
                
        history_limit_str = os.getenv("MESSAGE_HISTORY_LIMIT")
        if history_limit_str:
            try:
                self.config["session"]["message_history_limit"] = int(history_limit_str)
            except ValueError:
                logger.warning(f"Invalid MESSAGE_HISTORY_LIMIT value: {history_limit_str}")
        
        # Security settings
        encryption_str = os.getenv("API_KEY_ENCRYPTION")
        if encryption_str and encryption_str.lower() == "true":
            self.config["security"]["api_key_encryption"] = True
        elif encryption_str and encryption_str.lower() == "false":
            self.config["security"]["api_key_encryption"] = False
            
        clipboard_clear_str = os.getenv("CLIPBOARD_AUTO_CLEAR")
        if clipboard_clear_str and clipboard_clear_str.lower() == "true":
            self.config["security"]["clipboard_auto_clear"] = True
        elif clipboard_clear_str and clipboard_clear_str.lower() == "false":
            self.config["security"]["clipboard_auto_clear"] = False
            
        clear_delay_str = os.getenv("CLIPBOARD_CLEAR_DELAY")
        if clear_delay_str:
            try:
                # Strip whitespace and comments
                clean_value = clear_delay_str.split('#')[0].strip()
                clear_delay = int(clean_value)
                if clear_delay > 0:
                    self.config["security"]["clipboard_clear_delay"] = clear_delay
                    logger.debug(f"Set clipboard_clear_delay to {clear_delay}")
                else:
                    logger.warning(f"Invalid CLIPBOARD_CLEAR_DELAY value: {clear_delay_str} (must be a positive integer)")
            except ValueError:
                logger.warning(f"Invalid CLIPBOARD_CLEAR_DELAY value: {clear_delay_str} (must be a valid integer)")
        
        # Notification settings
        notifications_str = os.getenv("ENABLE_NOTIFICATIONS")
        if notifications_str and notifications_str.lower() == "true":
            self.config["notifications"]["enable"] = True
        elif notifications_str and notifications_str.lower() == "false":
            self.config["notifications"]["enable"] = False
            
        sound_str = os.getenv("NOTIFICATION_SOUND")
        if sound_str and sound_str.lower() == "true":
            self.config["notifications"]["sound"] = True
        elif sound_str and sound_str.lower() == "false":
            self.config["notifications"]["sound"] = False
        
        # Shortcut settings
        global_shortcut = os.getenv("GLOBAL_SHORTCUT")
        if global_shortcut:
            self.config["shortcuts"]["global"] = global_shortcut

    def _load_api_keys(self) -> Dict[str, Dict[str, str]]:
        """Load API keys from the secure api_keys.json file."""
        api_keys: Dict[str, Dict[str, str]] = {}
        
        # Add debug logging to show the exact path being used
        logger.debug(f"Attempting to load API keys from: {self.api_keys_file}")
        logger.debug(f"Full absolute path: {os.path.abspath(self.api_keys_file)}")
        
        if self.api_keys_file.exists():
            try:
                with open(self.api_keys_file, 'r') as f:
                    api_keys = json.load(f)
                    logger.info(f"Loaded API keys from {self.api_keys_file}")
                    # Debug: Print providers found (without showing actual keys)
                    providers = list(api_keys.keys())
                    logger.debug(f"Found API providers: {providers}")
                    if "openai" in api_keys:
                        has_key = bool(api_keys["openai"].get("api_key"))
                        logger.debug(f"OpenAI API key found: {has_key}")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading API keys: {e}")
        else:
            # Create default empty API keys file with proper structure if it doesn't exist
            default_api_keys: Dict[str, Dict[str, str]] = {
                "openai": {"api_key": ""},
                "anthropic": {"api_key": ""},
                "google": {"api_key": "", "project_id": ""},
                "openrouter": {"api_key": ""},
                "perplexity": {"api_key": ""},
                "elevenlabs": {"api_key": ""},
                "local": {"api_key": "", "model_path": ""}
            }
            with open(self.api_keys_file, 'w') as f:
                json.dump(default_api_keys, f, indent=2)
            # Set restrictive permissions
            os.chmod(self.api_keys_file, 0o600)
            logger.info(f"Created empty API keys file at {self.api_keys_file}")
            api_keys = default_api_keys
            
        # Override with environment variables if provided (for development/testing)
        # This section handles both older style env vars and newer structured ones
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            if "openai" not in api_keys:
                api_keys["openai"] = {}
            api_keys["openai"]["api_key"] = openai_key
            
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            if "anthropic" not in api_keys:
                api_keys["anthropic"] = {}
            api_keys["anthropic"]["api_key"] = anthropic_key
            
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            if "google" not in api_keys:
                api_keys["google"] = {}
            api_keys["google"]["api_key"] = google_key
            
        google_project = os.getenv("GOOGLE_PROJECT_ID")
        if google_project:
            if "google" not in api_keys:
                api_keys["google"] = {}
            api_keys["google"]["project_id"] = google_project
            
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            if "openrouter" not in api_keys:
                api_keys["openrouter"] = {}
            api_keys["openrouter"]["api_key"] = openrouter_key
            
        perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        if perplexity_key:
            if "perplexity" not in api_keys:
                api_keys["perplexity"] = {}
            api_keys["perplexity"]["api_key"] = perplexity_key
            
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        if elevenlabs_key:
            if "elevenlabs" not in api_keys:
                api_keys["elevenlabs"] = {}
            api_keys["elevenlabs"]["api_key"] = elevenlabs_key
            
        return api_keys

    def _merge_config(self, user_config: Dict[str, Any]) -> None:
        """Recursively merge user configuration into the default configuration."""
        for key, value in user_config.items():
            if isinstance(value, dict) and key in self.config and isinstance(self.config[key], dict):
                self._merge_config_dict(self.config[key], value)
            else:
                self.config[key] = value

    def _merge_config_dict(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Helper method to recursively merge dictionaries."""
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._merge_config_dict(target[key], value)
            else:
                target[key] = value

    def _configure_logging(self) -> None:
        """Configure logging based on loaded configuration."""
        log_level_str = self.config["app"]["log_level"]
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        logger.setLevel(log_level)
        logger.debug("Logging configured with level: %s", log_level_str)

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value by section and key."""
        try:
            return self.config[section][key]
        except KeyError:
            logger.warning(f"Configuration value not found: {section}.{key}, using default: {default}")
            return default

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get an API key for the specified provider."""
        logger.debug(f"Looking for API key for provider: {provider}")
        logger.debug(f"API keys structure contains providers: {list(self.api_keys.keys())}")
        
        provider_config = self.api_keys.get(provider, {})
        api_key = provider_config.get("api_key")
        
        if not api_key:
            logger.warning(f"API key not found for provider: {provider}")
        else:
            # Don't log the actual key, just that we found it
            logger.debug(f"API key found for provider: {provider}")
            
        return api_key
        
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get the complete configuration for a provider, including API keys and additional settings."""
        provider_config = self.api_keys.get(provider, {})
        model_config = self.config.get("model", {}).get(provider, {})
        # Merge model configuration with provider API configuration
        # Note: We don't include the API key in the model config
        result = {**model_config}
        for key, value in provider_config.items():
            if key != "api_key":  # Don't include the API key directly
                result[key] = value
        return result

    def save(self) -> None:
        """Save current configuration to config.json."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_file}")
        except IOError as e:
            logger.error(f"Error saving configuration: {e}")

    def save_api_key(self, provider: str, api_key: str, additional_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Save an API key and optional additional configuration to the secure api_keys.json file.
        
        Args:
            provider: The provider name (e.g., 'openai', 'anthropic')
            api_key: The API key string
            additional_config: Optional dictionary with additional provider-specific configuration
        """
        if provider not in self.api_keys:
            self.api_keys[provider] = {}
            
        self.api_keys[provider]["api_key"] = api_key
        
        # Add any additional configuration
        if additional_config:
            for key, value in additional_config.items():
                self.api_keys[provider][key] = value
        
        try:
            with open(self.api_keys_file, 'w') as f:
                json.dump(self.api_keys, f, indent=2)
            # Ensure restrictive permissions
            os.chmod(self.api_keys_file, 0o600)
            logger.info(f"Saved API key and configuration for {provider}")
        except IOError as e:
            logger.error(f"Error saving API key: {e}")
            
    def get_available_models(self) -> Dict[str, bool]:
        """
        Get a dictionary of available models based on API key availability.
        
        Returns:
            A dictionary with provider names as keys and boolean values 
            indicating whether a valid API key exists for that provider.
        """
        return {
            provider: bool(self.get_api_key(provider))
            for provider in self.api_keys.keys()
        }
        
    def get_model_details(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed model configuration for all providers or a specific provider.
        
        Args:
            provider: Optional provider name to get specific details
            
        Returns:
            Dictionary with model configurations
        """
        if provider:
            return self.config.get("model", {}).get(provider, {})
        else:
            return self.config.get("model", {})


# Create a singleton instance
config = Config()