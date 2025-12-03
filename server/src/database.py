from .config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.engine import URL
from typing import Generator

url = URL.create(
    drivername=Config.DB_DRIVER,
    username=Config.DB_USER,
    password=Config.DB_PASSWORD,
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    database=Config.DB_NAME,
)

engine = create_engine(url, echo=Config.DEBUG)  # echo=True for debugging
Session = sessionmaker(bind=engine)

def get_db() -> Generator[OrmSession, None, None]:
    with Session() as session:
        yield session
