from .config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.engine import URL
from typing import Generator
from .logging_config import get_logger

logger = get_logger(__name__)

url = URL.create(
    drivername=settings.db_driver,
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)

logger.debug(f"Database URL created: {settings.db_driver}://{settings.db_user}@{settings.db_host}:{settings.db_port}/{settings.db_name}")

engine = create_engine(url, echo=settings.debug)  # echo=True for debugging
Session = sessionmaker(bind=engine)

logger.info(f"Database engine created for: {settings.db_name}")

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
