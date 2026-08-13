from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from .config import settings

# SQLite configuration with proper timeout and pooling
if "sqlite" in settings.database_url:
    engine = create_engine(
        settings.database_url,
        connect_args={
            "check_same_thread": False,
            "timeout": 30  # 30 second timeout for database locks
        },
        poolclass=StaticPool,  # Use static pool for SQLite
        echo=False
    )

    # Enable WAL mode for better concurrency
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        try:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
        except Exception:
            pass  # Ignore pragma errors
else:
    engine = create_engine(
        settings.database_url,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
