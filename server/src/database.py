from .config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.engine import URL
from typing import Generator
from .logging_config import get_logger

logger = get_logger(__name__)

url = URL.create(
    drivername=Config.DB_DRIVER,
    username=Config.DB_USER,
    password=Config.DB_PASSWORD,
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    database=Config.DB_NAME,
)

logger.debug(f"Database URL created: {Config.DB_DRIVER}://{Config.DB_USER}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}")

engine = create_engine(url, echo=Config.DEBUG)  # echo=True for debugging
Session = sessionmaker(bind=engine)

logger.info(f"Database engine created for: {Config.DB_NAME}")

def get_db() -> Generator[OrmSession, None, None]:
    """
    Dependency for getting a database session.
    
    Yields:
        Database session
        
    Example:
        @app.get("/items/")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    logger.debug("Creating database session")
    with Session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            logger.debug("Closing database session")
