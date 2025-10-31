"""
Configuration management for M&A Diligence Swarm
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from loguru import logger


class AIModelConfig(BaseModel):
    """AI Model configuration"""
    model_name: str
    temperature: float = 0.1
    max_tokens: int
    use_cases: list[str]


class AgentConfig(BaseModel):
    """Agent configuration"""
    name: str
    role: str
    llm: str
    capabilities: list[str]
    social_media_llm: Optional[str] = None


class APIConfig(BaseModel):
    """API configuration"""
    base_url: str
    rate_limit: Optional[int] = None
    search_depth: Optional[str] = None
    max_results: Optional[int] = None
    endpoints: Optional[list[str]] = None


class ProcessingConfig(BaseModel):
    """Processing configuration"""
    max_concurrent_tasks: int = 5
    timeout_seconds: int = 300
    retry_attempts: int = 3
    batch_size: int = 10
    document_processing: Dict[str, Any] = Field(default_factory=dict)


class OutputConfig(BaseModel):
    """Output configuration"""
    formats: list[str]
    pdf: Dict[str, Any] = Field(default_factory=dict)
    excel: Dict[str, Any] = Field(default_factory=dict)
    dashboard: Dict[str, Any] = Field(default_factory=dict)


class VectorDBConfig(BaseModel):
    """Vector database configuration"""
    provider: str = "chromadb"
    collection_name: str = "ma_documents"
    embedding_model: str = "text-embedding-004"
    distance_metric: str = "cosine"


class Config:
    """Main configuration class"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration
        
        Args:
            config_path: Path to configuration file (default: config/settings.yaml)
        """
        # Load environment variables
        load_dotenv()
        
        # Set config path
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        
        self.config_path = Path(config_path)
        self._load_config()
        self._validate_env_vars()
        
        logger.info("Configuration loaded successfully")
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            
            # Parse configurations
            self.ai_models = {
                name: AIModelConfig(**config)
                for name, config in self._config['ai_models'].items()
            }
            
            self.agents = {
                name: AgentConfig(**config)
                for name, config in self._config['agents'].items()
            }
            
            self.apis = {
                name: APIConfig(**config)
                for name, config in self._config['apis'].items()
            }
            
            self.processing = ProcessingConfig(**self._config['processing'])
            self.output = OutputConfig(**self._config['output'])
            self.vector_db = VectorDBConfig(**self._config['vector_db'])
            self.logging = self._config['logging']
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _validate_env_vars(self):
        """Validate required environment variables"""
        required_vars = [
            'ANTHROPIC_API_KEY',
            'GOOGLE_API_KEY',
            'FMP_API_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
            logger.warning("Some features may not work properly")
    
    def get_api_key(self, service: str) -> str:
        """Get API key for a service
        
        Args:
            service: Service name (anthropic, google, openai, fmp, tavily)
        
        Returns:
            API key string
        """
        key_map = {
            'anthropic': 'ANTHROPIC_API_KEY',
            'google': 'GOOGLE_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'xai': 'XAI_API_KEY',  # X.AI for Grok models
            'fmp': 'FMP_API_KEY',
            'tavily': 'TAVILY_API_KEY'
        }
        
        env_var = key_map.get(service.lower())
        if not env_var:
            raise ValueError(f"Unknown service: {service}")
        
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(f"API key not found for {service}. Set {env_var} in .env file")
        
        return api_key
    
    def get_gcp_config(self) -> Dict[str, str]:
        """Get Google Cloud Platform configuration
        
        Returns:
            Dictionary with GCP configuration
        """
        return {
            'project_id': os.getenv('GOOGLE_CLOUD_PROJECT'),
            'credentials': os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            'bucket_name': os.getenv('GCS_BUCKET_NAME')
        }
    
    def get_agent_llm(self, agent_name: str) -> str:
        """Get the LLM to use for a specific agent
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            LLM name (gemini, claude, grok)
        """
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        return self.agents[agent_name].llm
    
    def get_model_config(self, model_name: str) -> AIModelConfig:
        """Get configuration for a specific model
        
        Args:
            model_name: Name of the model (gemini, claude, grok)
        
        Returns:
            AIModelConfig object
        """
        if model_name not in self.ai_models:
            raise ValueError(f"Unknown model: {model_name}")
        
        return self.ai_models[model_name]


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance
    
    Returns:
        Config object
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config():
    """Reload configuration from file"""
    global _config
    _config = Config()
    logger.info("Configuration reloaded")
