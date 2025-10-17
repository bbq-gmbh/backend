from sqlmodel import Session, SQLModel, create_engine

from app.config.settings import settings

engine = create_engine(settings.DATABASE_URL)


def init_db() -> None:
    """
    Initialize database by creating all tables.

    Note: All models must be imported before calling this function
    to ensure they are registered with SQLModel.metadata.
    """
    # Import models to register them with SQLModel.metadata
    import app.models  # noqa: F401

    # Create all tables
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
