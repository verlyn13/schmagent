"""
Configuration manager for Schmagent.

This module implements a hierarchical configuration system with the following sources
(in order of increasing precedence):

1. DEFAULT VALUES: Defined in Pydantic models as field defaults
   - These provide sensible defaults for all configuration options
   - Located in the Pydantic model classes (AppSettings, ModelSettings, etc.)

2. FILE-BASED CONFIGURATION: Loaded from JSON files
   - Main config: ~/.config/schmagent/config.json (or CONFIG_PATH env var)
   - API keys: ~/.secrets/schmagent/api_keys.json (or SECRETS_PATH + API_KEYS_FILE env vars)
   - These override the default values

3. ENVIRONMENT VARIABLES: Override both defaults and file-based config
   - Environment variables take highest precedence
   - Naming convention: UPPERCASE with underscores (e.g., OPENAI_API_KEY)
   - Boolean values: "true"/"false" (case-insensitive)
   - Loaded from .env file (if present) and actual environment variables

Configuration is validated using Pydantic models to ensure type safety and consistency.
The system is designed to be secure, with API keys stored separately from general configuration.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, IO, Union, List, Literal
from os import PathLike

from pydantic import BaseModel, Field, model_validator, field_validator

try:
    from dotenv import load_dotenv
except ImportError:
    # For type checking only
    def load_dotenv(
        dotenv_path: Optional[Union[str, PathLike[str]]] = None,
        stream: Optional[IO[str]] = None,
        verbose: bool = False,
        override: bool = False,
        interpolate: bool = True,
        encoding: Optional[str] = None
    ) -> bool:
        """Stub for type checking if dotenv is not available."""
        return False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for configuration sections
class AppSettings(BaseModel):
    """Application settings."""
    name: str = "Schmagent"
    debug: bool = False
    log_level: str = "INFO"


class ModelProviderSettings(BaseModel):
    """Base settings for model providers."""
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    cache_enabled: bool = True
    timeout: int = 60


class OpenAISettings(ModelProviderSettings):
    """OpenAI-specific settings."""
    model: str = "gpt-4-turbo"


class AnthropicSettings(ModelProviderSettings):
    """Anthropic-specific settings."""
    model: str = "claude-3-5-sonnet"
    max_tokens: int = 4096


class GoogleSettings(ModelProviderSettings):
    """Google-specific settings."""
    model: str = "gemini-pro"


class OpenRouterSettings(ModelProviderSettings):
    """OpenRouter-specific settings."""
    model: str = "openai/gpt-4-turbo"


class PerplexitySettings(ModelProviderSettings):
    """Perplexity-specific settings."""
    model: str = "llama-3-sonar-large-32k"


class ElevenLabsSettings(BaseModel):
    """ElevenLabs-specific settings."""
    voice_id: str = "premade/adam"
    model: str = "eleven_turbo_v2"
    cache_enabled: bool = True


class LocalModelSettings(BaseModel):
    """Local model settings."""
    model_path: Optional[str] = None
    model_type: str = "llama"
    cache_enabled: bool = True
    context_window: int = 4096


class ModelSettings(BaseModel):
    """Model settings."""
    default: str = "openai"
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    anthropic: AnthropicSettings = Field(default_factory=AnthropicSettings)
    google: GoogleSettings = Field(default_factory=GoogleSettings)
    openrouter: OpenRouterSettings = Field(default_factory=OpenRouterSettings)
    perplexity: PerplexitySettings = Field(default_factory=PerplexitySettings)
    elevenlabs: ElevenLabsSettings = Field(default_factory=ElevenLabsSettings)
    local: LocalModelSettings = Field(default_factory=LocalModelSettings)


class UISettings(BaseModel):
    """UI settings."""
    theme: str = "system"
    window_width: int = 800
    window_height: int = 600
    code_highlighting: bool = True
    enable_screenshots: bool = True


class SessionSettings(BaseModel):
    """Session settings."""
    persistence: bool = True
    max_history_sessions: int = 10
    message_history_limit: int = 50


class SecuritySettings(BaseModel):
    """Security settings."""
    api_key_encryption: bool = True
    clipboard_auto_clear: bool = False
    clipboard_clear_delay: int = 60

    @field_validator('clipboard_clear_delay')
    @classmethod
    def validate_clear_delay(cls, v: int) -> int:
        """Validate that clipboard_clear_delay is positive."""
        if v <= 0:
            raise ValueError("clipboard_clear_delay must be a positive integer")
        return v


class NotificationSettings(BaseModel):
    """Notification settings."""
    enable: bool = True
    sound: bool = True


class ShortcutSettings(BaseModel):
    """Shortcut settings."""
    global_shortcut: str = Field(default="<Super>s", alias="global")


class APIKeySettings(BaseModel):
    """API key settings for a provider."""
    api_key: str = ""


class GoogleAPIKeySettings(APIKeySettings):
    """Google-specific API key settings."""
    project_id: str = ""


class LocalAPIKeySettings(APIKeySettings):
    """Local model-specific API key settings."""
    model_path: str = ""


class APIKeys(BaseModel):
    """API keys for all providers."""
    openai: APIKeySettings = Field(default_factory=APIKeySettings)
    anthropic: APIKeySettings = Field(default_factory=APIKeySettings)
    google: GoogleAPIKeySettings = Field(default_factory=GoogleAPIKeySettings)
    openrouter: APIKeySettings = Field(default_factory=APIKeySettings)
    perplexity: APIKeySettings = Field(default_factory=APIKeySettings)
    elevenlabs: APIKeySettings = Field(default_factory=APIKeySettings)
    local: LocalAPIKeySettings = Field(default_factory=LocalAPIKeySettings)


class Settings(BaseModel):
    """Main settings class combining all sections."""
    app: AppSettings = Field(default_factory=AppSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    ui: UISettings = Field(default_factory=UISettings)
    session: SessionSettings = Field(default_factory=SessionSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    shortcuts: ShortcutSettings = Field(default_factory=lambda: ShortcutSettings())


class Config:
    """Configuration manager for Schmagent application."""
    
    def __init__(self):
        """
        Initialize configuration with default values, then load from files and environment variables.
        
        Configuration loading follows this order of precedence (later sources override earlier ones):
        1. Default values from Pydantic models
        2. Configuration files (config.json and api_keys.json)
        3. Environment variables (including from .env file)
        """
        # Load .env file if it exists (ENVIRONMENT VARIABLES SOURCE)
        load_dotenv()
        
        # Set up paths (can be overridden by environment variables)
        config_path_default = os.path.expanduser("~/.config/schmagent")
        data_path_default = os.path.expanduser("~/.local/share/schmagent")
        secrets_path_default = os.path.expanduser("~/.secrets/schmagent")
        
        # Environment variables can override default paths
        self.config_path = Path(os.getenv("CONFIG_PATH", config_path_default))
        self.data_path = Path(os.getenv("DATA_PATH", data_path_default))
        self.secrets_path = Path(os.getenv("SECRETS_PATH", secrets_path_default))
        
        # Ensure paths exist
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.secrets_path.mkdir(parents=True, exist_ok=True)
        
        # Set permissions for secrets directory
        os.chmod(self.secrets_path, 0o700)
        
        # Define file paths
        self.config_file = self.config_path / "config.json"
        api_keys_filename = os.getenv("API_KEYS_FILE", "api_keys.json")
        self.api_keys_file = self.secrets_path / api_keys_filename
        
        # Initialize configuration
        # 1. DEFAULT VALUES SOURCE: Start with default values from Pydantic models
        self.settings = Settings()
        
        # 2. FILE-BASED CONFIGURATION SOURCE: Load from config.json
        self._load_config_file()
        
        # 3. ENVIRONMENT VARIABLES SOURCE: Override with environment variables
        self._load_environment_variables()
        
        # Handle API keys separately for security
        # - Default values from APIKeys model
        # - File-based values from api_keys.json
        # - Environment variable overrides
        self.api_keys = self._load_api_keys()
        
        # For backward compatibility
        self.config = self._to_dict(self.settings)
        
        # Set log level after configuration is loaded
        self._configure_logging()

    def _load_config_file(self) -> None:
        """
        Load configuration from config.json if it exists.
        
        This is the FILE-BASED CONFIGURATION SOURCE that overrides default values
        but can be overridden by environment variables.
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as file_handle:
                    user_config = json.load(file_handle)
                    # Update settings with user config
                    self.settings = self._update_from_dict(self.settings, user_config)
                    logger.info("Loaded configuration from %s", self.config_file)
            except (json.JSONDecodeError, IOError) as error:
                logger.error("Error loading config file: %s", error)
        else:
            # Create empty config file if it doesn't exist
            with open(self.config_file, 'w', encoding='utf-8') as file_handle:
                json.dump({}, file_handle, indent=2)
            logger.info("Created empty configuration file at %s", self.config_file)

    def _update_from_dict(self, settings: Any, data: Dict[str, Any]) -> Any:
        """
        Update settings from a dictionary, handling nested structures.
        
        Args:
            settings: The settings object to update
            data: Dictionary with new values
            
        Returns:
            Updated settings object
        """
        if isinstance(settings, BaseModel):
            # Create a copy of the current model
            model_copy = settings.model_copy()
            
            # Update with new data
            for key, value in data.items():
                if hasattr(model_copy, key):
                    current_value = getattr(model_copy, key)
                    if isinstance(value, dict) and isinstance(current_value, (BaseModel, dict)):
                        # Recursively update nested models/dicts
                        setattr(model_copy, key, self._update_from_dict(current_value, value))
                    else:
                        # Direct update for simple values
                        setattr(model_copy, key, value)
            
            return model_copy
        elif isinstance(settings, dict):
            # Handle dictionary updates
            result = settings.copy()
            for key, value in data.items():
                if key in result and isinstance(value, dict) and isinstance(result[key], (dict, BaseModel)):
                    result[key] = self._update_from_dict(result[key], value)
                else:
                    result[key] = value
            return result
        else:
            # For other types, just return the new value
            return data

    def _to_dict(self, obj: Any) -> Any:
        """
        Convert Pydantic models to dictionaries recursively.
        
        Args:
            obj: Object to convert
            
        Returns:
            Dictionary representation
        """
        if isinstance(obj, BaseModel):
            return {k: self._to_dict(v) for k, v in obj.model_dump().items()}
        elif isinstance(obj, dict):
            return {k: self._to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._to_dict(item) for item in obj]
        else:
            return obj

    def _get_env_value(self, var_name: str, convert_func=None, default=None, config_path=None):
        """
        Helper function to get and convert environment variables.
        
        Args:
            var_name: Name of the environment variable
            convert_func: Optional function to convert the value (str, int, float, etc.)
            default: Default value if environment variable is not set or conversion fails
            config_path: List of nested keys to locate the config value (e.g., ["ui", "window_width"])
            
        Returns:
            The converted value or default
        """
        val = os.getenv(var_name)
        if val is None:
            return default
            
        if convert_func is None:
            return val
            
        try:
            return convert_func(val)
        except ValueError:
            logger.warning("Invalid value for %s: %s", var_name, val)
            return default
            
    def _get_bool_env_value(self, var_name: str, default=None, config_path=None):
        """
        Helper function specifically for boolean environment variables.
        
        Args:
            var_name: Name of the environment variable
            default: Default value if environment variable is not set
            config_path: List of nested keys to locate the config value
            
        Returns:
            True if value is "true" (case insensitive), False if "false", or default
        """
        val = os.getenv(var_name)
        if val is None:
            return default
            
        if val.lower() == "true":
            return True
        elif val.lower() == "false":
            return False
        else:
            logger.warning("Invalid boolean value for %s: %s", var_name, val)
            return default
            
    def _set_config_value(self, config_path: List[str], value: Any) -> None:
        """
        Set a value in the settings object.
        
        Args:
            config_path: List of keys to navigate the nested structure
            value: Value to set
        """
        if not config_path or value is None:
            return
            
        # Start with the settings object
        current = self.settings
        
        # Navigate to the parent object
        for key in config_path[:-1]:
            if not hasattr(current, key):
                logger.warning(f"Config path not found: {key} in {config_path}")
                return
            current = getattr(current, key)
            
        # Set the value on the parent object
        last_key = config_path[-1]
        if hasattr(current, last_key):
            try:
                setattr(current, last_key, value)
                # Update the dictionary representation
                self.config = self._to_dict(self.settings)
            except Exception as e:
                logger.warning(f"Failed to set config value {last_key}: {e}")
        else:
            logger.warning(f"Config key not found: {last_key} in {config_path}")

    def _load_environment_variables(self) -> None:
        """
        Load configuration from environment variables.
        
        This is the ENVIRONMENT VARIABLES SOURCE that takes highest precedence,
        overriding both default values and file-based configuration.
        
        Environment variables can come from:
        - The .env file (loaded by python-dotenv)
        - The actual environment variables set in the system
        """
        # Define a mapping of environment variables to configuration paths
        # Format: "ENV_VAR_NAME": (["path", "to", "config"], converter_function)
        env_var_mapping = {
            # App settings
            "APP_NAME": (["app", "name"], None),
            "DEBUG": (["app", "debug"], self._get_bool_env_value),
            "LOG_LEVEL": (["app", "log_level"], None),
            
            # Model settings
            "DEFAULT_MODEL": (["model", "default"], None),
            "OPENAI_MODEL": (["model", "openai", "model"], None),
            "OPENAI_TEMPERATURE": (["model", "openai", "temperature"], lambda x: float(x)),
            "OPENAI_MAX_TOKENS": (["model", "openai", "max_tokens"], lambda x: int(x)),
            
            # UI settings
            "THEME": (["ui", "theme"], None),
            "WINDOW_WIDTH": (["ui", "window_width"], lambda x: int(x)),
            "WINDOW_HEIGHT": (["ui", "window_height"], lambda x: int(x)),
            "CODE_HIGHLIGHTING": (["ui", "code_highlighting"], self._get_bool_env_value),
            "ENABLE_SCREENSHOTS": (["ui", "enable_screenshots"], self._get_bool_env_value),
            
            # Session settings
            "SESSION_PERSISTENCE": (["session", "persistence"], self._get_bool_env_value),
            "MAX_HISTORY_SESSIONS": (["session", "max_history_sessions"], lambda x: int(x)),
            "MESSAGE_HISTORY_LIMIT": (["session", "message_history_limit"], lambda x: int(x)),
            
            # Security settings
            "API_KEY_ENCRYPTION": (["security", "api_key_encryption"], self._get_bool_env_value),
            "CLIPBOARD_AUTO_CLEAR": (["security", "clipboard_auto_clear"], self._get_bool_env_value),
            
            # Notification settings
            "ENABLE_NOTIFICATIONS": (["notifications", "enable"], self._get_bool_env_value),
            "NOTIFICATION_SOUND": (["notifications", "sound"], self._get_bool_env_value),
        }
        
        # Process each environment variable
        for env_var, (config_path, converter) in env_var_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if converter:
                        value = converter(value)
                    self._set_config_value(config_path, value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid value for {env_var}: {value} - {str(e)}")
        
        # Special case for clipboard clear delay with additional validation
        clear_delay_str = os.getenv("CLIPBOARD_CLEAR_DELAY")
        if clear_delay_str:
            try:
                # Strip whitespace and comments
                clean_value = clear_delay_str.split('#')[0].strip()
                clear_delay = int(clean_value)
                if clear_delay > 0:
                    self._set_config_value(["security", "clipboard_clear_delay"], clear_delay)
                    logger.debug("Set clipboard_clear_delay to %s", clear_delay)
                else:
                    msg = "Invalid CLIPBOARD_CLEAR_DELAY value: %s (must be a positive integer)"
                    logger.warning(msg, clear_delay_str)
            except ValueError:
                msg = "Invalid CLIPBOARD_CLEAR_DELAY value: %s (must be a valid integer)"
                logger.warning(msg, clear_delay_str)
        
        # Special case for global shortcut (due to alias field)
        global_shortcut = os.getenv("GLOBAL_SHORTCUT")
        if global_shortcut:
            # Handle the alias field specially
            if hasattr(self.settings.shortcuts, "global_shortcut"):
                self.settings.shortcuts.global_shortcut = global_shortcut
                # Update the dictionary representation
                self.config = self._to_dict(self.settings)

    def _load_api_keys(self) -> APIKeys:
        """
        Load API keys from the secure api_keys.json file and environment variables.
        
        This follows the same configuration hierarchy:
        1. DEFAULT VALUES: Empty strings from APIKeys model
        2. FILE-BASED CONFIGURATION: From api_keys.json
        3. ENVIRONMENT VARIABLES: Override both defaults and file-based config
        """
        # 1. DEFAULT VALUES SOURCE: Start with default values from APIKeys model
        api_keys = APIKeys()
        
        # Add debug logging to show the exact path being used
        logger.debug("Attempting to load API keys from: %s", self.api_keys_file)
        logger.debug("Full absolute path: %s", os.path.abspath(self.api_keys_file))
        
        # 2. FILE-BASED CONFIGURATION SOURCE: Load from api_keys.json
        if self.api_keys_file.exists():
            try:
                with open(self.api_keys_file, 'r', encoding='utf-8') as file_handle:
                    api_keys_dict = json.load(file_handle)
                    # Update API keys from file
                    api_keys = self._update_from_dict(api_keys, api_keys_dict)
                    logger.info("Loaded API keys from %s", self.api_keys_file)
                    # Debug: Print providers found (without showing actual keys)
                    providers = list(api_keys_dict.keys())
                    logger.debug("Found API providers: %s", providers)
                    if "openai" in api_keys_dict:
                        has_key = bool(api_keys_dict["openai"].get("api_key"))
                        logger.debug("OpenAI API key found: %s", has_key)
            except (json.JSONDecodeError, IOError) as error:
                logger.error("Error loading API keys: %s", error)
        else:
            # Create default empty API keys file with proper structure if it doesn't exist
            default_api_keys = {
                "openai": {"api_key": ""},
                "anthropic": {"api_key": ""},
                "google": {"api_key": "", "project_id": ""},
                "openrouter": {"api_key": ""},
                "perplexity": {"api_key": ""},
                "elevenlabs": {"api_key": ""},
                "local": {"api_key": "", "model_path": ""}
            }
            with open(self.api_keys_file, 'w', encoding='utf-8') as file_handle:
                json.dump(default_api_keys, file_handle, indent=2)
            # Set restrictive permissions
            os.chmod(self.api_keys_file, 0o600)
            logger.info("Created empty API keys file at %s", self.api_keys_file)
        
        # 3. ENVIRONMENT VARIABLES SOURCE: Override with environment variables
        # Define a mapping of environment variables to API key fields
        env_var_mapping = {
            "OPENAI_API_KEY": ("openai", "api_key"),
            "ANTHROPIC_API_KEY": ("anthropic", "api_key"),
            "GOOGLE_API_KEY": ("google", "api_key"),
            "GOOGLE_PROJECT_ID": ("google", "project_id"),
            "OPENROUTER_API_KEY": ("openrouter", "api_key"),
            "PERPLEXITY_API_KEY": ("perplexity", "api_key"),
            "ELEVENLABS_API_KEY": ("elevenlabs", "api_key")
        }
        
        # Process each environment variable
        for env_var, (provider, field) in env_var_mapping.items():
            value = os.getenv(env_var)
            if value:
                provider_obj = getattr(api_keys, provider, None)
                if provider_obj and hasattr(provider_obj, field):
                    setattr(provider_obj, field, value)
                    logger.debug(f"Set {provider}.{field} from environment variable {env_var}")
        
        return api_keys

    def _configure_logging(self) -> None:
        """Configure logging based on loaded configuration."""
        log_level_str = self.settings.app.log_level
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        logger.setLevel(log_level)
        logger.debug("Logging configured with level: %s", log_level_str)

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value by section and key."""
        try:
            section_obj = getattr(self.settings, section, None)
            if section_obj is None:
                logger.warning("Configuration section not found: %s, using default: %s",
                               section, default)
                return default
                
            return getattr(section_obj, key, default)
        except (AttributeError, KeyError):
            logger.warning("Configuration value not found: %s.%s, using default: %s",
                           section, key, default)
            return default

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get an API key for the specified provider."""
        logger.debug("Looking for API key for provider: %s", provider)
        
        try:
            provider_obj = getattr(self.api_keys, provider, None)
            if provider_obj is None:
                logger.warning("API provider not found: %s", provider)
                return None
                
            api_key = provider_obj.api_key
            
            if not api_key:
                logger.warning("API key not found for provider: %s", provider)
            else:
                # Don't log the actual key, just that we found it
                logger.debug("API key found for provider: %s", provider)
            
            return api_key
        except AttributeError:
            logger.warning("API provider not found: %s", provider)
            return None
        
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get the complete configuration for a provider, including API keys and additional settings."""
        try:
            # Get model configuration
            model_config = {}
            if hasattr(self.settings.model, provider):
                provider_model = getattr(self.settings.model, provider)
                model_config = self._to_dict(provider_model)
            
            # Get API key configuration (excluding the actual API key)
            provider_config = {}
            if hasattr(self.api_keys, provider):
                provider_obj = getattr(self.api_keys, provider)
                provider_dict = self._to_dict(provider_obj)
                # Don't include the API key directly
                provider_config = {k: v for k, v in provider_dict.items() if k != "api_key"}
            
            # Merge configurations
            result = {**model_config, **provider_config}
            return result
        except AttributeError:
            logger.warning("Provider configuration not found: %s", provider)
            return {}

    def save(self) -> None:
        """Save current configuration to config.json."""
        try:
            # Convert settings to dictionary
            config_dict = self._to_dict(self.settings)
            
            with open(self.config_file, 'w', encoding='utf-8') as file_handle:
                json.dump(config_dict, file_handle, indent=2)
            logger.info("Saved configuration to %s", self.config_file)
        except IOError as error:
            logger.error("Error saving configuration: %s", error)

    def save_api_key(self, provider: str, api_key: str, 
                     additional_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Save an API key and optional additional configuration to the secure api_keys.json file.
        
        Args:
            provider: The provider name (e.g., 'openai', 'anthropic')
            api_key: The API key string
            additional_config: Optional dictionary with additional provider-specific configuration
        """
        try:
            # Get the provider object
            if hasattr(self.api_keys, provider):
                provider_obj = getattr(self.api_keys, provider)
                
                # Set the API key
                provider_obj.api_key = api_key
                
                # Add any additional configuration
                if additional_config:
                    for key, value in additional_config.items():
                        if hasattr(provider_obj, key):
                            setattr(provider_obj, key, value)
                
                # Save to file
                api_keys_dict = self._to_dict(self.api_keys)
                
                with open(self.api_keys_file, 'w', encoding='utf-8') as file_handle:
                    json.dump(api_keys_dict, file_handle, indent=2)
                # Ensure restrictive permissions
                os.chmod(self.api_keys_file, 0o600)
                logger.info("Saved API key and configuration for %s", provider)
            else:
                logger.error("Unknown provider: %s", provider)
        except IOError as error:
            logger.error("Error saving API key: %s", error)
            
    def get_available_models(self) -> Dict[str, bool]:
        """
        Get a dictionary of available models based on API key availability.
        
        Returns:
            A dictionary with provider names as keys and boolean values 
            indicating whether a valid API key exists for that provider.
        """
        return {
            provider: bool(self.get_api_key(provider))
            for provider in self._to_dict(self.api_keys).keys()
        }
        
    def get_model_details(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed model configuration for all providers or a specific provider.
        
        Args:
            provider: Optional provider name to get specific details
            
        Returns:
            Dictionary with model configurations
        """
        model_config = self._to_dict(self.settings.model)
        if provider:
            return dict(model_config.get(provider, {}))
        return dict(model_config)


# Create a singleton instance
config = Config()
