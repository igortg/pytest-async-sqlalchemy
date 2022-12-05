# pytest-async-sqlalchemy

![PyPI version](https://img.shields.io/pypi/v/pytest-async-sqlalchemy.svg)
![Python versions](https://img.shields.io/pypi/pyversions/pytest-async-sqlalchemy.svg)

Database testing fixtures using the SQLAlchemy asyncio API

You can install "pytest-async-sqlalchemy" via [pip] from [PyPI]

    $ pip install pytest-async-sqlalchemy

## Setup

### Providing a Session Scoped Event Loop

The first thing to do is to declare an `event_loop` fixture  with the scope set as "session". 
You can copy & paste the code below to your `conftest.py`:

    @pytest.fixture(scope="session")
    def event_loop():
        """
        Creates an instance of the default event loop for the test session.
        """
        if sys.platform.startswith("win") and sys.version_info[:2] >= (3, 8):
            # Avoid "RuntimeError: Event loop is closed" on Windows when tearing down tests
            # https://github.com/encode/httpx/issues/914
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        loop = asyncio.new_event_loop()
        yield loop
        loop.close()

This is required since **pytest-async-sqlalchemy** shares the database connection between tests
for performance reasons, but the default `event_loop` fixture defined by 
[pytest-asyncio](http://pypi.org/project/pytest-asyncio) is function scoped<sup>1</sup> (i.e., it 
kills the database connection after each test). 

### Providing Database URL and Initialization

**pytest-async-sqlalchemy** provides placeholders to configure and initialize
the testing database: `database_url` and `init_database`. These two **must** be
defined in your project `conftest.py` like below:

    @pytest.fixture(scope="session")
    def _database_url():
        return "postgresql+asyncpg://postgres:masterkey@localhost/dbtest"
    
    
    @pytest.fixture(scope="session")
    def init_database():
        from myprorject.db import metadata
    
        return metadata.create_all

The `_database_url` must be a session-scoped fixture that returns the database URL in
SQLAlchemy standard. `init_database` must also be a session-scoped fixture that returns
the callable used to initialize the database (in most cases, this would return the 
`metadata.create_all` function).    

## Usage

This plugin provides the following fixtures:

- `db_session`: An `AsyncSession` object bounded to the test session database. Database 
  transactions are discarded after each test function, so the same database is used for 
  the entire test suite (avoiding the overhead of initializing a database on every test).
- `database`: An URL to the initialized test session database.
- `scoped_database`: `scoped_database` provides a new database within the scope of the
  test function. The value of the fixture is a string URL pointing to the database.

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [MIT] license, "pytest-async-sqlalchemy" is free and open source software

[pip]: http://pypi.org/project/pip
[PyPI]: https://pypi.org/project
[MIT]: http://opensource.org/licenses/MIT
[tox]: https://tox.readthedocs.io/en/latest/

---

<small>1. **pytest-async-sqlalchemy** can't provide its own `event_loop` since pytest plugins are not 
able to override fixtures from one another. So the only solution we have now is to aks the user to
declare its own `event_loop` fixture. Suggestions on how to overcome that in a better way are 
welcome, hit us on the Issues section.</small>
