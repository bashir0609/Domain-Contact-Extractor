"""
Configuration management for Email Finder Pro
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AppConfig:
    """Centralized configuration management"""
    
    # API Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL: str = "perplexity/llama-3-sonar-large-online"
    
    # Rate Limiting
    RATE_LIMIT_DELAY: float = float(os.getenv("RATE_LIMIT_DELAY", "2.0"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Scraping Configuration
    SELENIUM_TIMEOUT: int = int(os.getenv("SELENIUM_TIMEOUT", "10"))
    PAGE_LOAD_DELAY: float = float(os.getenv("PAGE_LOAD_DELAY", "2.0"))
    MAX_EMAILS_PER_SITE: int = int(os.getenv("MAX_EMAILS_PER_SITE", "100"))
    
    # Email Validation
    EXCLUDED_DOMAINS: set = {
        "example.com", "test.com", "domain.com", "yoursite.com",
        "sentry.io", "google.com", "facebook.com", "twitter.com",
        "linkedin.com", "instagram.com", "youtube.com", "wordpress.com",
        "github.com", "stackoverflow.com", "reddit.com"
    }
    
    # User Agent for requests
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "app.log")
    
    # Feature Flags
    ENABLE_SITEMAP_SEARCH: bool = os.getenv("ENABLE_SITEMAP_SEARCH", "true").lower() == "true"
    ENABLE_DEEP_SEARCH: bool = os.getenv("ENABLE_DEEP_SEARCH", "true").lower() == "true"
    ENABLE_EMAIL_CATEGORIZATION: bool = os.getenv("ENABLE_EMAIL_CATEGORIZATION", "true").lower() == "true"
    
    # Security Settings
    RESTRICT_PRIVATE_IPS: bool = os.getenv("RESTRICT_PRIVATE_IPS", "true").lower() == "true"
    MAX_URL_LENGTH: int = int(os.getenv("MAX_URL_LENGTH", "2048"))
    
    @classmethod
    def get_chrome_options(cls) -> Dict[str, Any]:
        """Get Chrome options for Selenium"""
        return {
            "headless": True,
            "disable_gpu": True,
            "no_sandbox": True,
            "disable_dev_shm_usage": True,
            "disable_blink_features": "AutomationControlled",
            "user_agent": cls.USER_AGENT,
            "window_size": "1920,1080"
        }
    
    @classmethod
    def get_request_headers(cls) -> Dict[str, str]:
        """Get standard request headers"""
        return {
            "User-Agent": cls.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    @classmethod
    def validate_config(cls) -> tuple[bool, list[str]]:
        """Validate configuration and return any errors"""
        errors = []
        
        if not cls.OPENROUTER_API_KEY:
            errors.append("OPENROUTER_API_KEY is required")
        
        if cls.RATE_LIMIT_DELAY < 0:
            errors.append("RATE_LIMIT_DELAY must be >= 0")
        
        if cls.MAX_RETRIES < 1:
            errors.append("MAX_RETRIES must be >= 1")
        
        if cls.REQUEST_TIMEOUT < 1:
            errors.append("REQUEST_TIMEOUT must be >= 1")
        
        return len(errors) == 0, errors

class EmailPatterns:
    """Email extraction and validation patterns"""
    
    # Basic email regex
    EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Common fake email patterns to exclude
    FAKE_PATTERNS = [
        r'noreply', r'no-reply', r'donotreply', r'test@',
        r'admin@example', r'user@example', r'contact@example',
        r'webmaster@example', r'info@example', r'@example\.com',
        r'sample@', r'demo@', r'placeholder@'
    ]
    
    # Email categorization patterns
    CATEGORY_PATTERNS = {
        'sales': [
            r'sales', r'business', r'commercial', r'revenue',
            r'partnerships', r'enterprise', r'accounts'
        ],
        'support': [
            r'support', r'help', r'service', r'assistance',
            r'helpdesk', r'care', r'ticket'
        ],
        'info': [
            r'info', r'contact', r'hello', r'general',
            r'inquiry', r'questions'
        ],
        'admin': [
            r'admin', r'webmaster', r'postmaster', r'system',
            r'technical', r'it', r'tech'
        ],
        'marketing': [
            r'marketing', r'promo', r'newsletter', r'campaign',
            r'social', r'media', r'pr'
        ],
        'hr': [
            r'hr', r'human', r'resources', r'recruitment',
            r'careers', r'jobs', r'talent'
        ]
    }

class UIConfig:
    """UI/UX configuration settings"""
    
    # Streamlit page config
    PAGE_TITLE = "Email Finder Pro"
    PAGE_ICON = "📧"
    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"
    
    # Color scheme
    COLORS = {
        'primary': '#1f77b4',
        'success': '#2ca02c',
        'warning': '#ff7f0e',
        'error': '#d62728',
        'info': '#17becf'
    }
    
    # Progress messages
    PROGRESS_MESSAGES = {
        'loading_models': "🤖 Loading available AI models...",
        'validating_input': "✅ Validating input data...",
        'generating_prompt': "📝 Generating search strategy...",
        'searching_web': "🌐 Searching the web for contacts...",
        'processing_results': "📊 Processing and analyzing results...",
        'extracting_requests': "🔍 Extracting with HTTP requests...",
        'extracting_selenium': "🌐 Extracting with browser automation...",
        'searching_sitemap': "🗺️ Searching sitemap...",
        'categorizing': "📋 Categorizing email addresses...",
        'finalizing': "✨ Finalizing results..."
    }
    
    # Help texts
    HELP_TEXTS = {
        'api_key': "Get your API key from openrouter.ai - required for AI search",
        'company_name': "Enter the exact company name as it appears officially",
        'website_url': "Main company website (with or without https://)",
        'country': "Primary company location or headquarters",
        'search_depth': "Deep research takes longer but provides more comprehensive results",
        'extraction_method': "Auto tries requests first, then Selenium if needed",
        'sitemap_search': "Also search sitemap.xml for additional email addresses",
        'categorization': "Group emails by type (sales, support, admin, etc.)"
    }

# Create global config instance
config = AppConfig()
email_patterns = EmailPatterns()
ui_config = UIConfig()

# Validate configuration on import
is_valid, config_errors = config.validate_config()
if not is_valid and config.OPENROUTER_API_KEY:  # Only show errors if API key is set
    print("Configuration warnings:")
    for error in config_errors:
        print(f"  - {error}")
