import dotenv
import os

dotenv.load_dotenv()

class Config:
    # Application Settings
    DEBUG = os.getenv("DEBUG", "True") == "True"
    
    # Database Configuration
    DB_DRIVER = os.getenv("DB_DRIVER", "postgresql+psycopg2")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "valheim_db")
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "detailed")  # "simple" or "detailed"
    LOG_FILE = os.getenv("LOG_FILE", None)  # Optional log file path
    
    # API Configuration
    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))

