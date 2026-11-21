import os

os.environ["DATABASE_URL"] = "postgresql+psycopg2://postgres:postgres@localhost:5432/pms_test"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.base import Base
from app.database import get_db
from app.main import app
from app.models import User, UserRole
from app.security import hash_password

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once for the whole test session."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """
    Give each test its own connection + transaction, and roll it back
    at the end -- so tests never leak data into each other regardless
    of execution order.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


DEMO_PASSWORD = "Password123!"


def make_user(db, name, email, role) -> User:
    user = User(
        name=name,
        email=email,
        role=role,
        password_hash=hash_password(DEMO_PASSWORD),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def admin_user(db):
    return make_user(db, "Admin", "admin@test.com", UserRole.ADMIN)


@pytest.fixture()
def manager_user(db):
    return make_user(db, "Manager One", "manager1@test.com", UserRole.PROPERTY_MANAGER)


@pytest.fixture()
def other_manager_user(db):
    return make_user(db, "Manager Two", "manager2@test.com", UserRole.PROPERTY_MANAGER)


@pytest.fixture()
def tenant_user(db):
    return make_user(db, "Tenant One", "tenant1@test.com", UserRole.TENANT)


@pytest.fixture()
def other_tenant_user(db):
    return make_user(db, "Tenant Two", "tenant2@test.com", UserRole.TENANT)


def auth_headers(client: TestClient, email: str, password: str = DEMO_PASSWORD) -> dict:
    response = client.post(
        "/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
