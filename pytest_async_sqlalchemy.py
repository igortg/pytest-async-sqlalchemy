# -*- coding: utf-8 -*-
import asyncio
import sys

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker


def pytest_addoption(parser):
    parser.addoption(
        "--database-url",
        action="store",
        default="",
        help="Use the given Postgres URL and skip Postgres container booting",
    )


@pytest.fixture(scope="session")
def event_loop():
    """
    Creates an instance of the default event loop for the test session.
    """
    if sys.version_info[:2] >= (3, 8) and sys.platform.startswith("win"):
        # Avoid "RuntimeError: Event loop is closed" on Windows when tearing down tests
        # https://github.com/encode/httpx/issues/914
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def _database_url(database_url, request):
    url = request.config.getoption("database_url") or database_url
    return url


async def create_database(database_url):
    database_name = make_url(database_url).database
    dbms_url = database_url.replace("/" + database_name, "")
    engine = create_async_engine(dbms_url, isolation_level="AUTOCOMMIT")

    async with engine.connect() as conn:
        c = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname='{database_name}'")
        )
        database_exists = c.scalar() == 1

    if database_exists:
        await drop_database(database_url)

    async with engine.connect() as conn:
        await conn.execute(
            text(f'CREATE DATABASE "{database_name}" ENCODING "utf8" TEMPLATE template1')
        )


async def drop_database(database_url):
    database_name = make_url(database_url).database
    dbms_url = database_url.replace("/" + database_name, "")
    engine = create_async_engine(dbms_url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        disc_users = """
        SELECT pg_terminate_backend(pg_stat_activity.%(pid_column)s)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '%(database)s'
          AND %(pid_column)s <> pg_backend_pid();
        """ % {
            "pid_column": "pid",
            "database": database_name,
        }
        await conn.execute(text(disc_users))

        await conn.execute(text(f'DROP DATABASE "{database_name}"'))


@pytest.fixture(scope="session")
async def _engine(_database_url, event_loop, init_database):
    await create_database(_database_url)

    engine = create_async_engine(_database_url)
    async with engine.begin() as conn:
        await conn.run_sync(init_database)

    try:
        yield engine
    finally:
        await engine.dispose()
        await drop_database(_database_url)


@pytest.fixture(scope="function")
async def function_scoped_database(_database_url) -> AsyncEngine:
    """
    This fixture creates a new database just for the test function being run (instead of
    using the same database for the entire test session).
    """
    function_scoped_database_url = _database_url + "_function_scoped"
    await create_database(function_scoped_database_url)

    engine = create_async_engine(function_scoped_database_url)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()
        await drop_database(function_scoped_database_url)


@pytest.fixture(scope="function")
async def database(_database_url) -> str:
    """
    This fixture creates a new database just for the test function being run (instead of
    using the same database for the entire test session).
    """
    database_url = _database_url + "_function_scoped"
    await create_database(database_url)

    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    await engine.dispose()

    try:
        yield database_url
    finally:
        await drop_database(database_url)


@pytest.fixture()
async def dbsession(_engine):
    """
    Fixture that returns a SQLAlchemy session with a SAVEPOINT, and the rollback to it
    after the test completes.
    """
    connection = await _engine.connect()
    trans = await connection.begin()

    Session = sessionmaker(connection, expire_on_commit=False, class_=AsyncSession)
    session = Session()

    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()


@pytest.fixture()
async def transaction(_engine):
    conn = await _engine.begin()
    try:
        yield conn
    finally:
        await conn.rollback()
