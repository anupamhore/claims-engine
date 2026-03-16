"""
WHY: Centralized configuration management
  - Load environment variables safely
  - Type validation for config values
  - Defaults for development
  - Easy to override per environment

HOW:
  - Load from .env using python-dotenv
  - Validate required fields
  - Return config dict

ALTERNATIVE not chosen:
  - Hardcoded values: Not secure, inflexible
  - pydantic Settings: Overkill, adds dependency
"""

import os
from dotenv import load_dotenv
from src.utils.exceptions import ConfigurationError

# Load .env file
load_dotenv()


def load_config() -> dict:
    """
    Load and validate configuration from environment.
    
    Returns:
        Configuration dictionary
        
    Raises:
        ConfigurationError: If required config is missing
    """
    
    # Required fields
    required_fields = [
        "DB_HOST",
        "DB_PORT",
        "DB_USER",
        "DB_PASSWORD",
        "DB_NAME",
    ]

    # Check required fields in .env (except during testing)
    if os.getenv("APP_ENV") != "testing":
        missing = [field for field in required_fields if not os.getenv(field)]
        if missing:
            raise ConfigurationError(
                f"Missing required configuration: {', '.join(missing)}. "
                f"Please check your .env file."
            )

    config = {
        # API
        "app_name": os.getenv("APP_NAME", "Claims-Triage-Engine"),
        "app_env": os.getenv("APP_ENV", "development"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),

        # Database
        "db_host": os.getenv("DB_HOST", "localhost"),
        "db_port": int(os.getenv("DB_PORT", "5432")),
        "db_user": os.getenv("DB_USER", "claims_user"),
        "db_password": os.getenv("DB_PASSWORD", "password"),
        "db_name": os.getenv("DB_NAME", "claims_db"),
        "db_pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
        "db_max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "40")),

        # Redis
        "redis_host": os.getenv("REDIS_HOST", "localhost"),
        "redis_port": int(os.getenv("REDIS_PORT", "6379")),
        "redis_db": int(os.getenv("REDIS_DB", "0")),
        "redis_password": os.getenv("REDIS_PASSWORD"),
        "redis_ttl": int(os.getenv("REDIS_TTL", "86400")),

        # Kafka
        "kafka_brokers": os.getenv("KAFKA_BROKERS", "localhost:9092"),
        "kafka_security_protocol": os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        "kafka_consumer_group": os.getenv("KAFKA_CONSUMER_GROUP", "claims-processor"),

        # LLM: Groq
        "groq_api_key": os.getenv("GROQ_API_KEY"),
        "groq_model": os.getenv("GROQ_MODEL", "mixtral-8x7b-32768"),
        "groq_temperature": float(os.getenv("GROQ_TEMPERATURE", "0.1")),
        "groq_max_tokens": int(os.getenv("GROQ_MAX_TOKENS", "500")),

        # LLM: OpenAI
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4"),
        "openai_temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
        "openai_max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "500")),

        # ML Models
        "model_cache_dir": os.getenv("MODEL_CACHE_DIR", "./models"),
        "bert_model_name": os.getenv("BERT_MODEL_NAME", "distilbert-base-uncased"),
        "xgboost_model_path": os.getenv("XGBOOST_MODEL_PATH", "./models/xgboost_fraud_model.pkl"),
        "min_confidence_threshold": float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.7")),

        # AWS
        "aws_region": os.getenv("AWS_REGION", "us-east-1"),
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "s3_bucket_name": os.getenv("S3_BUCKET_NAME"),
        "ecr_registry": os.getenv("ECR_REGISTRY"),

        # Security
        "secret_key": os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
        "api_key_header_name": os.getenv("API_KEY_HEADER_NAME", "X-API-Key"),
        "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
        "jwt_expiration_hours": int(os.getenv("JWT_EXPIRATION_HOURS", "24")),

        # CORS
        "cors_origins": os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8501"),
        "allowed_hosts": os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1"),

        # Monitoring
        "sentry_dsn": os.getenv("SENTRY_DSN"),
        "log_format": os.getenv("LOG_FORMAT", "json"),
    }

    return config


# Load on module import
try:
    _config = load_config()
except ConfigurationError as e:
    # Allow import but warn about missing config
    print(f"⚠️ Configuration warning: {e}")
    _config = {}
