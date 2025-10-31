"""
Database connection management for PostgreSQL
Supports both local development and Cloud SQL
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from loguru import logger
from typing import Generator

# Database configuration from environment
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "ma_diligence")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Cloud SQL connection
CLOUD_SQL_CONNECTION = os.getenv("CLOUD_SQL_CONNECTION_NAME")  # e.g., project:region:instance

def get_database_url() -> str:
    """
    Get database URL based on environment
    
    Returns:
        Database connection URL
    """
    if ENVIRONMENT == "production" and CLOUD_SQL_CONNECTION:
        # Cloud SQL connection using Unix socket
        logger.info(f"Using Cloud SQL connection: {CLOUD_SQL_CONNECTION}")
        return f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?host=/cloudsql/{CLOUD_SQL_CONNECTION}"
    else:
        # Standard PostgreSQL connection for development
        logger.info(f"Using standard PostgreSQL connection: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        return f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# Create engine
DATABASE_URL = get_database_url()

if ENVIRONMENT == "production":
    # Production settings - no connection pooling for Cloud Run
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        echo=False,
        connect_args={
            "connect_timeout": 10,
            "options": "-c timezone=utc"
        }
    )
else:
    # Development settings - with connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=True,  # Log SQL queries in development
        connect_args={
            "connect_timeout": 10,
            "options": "-c timezone=utc"
        }
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session for dependency injection
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database schema
    Creates all tables defined in models
    """
    from src.database.models import Base, User
    import bcrypt
    
    try:
        logger.info("Initializing database schema...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")
        
        # Create default admin user if not exists
        db = SessionLocal()
        try:
            admin_exists = db.query(User).filter_by(email="smaan2011@gmail.com").first()
            if not admin_exists:
                logger.info("Creating default admin user...")
                
                # Hash password
                password = "admin123"  # Change this in production!
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
                
                # Create admin user
                admin_user = User(
                    id="admin-001",
                    email="smaan2011@gmail.com",
                    password_hash=password_hash,
                    role="admin",
                    is_active=True
                )
                
                db.add(admin_user)
                db.commit()
                logger.info(f"✓ Created admin user: smaan2011@gmail.com")
                logger.warning("⚠️  IMPORTANT: Change the default admin password!")
            else:
                logger.info("Admin user already exists")
                
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is working
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        logger.info("✓ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def get_db_stats() -> dict:
    """
    Get database statistics
    
    Returns:
        Dictionary with database stats
    """
    from src.database.models import User, Analysis
    
    try:
        db = SessionLocal()
        
        stats = {
            "total_users": db.query(User).count(),
            "active_users": db.query(User).filter_by(is_active=True).count(),
            "total_analyses": db.query(Analysis).count(),
            "completed_analyses": db.query(Analysis).filter_by(status="completed").count(),
            "running_analyses": db.query(Analysis).filter_by(status="running").count()
        }
        
        db.close()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {}
