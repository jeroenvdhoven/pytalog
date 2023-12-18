from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock

import pandas as pd
from pytest import mark

from pytalog.pandas.data_sources.pandas import PandasFileSource
from tests.utils import are_dataframes_equal, pytest_assert


class TestPandasFileSource:
    def test_assert(self):
        format = "adfjklljkfd"
        with pytest_assert(AssertionError, f"`{format}` is not a supported format for Pandas!"):
            PandasFileSource("", format)

    def test_read_unit(self):
        path = "some path"
        format = "__tmp__"
        args = {"a": 3, "index": False}

        mock_read = MagicMock()
        try:
            PandasFileSource.PANDAS_IO_FUNCTIONS[format] = (mock_read, None)
            source = PandasFileSource(path, format, read_args=args)
            source.read()

            mock_read.assert_called_once_with(path, **args)
        finally:
            del PandasFileSource.PANDAS_IO_FUNCTIONS[format]

    @mark.parametrize(
        ["format", "suffix", "write_func", "write_kwargs", "read_kwargs"],
        [
            ["csv", ".csv", "to_csv", {"index": False}, {"dtype": {"z": "str"}}],
            ["excel", ".xlsx", "to_excel", {"index": False}, {"dtype": {"z": "str"}}],
            ["parquet", ".parquet", "to_parquet", {}, {}],
            ["json", ".json", "to_json", {}, {"dtype": {"z": "str"}}],
        ],
    )
    def test_read_integration(self, format: str, suffix: str, write_func: str, write_kwargs: dict, read_kwargs: dict):
        df = pd.DataFrame(
            {
                "x": [1, 2, 3],
                "y": ["a", "b", "c"],
                "z": ["3", "6", "7"],
            }
        )

        with NamedTemporaryFile("r+", suffix=suffix) as f:
            writer = getattr(df, write_func)
            writer(f.name, **write_kwargs)

            source = PandasFileSource(path=f.name, format=format, read_args=read_kwargs)
            result = source.read()

            are_dataframes_equal(df, result)

    def test_write_unit(self):
        path = "some path"
        format = "some_write_function"
        args = {"a": 3, "index": False}

        mock_df = MagicMock()
        mock_write = MagicMock()

        try:
            PandasFileSource.PANDAS_IO_FUNCTIONS[format] = (None, mock_write)
            source = PandasFileSource(path, format, write_args=args)
            source.write(mock_df)

            mock_write.assert_called_once_with(mock_df, path, **args)
        finally:
            del PandasFileSource.PANDAS_IO_FUNCTIONS[format]

    @mark.parametrize(
        ["format", "suffix", "read_func", "write_kwargs", "read_kwargs"],
        [
            ["csv", ".csv", "read_csv", {"index": False}, {"dtype": {"z": "str"}}],
            ["excel", ".xlsx", "read_excel", {"index": False}, {"dtype": {"z": "str"}}],
            ["parquet", ".parquet", "read_parquet", {}, {}],
            ["json", ".json", "read_json", {}, {"dtype": {"z": "str"}}],
        ],
    )
    def test_write_integration(self, format: str, suffix: str, read_func: str, write_kwargs: dict, read_kwargs: dict):
        df = pd.DataFrame(
            {
                "x": [1, 2, 3],
                "y": ["a", "b", "c"],
                "z": ["3", "6", "7"],
            }
        )

        with NamedTemporaryFile("r+", suffix=suffix) as f:
            source = PandasFileSource(path=f.name, format=format, write_args=write_kwargs)
            source.write(df)

            reader = getattr(pd, read_func)
            result = reader(f.name, **read_kwargs)

            are_dataframes_equal(df, result)
