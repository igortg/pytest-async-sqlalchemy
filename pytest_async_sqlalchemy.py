# -*- coding: utf-8 -*-
import asyncio
import sys

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url, URL
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
def _database_url(database_url, request) -> URL:
    url = request.config.getoption("database_url") or database_url
    return make_url(url)


async def create_database(url: URL):
    database_name = url.database
    dbms_url = url.set(database="")
    engine = create_async_engine(dbms_url, isolation_level="AUTOCOMMIT")

    async with engine.connect() as conn:
        c = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname='{database_name}'")
        )
        database_exists = c.scalar() == 1

    if database_exists:
        await drop_database(url)

    async with engine.connect() as conn:
        await conn.execute(
            text(f'CREATE DATABASE "{database_name}" ENCODING "utf8" TEMPLATE template1')
        )


async def drop_database(url: URL):
    dbms_url = url.set(database="")
    engine = create_async_engine(dbms_url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        disc_users = """
        SELECT pg_terminate_backend(pg_stat_activity.%(pid_column)s)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '%(database)s'
          AND %(pid_column)s <> pg_backend_pid();
        """ % {
            "pid_column": "pid",
            "database": url.database,
        }
        await conn.execute(text(disc_users))

        await conn.execute(text(f'DROP DATABASE "{url.database}"'))


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
async def function_scoped_database(_database_url, init_database) -> AsyncEngine:
    """
    This fixture creates a new database just for the test function being run (instead of
    using the same database for the entire test session).
    """
    new_database_name = _database_url.database + "_function_scoped"
    function_scoped_database_url = _database_url.set(database=new_database_name)
    await create_database(function_scoped_database_url)

    engine = create_async_engine(function_scoped_database_url)
    async with engine.begin() as conn:
        await conn.run_sync(init_database)

    try:
        yield engine
    finally:
        await engine.dispose()
        await drop_database(function_scoped_database_url)


@pytest.fixture(scope="function")
async def database(_database_url, init_database) -> str:
    """
    This fixture creates a new database just for the test function being run.
    """
    database_url = _database_url.set(
        database=_database_url.database + "_function_scoped"
    )
    await create_database(database_url)

    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(init_database)
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
