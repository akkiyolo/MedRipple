from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings
from app.core.logging import logger

engine = create_engine(
    settings.sqlalchemy_database_uri,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        with engine.begin() as conn:
            # Migration checks for users table columns
            columns = [
                ("password_reset_token_hash", "VARCHAR(255)"),
                ("password_reset_expires_at", "TIMESTAMP WITH TIME ZONE"),
                ("profile_image_key", "VARCHAR(512)"),
                ("profile_image_content_type", "VARCHAR(100)"),
                ("profile_image_size", "INTEGER"),
                ("profile_image_uploaded_at", "TIMESTAMP WITH TIME ZONE"),
                ("google_access_token", "VARCHAR(2048)"),
                ("google_refresh_token", "VARCHAR(2048)"),
                ("google_token_expires_at", "TIMESTAMP WITH TIME ZONE"),
            ]
            for col_name, col_type in columns:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                except Exception as e:
                    logger.debug(f"Column migration notice ({col_name}): {e}")
        logger.info("Database schema initialized and verified successfully.")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
