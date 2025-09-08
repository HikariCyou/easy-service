import pytest
import asyncio
from tortoise import Tortoise
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db():
    """Initialize test database for each test."""
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["app.models"]}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
def client():
    """Test client fixture."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client():
    """Async test client fixture."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac