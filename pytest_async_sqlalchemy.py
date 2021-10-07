# -*- coding: utf-8 -*-
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


def pytest_addoption(parser):
    parser.addoption(
        "--database-url",
        action="store",
        default="",
        help="Use the given Postgres URL and skip Postgres container booting",
    )


@pytest.fixture(scope="session")
def database_url(request):
    effective_url = request.config.getoption("database_url")
    if effective_url:
        return effective_url
    else:
        try:
            return request.getfixturevalue("_database_url")
        except pytest.FixtureLookupError:
            pytest.exit(
                'Database URL not given. Define a "_database_url" session fixture or '
                'use the "--database-url" in the command line.',
                returncode=1,
            )


@pytest.fixture(scope="session")
async def database(database_url, event_loop, init_database):
    await create_database(database_url)

    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(init_database)
    await engine.dispose()

    try:
        yield database_url
    finally:
        await drop_database(database_url)


@pytest.fixture(scope="session")
async def sqla_engine(database):
    engine = create_async_engine(database)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="function")
async def scoped_sqla_engine(database_url, init_database):
    """
    This fixture creates a new database just for the test function being run.
    """
    url_object = make_url(database_url)
    scoped_sqla_url = url_object.set(database=url_object.database + "_function_scoped")
    await create_database(scoped_sqla_url)

    engine = create_async_engine(scoped_sqla_url)
    async with engine.begin() as conn:
        await conn.run_sync(init_database)

    try:
        yield engine
    finally:
        await engine.dispose()
        await drop_database(scoped_sqla_url)


@pytest.fixture(scope="function")
async def scoped_database(scoped_sqla_engine):
    """
    This fixture creates a new database just for the test function being run.
    """
    scoped_sqla_url = scoped_sqla_engine.url
    return scoped_sqla_url.render_as_string(hide_password=False)


@pytest.fixture()
async def db_session(sqla_engine):
    """
    Fixture that returns a SQLAlchemy session with a SAVEPOINT, and the rollback to it
    after the test completes.
    """
    connection = await sqla_engine.connect()
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
async def dbsession(db_session):
    """
    Alias for backward compatibility
    """
    yield db_session


@pytest.fixture()
async def transaction(_engine):
    conn = await _engine.begin()
    try:
        yield conn
    finally:
        await conn.rollback()


POSTGRES_DEFAULT_DB = "postgres"


async def create_database(url: str):
    url_object = make_url(url)
    database_name = url_object.database
    dbms_url = url_object.set(database=POSTGRES_DEFAULT_DB)
    engine = create_async_engine(dbms_url, isolation_level="AUTOCOMMIT")

    async with engine.connect() as conn:
        c = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname='{database_name}'")
        )
        database_exists = c.scalar() == 1

    if database_exists:
        await drop_database(url_object)

    async with engine.connect() as conn:
        await conn.execute(
            text(f'CREATE DATABASE "{database_name}" ENCODING "utf8" TEMPLATE template1')
        )
    await engine.dispose()


async def drop_database(url: str):
    url_object = make_url(url)
    dbms_url = url_object.set(database=POSTGRES_DEFAULT_DB)
    engine = create_async_engine(dbms_url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        disc_users = """
        SELECT pg_terminate_backend(pg_stat_activity.%(pid_column)s)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '%(database)s'
          AND %(pid_column)s <> pg_backend_pid();
        """ % {
            "pid_column": "pid",
            "database": url_object.database,
        }
        await conn.execute(text(disc_users))

        await conn.execute(text(f'DROP DATABASE "{url_object.database}"'))
