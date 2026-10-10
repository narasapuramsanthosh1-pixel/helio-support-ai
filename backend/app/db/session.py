from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import PROJECT_ROOT, settings


class Base(DeclarativeBase):
    pass


def _database_url() -> str:
    url = settings.database_url
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        relative = url.removeprefix("sqlite:///")
        database_path = (PROJECT_ROOT / relative).resolve()
        database_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{database_path.as_posix()}"
    return url


DATABASE_URL = _database_url()
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Import model modules to register ORM metadata before create_all() is used.
from app.models import entities  # noqa: F401


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
