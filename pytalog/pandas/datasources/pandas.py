from typing import Any, Dict, Optional

import pandas as pd

from pytalog.base.datasources.data_source import DataSource, WriteableDataSource


class DataFrameSource(DataSource[pd.DataFrame]):
    def __init__(self, df: pd.DataFrame) -> None:
        """A DataSource based around a created DataFrame.

        Good for testing purposes, but please use other sources for actual usage.

        Args:
            df (pd.DataFrame): The DataFrame to use as a source.
        """
        super().__init__()
        self.df = df

    def read(self) -> pd.DataFrame:
        """Returns the DataFrame given as input before.

        Returns:
            pd.DataFrame: The DataFrame used to initialise this object.
        """
        return self.df


class SqlSource(DataSource[pd.DataFrame]):
    def __init__(
        self,
        sql: str,
        con: str,
        *args: Any,
        **kwargs: Any,
    ):
        """Reads data from a sql table using Pandas read_sql.

        This class only acts as a storage for the arguments to call Pandas read_sql.
        For proper documentation on the arguments, check Pandas read_sql.

        Args:
            sql (str): The sql and the `sql` argument to `Pandas read_sql`.
            con (str): The con string and `con` argument to `Pandas read_sql`.
            args: Positional arguments to be passed to `Pandas read_sql`.
            kwargs: Keyword arguments to be passed to `Pandas read_sql`.
        """
        self.sql = sql
        self.con = con
        self.args = args
        self.kwargs = kwargs
        super().__init__()

    def read(self) -> pd.DataFrame:
        """Use the provided arguments to call `read_sql`.

        Returns:
            pd.DataFrame: The result of the provided query.
        """
        return pd.read_sql(*self.args, sql=self.sql, con=self.con, **self.kwargs)


class PandasFileSource(WriteableDataSource[pd.DataFrame]):
    PANDAS_IO_FUNCTIONS = {
        "json": (pd.read_json, lambda df, path, **args: df.to_json(path, **args)),
        "csv": (pd.read_csv, lambda df, path, **args: df.to_csv(path, **args)),
        "parquet": (pd.read_parquet, lambda df, path, **args: df.to_parquet(path, **args)),
        "excel": (pd.read_excel, lambda df, path, **args: df.to_excel(path, **args)),
    }

    def __init__(
        self,
        path: str,
        format: str,
        read_args: Optional[Dict[str, Any]] = None,
        write_args: Optional[Dict[str, Any]] = None,
    ):
        """Reads data from a given file using Pandas.

        Currently supported files include:
            - csv
            - excel
            - parquet
            - json

        Args:
            path (str): The path to the file.
            format (str): The format of the file. Pandas should support this. Supported
                values can be found in PandasFileSource.FUNCTIONS
            read_args (Optional[Dict[str, Any]]): Keyword arguments to be passed to `Pandas read_*`.
                By default no args are passed.
            write_args (Optional[Dict[str, Any]]): Keyword arguments to be passed to `Pandas to_*`.
                By default no args are passed.
        """
        super().__init__()
        assert format in self.PANDAS_IO_FUNCTIONS, f"`{format}` is not a supported format for Pandas!"

        self.path = path
        self.format = format
        self.read_args = {} if read_args is None else read_args
        self.write_args = {} if write_args is None else write_args

    def read(self) -> pd.DataFrame:
        """Use the provided arguments to call `read_sql`.

        Returns:
            pd.DataFrame: The result of the provided query.
        """
        read_func, _ = self.PANDAS_IO_FUNCTIONS[self.format]
        return read_func(self.path, **self.read_args)

    def write(self, data: pd.DataFrame) -> None:
        """Writes the given data to the given file.

        Args:
            data (pd.DataFrame): The DataFrame to be written.
        """
        _, write_func = self.PANDAS_IO_FUNCTIONS[self.format]
        write_func(data, self.path, **self.write_args)
