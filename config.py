import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    """
    Base configuration class.
    """
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    """
    Development-specific configuration.
    """
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URI', 'sqlite:///development.db')

class ProductionConfig(Config):
    """
    Production-specific configuration.
    """
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('PROD_DATABASE_URI', 'postgresql://user:password@localhost:5432/leadgen')

# Configuration mapping
configurations = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}
