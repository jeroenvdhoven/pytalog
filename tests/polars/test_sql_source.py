from sqlite3 import connect
from typing import Any, Generator
from unittest.mock import patch

import polars as pl
from pytest import fixture
from sqlalchemy.engine import Engine, create_engine

from pytalog.polars.data_sources.sql import PolarsSqlSource


@fixture(scope="session")
def db() -> Generator[Engine, Any, None]:
    """Starts an in-memory SQLite database.

    The returned Engine will be a SQLalchemy one, to allow more flexibility
    with the mocking of other databases.

    Yields:
        Generator[Engine, Any, None]: A SQLalchemy database engine for
            the creater SQLite database.
    """
    connect(":memory:")
    yield create_engine("sqlite:///:memory:")


class TestSqlSource:
    def test_read(self):
        query = "Select * from *"
        conn = "sqlite://nowhere"
        extra = [4, 5]
        source = PolarsSqlSource(query, conn, 1, 2, extra=extra)

        with patch("pytalog.polars.data_sources.sql.read_database") as mock_read_sql:
            result = source.read()

        mock_read_sql.assert_called_once_with(1, 2, query=query, connection=conn, extra=extra)
        assert result == mock_read_sql.return_value

    def test_read_integration(self, db: Engine):
        table = "mytesttable"
        query = f"Select * from {table}"

        with db.connect() as conn:
            df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
            df.write_database(table, connection=conn)

            source = PolarsSqlSource(query, conn)
            result = source.read()

        assert result.equals(df)
