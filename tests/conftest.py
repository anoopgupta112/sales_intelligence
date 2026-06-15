import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport
import app.db.session
from app.main import app as fastapi_app
from app.db.base import Base
from app.db.models import User, Lead, ResearchReport, OutreachMessage, WorkflowRun, AgentLog
from app.db.session import get_db

# Use a file-based SQLite database for testing to maintain tables across connections
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create engine and schema once for the test session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        # Create all tables in the SQLite database
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    
    # Remove the temporary SQLite file
    import os
    if os.path.exists("./test.db"):
        try:
            os.remove("./test.db")
        except Exception:
            pass

@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session tied to a transaction which is rolled back after each test."""
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    # Patch the global session maker so that LangGraph workflow nodes use the SQLite test session
    old_maker = app.db.session.async_session_maker
    app.db.session.async_session_maker = async_session
    
    async with async_session() as session:
        try:
            yield session
        finally:
            app.db.session.async_session_maker = old_maker
            await session.rollback()

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async client with the database session overridden."""
    # Override get_db dependency to yield the test db session
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()
