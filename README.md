# pytest-async-sqlalchemy

![PyPI version](https://img.shields.io/pypi/v/pytest-async-sqlalchemy.svg)
![Python versions](https://img.shields.io/pypi/pyversions/pytest-async-sqlalchemy.svg)

Database testing fixtures using the SQLAlchemy asyncio API

You can install "pytest-async-sqlalchemy" via [pip] from [PyPI]

    $ pip install pytest-async-sqlalchemy

## Setup

`pytest-async-sqlalchemy` provides placeholders to configure and initialize
the testing database: `database_url` and `init_database`. These two **must** be
defined in your project `conftest.py` like below:

    @pytest.fixture(scope="session")
    def database_url():
        return "postgresql+asyncpg://postgres:masterkey@localhost/dbtest"
    
    
    @pytest.fixture(scope="session")
    def init_database():
        from myprorject.db import metadata
    
        return metadata.create_all

The `database_url` must be a session-scoped fixture that returns the database URI.
`init_database` must also be a session-scoped fixture that returns the callable used
to initialize the database (in most cases, this would return the 
`metadata.create_all` function).    

## Usage

This plugin provides the following fixtures:

- `dbsession`: An `AsyncSession` object bounded to the test database. Database changes
  are discarded after each test function, so the same database is used for the entire 
  test suite (avoiding the overhead of initializing a database on every test).
- `database`: `database` provides a new database within the scope of the test function. 
  The value of the fixture is a string URL pointing to the database.

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [MIT] license, "pytest-async-sqlalchemy" is free and open source software

[pip]: http://pypi.org/project/pip
[PyPI]: https://pypi.org/project
[MIT]: http://opensource.org/licenses/MIT
[tox]: https://tox.readthedocs.io/en/latest/