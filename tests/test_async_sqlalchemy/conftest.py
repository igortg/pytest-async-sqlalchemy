import pytest

from sqlalchemy import MetaData, Table, String, Integer, Column

metadata = MetaData()

table1 = Table(
    "table1",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("descr", String),
)


@pytest.fixture(scope="session")
def database_url():
    return "postgresql+asyncpg://postgres:masterkey@localhost/defaultdb"


@pytest.fixture(scope="session")
def init_database():
    return metadata.create_all
