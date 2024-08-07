from typing import Any, Union

from polars import DataFrame, read_database  # type: ignore

from pytalog.base.data_sources.data_source import DataSource

try:
    from sqlalchemy.engine import Connection
except ImportError:
    Connection = Any


class PolarsSqlSource(DataSource[DataFrame]):
    def __init__(
        self,
        query: str,
        connection: Union[str, Connection],
        *args: Any,
        **kwargs: Any,
    ):
        """Reads data from a sql table using Polars read_sql.

        This class only acts as a storage for the arguments to call Polars read_database.
        For proper documentation on the arguments, check Polars read_database.

        Args:
            query (str): The sql query argument to `Polars read_database`.
            connection (Union[str, Connection]): The connection string (or Connection)
                argument to `Polars read_database`.
            *args (Any): Positional arguments to be passed to `Polars read_database`.
            **kwargs (Any): Keyword arguments to be passed to `Polars read_database`.
        """
        self.query = query
        self.connection = connection
        self.args = args
        self.kwargs = kwargs
        super().__init__()

    def read(self) -> DataFrame:
        """Use the provided arguments to call `read_sql`.

        Returns:
            DataFrame: The result of the provided query.
        """
        return read_database(*self.args, query=self.query, connection=self.connection, **self.kwargs)
