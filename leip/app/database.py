from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config.settings import settings

# Determine if we're using SQLite based on the URL
is_sqlite = settings.database_url.startswith("sqlite")

# SQLite needs check_same_thread=False
connect_args = {"check_same_thread": False} if is_sqlite else {}

try:
    engine = create_engine(
        settings.database_url,
        pool_size=settings.database_pool_size if not is_sqlite else 5,
        max_overflow=10 if not is_sqlite else 10,
        echo=settings.database_echo_sql,
        connect_args=connect_args
    )
except TypeError:
    # If using SQLite and pool_size is passed, it might raise an error for some SQLite configurations
    # We will fallback to default engine creation
    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo_sql,
        connect_args=connect_args
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
