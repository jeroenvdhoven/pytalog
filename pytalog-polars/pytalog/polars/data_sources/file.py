from typing import Any, Dict, Optional, Protocol

import polars as pl
from polars import DataFrame  # type: ignore

from pytalog.base.data_sources.data_source import WriteableDataSource


class _PolarsReadFunction(Protocol):
    def __call__(self, source: str, **kwargs: Any) -> DataFrame:
        ...


class _PolarsWriteFunction(Protocol):
    def __call__(self, df: DataFrame, source: str, **kwargs: Any) -> Any:
        ...


class PolarsFileSource(WriteableDataSource[DataFrame]):
    def __init__(
        self,
        path: str,
        format: str,
        read_args: Optional[Dict[str, Any]] = None,
        write_args: Optional[Dict[str, Any]] = None,
    ):
        """Reads data from a given file using Polars.

        Args:
            path (str): The path to the file.
            format (str): The format of the file. Polars should support this. We'll look for the
                relevant read/write function by searching polars.read_<format> or df.to_<format>.
            read_args (Optional[Dict[str, Any]]): Keyword arguments to be passed to `polars read_*`.
                By default no args are passed.
            write_args (Optional[Dict[str, Any]]): Keyword arguments to be passed to `polars write_*`.
                By default no args are passed.
        """
        self.path = path
        self.format = format
        self.read_args = {} if read_args is None else read_args
        self.write_args = {} if write_args is None else write_args

        self.read_dict = self._create_read_function_dict()
        self.write_dict = self._create_write_function_dict()

        assert (
            format in self.read_dict
        ), f"`{format}` is not a supported read format for Polars! Check pl.read_* functions."
        assert (
            format in self.write_dict
        ), f"`{format}` is not a supported write format for Polars! Check pl.write_* functions."

    def read(self) -> DataFrame:
        """Reads the data from the source."""
        read_func = self.read_dict[self.format]
        return read_func(source=self.path, **self.read_args)

    def write(self, data: DataFrame) -> None:
        """Writes the data to the source."""
        write_func = self.write_dict[self.format]
        write_func(data, self.path, **self.write_args)

    @staticmethod
    def _create_read_function_dict() -> Dict[str, _PolarsReadFunction]:
        return {key.replace("read_", ""): func for key, func in pl.__dict__.items() if key.startswith("read_")}

    @staticmethod
    def _create_write_function_dict() -> Dict[str, _PolarsWriteFunction]:
        return {key.replace("write_", ""): func for key, func in DataFrame.__dict__.items() if key.startswith("write_")}
