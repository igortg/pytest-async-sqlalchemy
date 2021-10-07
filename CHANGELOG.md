# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Add a `_` prefix to the fixture used to define the database URL: from `database_url` to
  `_database_url`
- `_database_url` value is overridden by the `--database-url` CLI option, if given
- `_engine` fixture renamed to `sqla_engine`
- `database` fixture renamed to `scoped_database`. A new fixture named `database` gives
  access to the test session database
- `function_scoped_database` fixture renamed to `scoped_sqla_engine`
- `db_session` fixture renamed to `dbsession` (`dbsession` fixture was kept for 
  backward compatibility)

### Fixed

- Fixed issue to create the test database when default user not set to "postgres" (#2)
