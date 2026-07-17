import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://wallet_user:password@localhost:5433/wallet_api_test",
)

os.environ["DATABASE_URL"] = TEST_DATABASE_URL

engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

from app.database import get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    alembic_config = Config("alembic.ini")

    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")

    yield

    command.downgrade(alembic_config, "base")


@pytest.fixture()
def client():
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
