# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from app.logger import get_logger

load_dotenv()  # reads variables from .env file into os.environ

logger = get_logger(__name__)

# Build the connection string from environment variables
# Format: postgresql://user:password@host:port/dbname
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

# create_engine: the "factory" that manages the actual DB connection
# pool_pre_ping=True: tests the connection before each use (handles dropped connections)
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

# SessionLocal: a factory for creating database sessions
# Each request gets its own session (like a temporary workspace)
# autocommit=False: changes aren't saved until you explicitly commit
# autoflush=False: SQLAlchemy won't auto-write to DB mid-session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: all your SQLAlchemy models will inherit from this
Base = declarative_base()


def get_db():
    """
    Dependency function that provides a database session per request.
    Uses 'yield' so FastAPI can run cleanup code (db.close()) after the request.
    This is called a 'context manager' pattern.
    """
    db = SessionLocal()
    try:
        logger.debug("Database session opened")
        yield db          # ← FastAPI pauses here, runs your endpoint, then continues
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()     # undo any incomplete changes if something went wrong
        raise
    finally:
        db.close()        # ALWAYS close, even if an error occurred
        logger.debug("Database session closed")