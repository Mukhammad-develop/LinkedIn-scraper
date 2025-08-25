"""
Step 6: Configuration Management System
Centralized configuration with environment variables, profiles, and validation
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import logging
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    """Browser configuration settings"""
    headless: bool = True
    timeout: int = 30
    window_size: tuple = (1920, 1080)
    user_agent: Optional[str] = None
    disable_images: bool = True
    disable_javascript: bool = False
    page_load_strategy: str = "normal"  # normal, eager, none


@dataclass 
class ScrapingConfig:
    """Scraping behavior configuration"""
    max_retries: int = 3
    retry_delay: float = 1.0
    request_delay: tuple = (1.0, 3.0)
    max_profiles_per_session: int = 50
    session_timeout: int = 1800  # 30 minutes
    enable_quality_analysis: bool = True
    min_quality_score: float = 0.5


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 10
    requests_per_hour: int = 100
    burst_limit: int = 3
    cooldown_period: int = 300
    jitter_range: tuple = (0.5, 2.0)
    adaptive_delays: bool = True


@dataclass
class OutputConfig:
    """Output configuration"""
    default_format: str = "json"
    output_directory: str = "data"
    filename_template: str = "profile_{timestamp}"
    include_timestamp: bool = True
    compress_output: bool = False
    backup_outputs: bool = True
    max_backup_files: int = 10


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    file_path: str = "logs/scraper.log"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    console_enabled: bool = True


@dataclass
class ProxyConfig:
    """Proxy configuration"""
    enabled: bool = False
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    proxy_list: List[str] = field(default_factory=list)
    rotation_enabled: bool = False
    test_url: str = "http://httpbin.org/ip"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    enabled: bool = False
    type: str = "sqlite"  # sqlite, postgresql, mysql
    host: str = "localhost"
    port: int = 5432
    database: str = "linkedin_scraper"
    username: Optional[str] = None
    password: Optional[str] = None
    connection_pool_size: int = 5


class ConfigurationManager:
    """Centralized configuration management"""
    
    def __init__(self, config_file: Optional[str] = None, profile: str = "default"):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to configuration file
            profile: Configuration profile to use
        """
        self.config_file = config_file or "config.yaml"
        self.profile = profile
        self.config_data = {}
        self.env_prefix = "LINKEDIN_SCRAPER_"
        
        # Default configurations
        self.browser = BrowserConfig()
        self.scraping = ScrapingConfig()
        self.rate_limit = RateLimitConfig()
        self.output = OutputConfig()
        self.logging = LoggingConfig()
        self.proxy = ProxyConfig()
        self.database = DatabaseConfig()
        
        # Load configurations
        self.load_configuration()
    
    def load_configuration(self):
        """Load configuration from file and environment variables"""
        # Load from file if exists
        if os.path.exists(self.config_file):
            self._load_from_file()
        
        # Override with environment variables
        self._load_from_environment()
        
        # Apply configuration to dataclasses
        self._apply_configuration()
        
        logger.info(f"Configuration loaded from profile: {self.profile}")
    
    def _load_from_file(self):
        """Load configuration from YAML/JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    all_configs = yaml.safe_load(f)
                else:
                    all_configs = json.load(f)
            
            # Get profile-specific config
            if self.profile in all_configs:
                self.config_data = all_configs[self.profile]
            elif 'default' in all_configs:
                self.config_data = all_configs['default']
                logger.warning(f"Profile '{self.profile}' not found, using 'default'")
            else:
                self.config_data = all_configs
                
        except Exception as e:
            logger.warning(f"Could not load config file {self.config_file}: {e}")
            self.config_data = {}
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        env_mappings = {
            f"{self.env_prefix}BROWSER_HEADLESS": ("browser", "headless", bool),
            f"{self.env_prefix}BROWSER_TIMEOUT": ("browser", "timeout", int),
            f"{self.env_prefix}SCRAPING_MAX_RETRIES": ("scraping", "max_retries", int),
            f"{self.env_prefix}RATE_LIMIT_PER_MINUTE": ("rate_limit", "requests_per_minute", int),
            f"{self.env_prefix}RATE_LIMIT_PER_HOUR": ("rate_limit", "requests_per_hour", int),
            f"{self.env_prefix}OUTPUT_FORMAT": ("output", "default_format", str),
            f"{self.env_prefix}OUTPUT_DIR": ("output", "output_directory", str),
            f"{self.env_prefix}LOG_LEVEL": ("logging", "level", str),
            f"{self.env_prefix}PROXY_ENABLED": ("proxy", "enabled", bool),
            f"{self.env_prefix}PROXY_HTTP": ("proxy", "http_proxy", str),
            f"{self.env_prefix}DB_ENABLED": ("database", "enabled", bool),
            f"{self.env_prefix}DB_TYPE": ("database", "type", str),
            f"{self.env_prefix}DB_HOST": ("database", "host", str),
            f"{self.env_prefix}DB_PORT": ("database", "port", int),
        }
        
        for env_var, (section, key, var_type) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert type
                try:
                    if var_type == bool:
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif var_type == int:
                        value = int(value)
                    elif var_type == float:
                        value = float(value)
                    
                    # Set in config data
                    if section not in self.config_data:
                        self.config_data[section] = {}
                    self.config_data[section][key] = value
                    
                except ValueError as e:
                    logger.warning(f"Invalid value for {env_var}: {value} ({e})")
    
    def _apply_configuration(self):
        """Apply loaded configuration to dataclass instances"""
        # Browser configuration
        if "browser" in self.config_data:
            browser_config = self.config_data["browser"]
            for key, value in browser_config.items():
                if hasattr(self.browser, key):
                    setattr(self.browser, key, value)
        
        # Scraping configuration
        if "scraping" in self.config_data:
            scraping_config = self.config_data["scraping"]
            for key, value in scraping_config.items():
                if hasattr(self.scraping, key):
                    setattr(self.scraping, key, value)
        
        # Rate limiting configuration
        if "rate_limit" in self.config_data:
            rate_limit_config = self.config_data["rate_limit"]
            for key, value in rate_limit_config.items():
                if hasattr(self.rate_limit, key):
                    setattr(self.rate_limit, key, value)
        
        # Output configuration
        if "output" in self.config_data:
            output_config = self.config_data["output"]
            for key, value in output_config.items():
                if hasattr(self.output, key):
                    setattr(self.output, key, value)
        
        # Logging configuration
        if "logging" in self.config_data:
            logging_config = self.config_data["logging"]
            for key, value in logging_config.items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)
        
        # Proxy configuration
        if "proxy" in self.config_data:
            proxy_config = self.config_data["proxy"]
            for key, value in proxy_config.items():
                if hasattr(self.proxy, key):
                    setattr(self.proxy, key, value)
        
        # Database configuration
        if "database" in self.config_data:
            database_config = self.config_data["database"]
            for key, value in database_config.items():
                if hasattr(self.database, key):
                    setattr(self.database, key, value)
    
    def save_configuration(self, output_file: Optional[str] = None):
        """Save current configuration to file"""
        output_file = output_file or self.config_file
        
        config_dict = {
            self.profile: {
                "browser": {
                    "headless": self.browser.headless,
                    "timeout": self.browser.timeout,
                    "window_size": self.browser.window_size,
                    "user_agent": self.browser.user_agent,
                    "disable_images": self.browser.disable_images,
                    "disable_javascript": self.browser.disable_javascript,
                    "page_load_strategy": self.browser.page_load_strategy
                },
                "scraping": {
                    "max_retries": self.scraping.max_retries,
                    "retry_delay": self.scraping.retry_delay,
                    "request_delay": self.scraping.request_delay,
                    "max_profiles_per_session": self.scraping.max_profiles_per_session,
                    "session_timeout": self.scraping.session_timeout,
                    "enable_quality_analysis": self.scraping.enable_quality_analysis,
                    "min_quality_score": self.scraping.min_quality_score
                },
                "rate_limit": {
                    "requests_per_minute": self.rate_limit.requests_per_minute,
                    "requests_per_hour": self.rate_limit.requests_per_hour,
                    "burst_limit": self.rate_limit.burst_limit,
                    "cooldown_period": self.rate_limit.cooldown_period,
                    "jitter_range": self.rate_limit.jitter_range,
                    "adaptive_delays": self.rate_limit.adaptive_delays
                },
                "output": {
                    "default_format": self.output.default_format,
                    "output_directory": self.output.output_directory,
                    "filename_template": self.output.filename_template,
                    "include_timestamp": self.output.include_timestamp,
                    "compress_output": self.output.compress_output,
                    "backup_outputs": self.output.backup_outputs,
                    "max_backup_files": self.output.max_backup_files
                },
                "logging": {
                    "level": self.logging.level,
                    "format": self.logging.format,
                    "file_enabled": self.logging.file_enabled,
                    "file_path": self.logging.file_path,
                    "max_file_size": self.logging.max_file_size,
                    "backup_count": self.logging.backup_count,
                    "console_enabled": self.logging.console_enabled
                },
                "proxy": {
                    "enabled": self.proxy.enabled,
                    "http_proxy": self.proxy.http_proxy,
                    "https_proxy": self.proxy.https_proxy,
                    "proxy_list": self.proxy.proxy_list,
                    "rotation_enabled": self.proxy.rotation_enabled,
                    "test_url": self.proxy.test_url
                },
                "database": {
                    "enabled": self.database.enabled,
                    "type": self.database.type,
                    "host": self.database.host,
                    "port": self.database.port,
                    "database": self.database.database,
                    "username": self.database.username,
                    "password": self.database.password,
                    "connection_pool_size": self.database.connection_pool_size
                }
            }
        }
        
        try:
            with open(output_file, 'w') as f:
                if output_file.endswith('.yaml') or output_file.endswith('.yml'):
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get_scraper_config(self) -> Dict[str, Any]:
        """Get configuration dictionary for scraper initialization"""
        return {
            "headless": self.browser.headless,
            "timeout": self.browser.timeout,
            "max_retries": self.scraping.max_retries,
            "rate_limit_config": self.rate_limit,
            "enable_quality_analysis": self.scraping.enable_quality_analysis
        }
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get configuration dictionary for output manager"""
        return {
            "default_format": self.output.default_format,
            "output_directory": self.output.output_directory,
            "filename_template": self.output.filename_template,
            "include_timestamp": self.output.include_timestamp
        }
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate browser config
        if self.browser.timeout <= 0:
            issues.append("Browser timeout must be positive")
        
        if not isinstance(self.browser.window_size, (list, tuple)) or len(self.browser.window_size) != 2:
            issues.append("Browser window_size must be a tuple of (width, height)")
        
        # Validate scraping config
        if self.scraping.max_retries < 0:
            issues.append("Max retries cannot be negative")
        
        if self.scraping.min_quality_score < 0 or self.scraping.min_quality_score > 1:
            issues.append("Min quality score must be between 0 and 1")
        
        # Validate rate limiting
        if self.rate_limit.requests_per_minute <= 0:
            issues.append("Requests per minute must be positive")
        
        if self.rate_limit.requests_per_hour <= 0:
            issues.append("Requests per hour must be positive")
        
        if self.rate_limit.requests_per_hour < self.rate_limit.requests_per_minute:
            issues.append("Requests per hour should be >= requests per minute")
        
        # Validate output config
        if not self.output.default_format:
            issues.append("Default output format cannot be empty")
        
        valid_formats = ["json", "csv", "xlsx", "xml", "html", "yaml"]
        if self.output.default_format not in valid_formats:
            issues.append(f"Invalid output format. Must be one of: {valid_formats}")
        
        # Validate logging config
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level.upper() not in valid_log_levels:
            issues.append(f"Invalid log level. Must be one of: {valid_log_levels}")
        
        # Validate database config
        if self.database.enabled:
            valid_db_types = ["sqlite", "postgresql", "mysql"]
            if self.database.type not in valid_db_types:
                issues.append(f"Invalid database type. Must be one of: {valid_db_types}")
            
            if self.database.port <= 0 or self.database.port > 65535:
                issues.append("Database port must be between 1 and 65535")
        
        return issues
    
    def create_directories(self):
        """Create necessary directories based on configuration"""
        directories = [
            self.output.output_directory,
            os.path.dirname(self.logging.file_path) if self.logging.file_enabled else None
        ]
        
        for directory in directories:
            if directory:
                try:
                    os.makedirs(directory, exist_ok=True)
                    logger.debug(f"Created directory: {directory}")
                except Exception as e:
                    logger.warning(f"Could not create directory {directory}: {e}")
    
    def setup_logging(self):
        """Setup logging based on configuration"""
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Set log level
        log_level = getattr(logging, self.logging.level.upper(), logging.INFO)
        root_logger.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(self.logging.format)
        
        # Console handler
        if self.logging.console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if self.logging.file_enabled:
            try:
                from logging.handlers import RotatingFileHandler
                
                # Ensure log directory exists
                os.makedirs(os.path.dirname(self.logging.file_path), exist_ok=True)
                
                file_handler = RotatingFileHandler(
                    self.logging.file_path,
                    maxBytes=self.logging.max_file_size,
                    backupCount=self.logging.backup_count
                )
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
                
            except Exception as e:
                logger.warning(f"Could not setup file logging: {e}")
    
    def get_environment_template(self) -> str:
        """Generate environment variables template"""
        template = f"""# LinkedIn Scraper Configuration
# Copy this file to .env and modify as needed

# Browser Settings
{self.env_prefix}BROWSER_HEADLESS=true
{self.env_prefix}BROWSER_TIMEOUT=30

# Scraping Settings  
{self.env_prefix}SCRAPING_MAX_RETRIES=3

# Rate Limiting
{self.env_prefix}RATE_LIMIT_PER_MINUTE=10
{self.env_prefix}RATE_LIMIT_PER_HOUR=100

# Output Settings
{self.env_prefix}OUTPUT_FORMAT=json
{self.env_prefix}OUTPUT_DIR=data

# Logging
{self.env_prefix}LOG_LEVEL=INFO

# Proxy Settings
{self.env_prefix}PROXY_ENABLED=false
{self.env_prefix}PROXY_HTTP=
{self.env_prefix}PROXY_HTTPS=

# Database Settings
{self.env_prefix}DB_ENABLED=false
{self.env_prefix}DB_TYPE=sqlite
{self.env_prefix}DB_HOST=localhost
{self.env_prefix}DB_PORT=5432
"""
        return template


# Global configuration instance
config = None

def get_config(config_file: Optional[str] = None, profile: str = "default") -> ConfigurationManager:
    """Get global configuration instance"""
    global config
    if config is None:
        config = ConfigurationManager(config_file, profile)
    return config

def initialize_config(config_file: Optional[str] = None, profile: str = "default"):
    """Initialize global configuration"""
    global config
    config = ConfigurationManager(config_file, profile)
    
    # Validate configuration
    issues = config.validate_configuration()
    if issues:
        logger.warning(f"Configuration issues found: {issues}")
    
    # Create directories
    config.create_directories()
    
    # Setup logging
    config.setup_logging()
    
    logger.info("Configuration initialized successfully") 