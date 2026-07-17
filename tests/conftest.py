import os

import pytest
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

from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE IF EXISTS wallets CASCADE")

    Base.metadata.create_all(bind=engine)

    yield

    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE IF EXISTS wallets CASCADE")


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
