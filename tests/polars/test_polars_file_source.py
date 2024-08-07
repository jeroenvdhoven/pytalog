from tempfile import NamedTemporaryFile
from typing import Callable
from unittest.mock import MagicMock, patch

import polars as pl
from pytest import mark

from pytalog.polars.data_sources import PolarsFileSource
from tests.utils import pytest_assert


class TestPolarsFileSource:
    def test_assert(self):
        format = "adfjklljkfd"
        with pytest_assert(
            AssertionError, f"`{format}` is not a supported read format for Polars! Check pl.read_* functions."
        ):
            PolarsFileSource("", format)

    def test_read_unit(self):
        path = "some path"
        format = "csv"
        args = {"a": 3, "index": False}

        mock_read = MagicMock()
        with patch("polars.read_csv") as mock_read:
            source = PolarsFileSource(path, format, read_args=args)
            source.read()

            mock_read.assert_called_once_with(source=path, **args)

    @mark.parametrize(
        ["format", "suffix", "write_func"],
        [
            ["csv", ".csv", pl.DataFrame.write_csv],
            ["excel", ".xlsx", pl.DataFrame.write_excel],
            ["parquet", ".parquet", pl.DataFrame.write_parquet],
            ["json", ".json", pl.DataFrame.write_json],
        ],
    )
    def test_read_integration(self, format: str, suffix: str, write_func: Callable):
        df = pl.DataFrame(
            {
                "x": [1, 2, 3],
                "y": ["a", "b", "c"],
                "z": ["3", "6", "7a"],
            }
        )

        with NamedTemporaryFile("r+", suffix=suffix) as f:
            write_func(df, f.name)

            source = PolarsFileSource(path=f.name, format=format)
            result = source.read()

            assert df.equals(result)

    def test_write_unit(self):
        path = "some path"
        format = "csv"
        args = {"a": 3, "index": False}

        mock_df = MagicMock()
        mock_write = MagicMock()

        source = PolarsFileSource(path, format, write_args=args)
        source.write_dict = {format: mock_write}
        source.write(mock_df)

        mock_write.assert_called_once_with(mock_df, path, **args)

    @mark.parametrize(
        ["format", "suffix", "read_func"],
        [
            [
                "csv",
                ".csv",
                pl.read_csv,
            ],
            [
                "excel",
                ".xlsx",
                pl.read_excel,
            ],
            [
                "parquet",
                ".parquet",
                pl.read_parquet,
            ],
            [
                "json",
                ".json",
                pl.read_json,
            ],
        ],
    )
    def test_write_integration(self, format: str, suffix: str, read_func: Callable[..., pl.DataFrame]):
        df = pl.DataFrame(
            {
                "x": [1, 2, 3],
                "y": ["a", "b", "c"],
                "z": ["3", "6e", "7"],
            }
        )

        with NamedTemporaryFile("r+", suffix=suffix) as f:
            source = PolarsFileSource(path=f.name, format=format)
            source.write(df)

            result = read_func(f.name)

            assert df.equals(result)
