import dotenv
import os

dotenv.load_dotenv()

class Config:
    DEBUG = os.getenv("DEBUG", "True") == "True"
    DB_DRIVER = os.getenv("DB_DRIVER", "postgresql+psycopg2")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "valheim_db")
