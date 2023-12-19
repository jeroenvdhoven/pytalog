from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
from pandas.testing import assert_frame_equal
from pytest import mark

from pytalog.base.catalog import Catalog, DataSet
from pytalog.base.data_sources.data_source import DataSource
from tests.utils import pytest_assert


class DummyDataSource(DataSource[int]):
    def __init__(self, v: int) -> None:
        super().__init__()
        self.v = v

    def read(self) -> int:
        return self.v

    @staticmethod
    def dummy_method(p):
        return p + 5


class Test_Catalog:
    def test_read_all(self):
        dss = Catalog[int](
            {
                "a": DummyDataSource(5),
                "b": DummyDataSource(10),
            }
        )

        result = dss.read_all()
        expected = {
            "a": 5,
            "b": 10,
        }
        assert isinstance(result, DataSet)
        assert len(expected) == len(result)
        assert expected["a"] == result["a"]
        assert expected["b"] == result["b"]

    def test_read_with_skip(self):
        validation_set = MagicMock()
        dss = Catalog[int](
            {
                "a": DummyDataSource(5),
                "b": DummyDataSource(10),
            },
            validation_set=validation_set,
        )

        result = dss.read("a", skip_validation=True)
        assert result == 5
        validation_set.validate_data.assert_not_called()

    def test_read(self):
        validation_set = MagicMock()
        dss = Catalog[int](
            {
                "a": DummyDataSource(5),
                "b": DummyDataSource(10),
            },
            validation_set=validation_set,
        )

        result = dss.read("a")
        assert result == 5
        validation_set.validate_data.assert_called_once_with("a", 5)

    @mark.parametrize(
        ["expectation", "dictionary"],
        [
            [False, {}],
            [False, {"1": 1, "2": 2, "3": 3}],
            [False, {"callable": "", "-": {}}],
            [False, {"-": "", "args": {}}],
            [False, {"-": "", "args": []}],
            [True, {"callable": "", "args": {}}],
        ],
    )
    def test_is_valid_parseable_object(self, expectation: bool, dictionary: dict):
        result = Catalog._is_valid_parseable_object(dictionary)
        assert result == expectation

    def test_load_class(self):
        path = "pytalog.base.data_sources.DataSource"
        result = Catalog._load_class(path)

        assert result == DataSource

    def test_load_class_assert(self):
        path = "pytalog.base.data_sources.DataSource:read:failure"

        with pytest_assert(AssertionError, f"{path}: Catalogs do not accept paths with more than 1 `:`"):
            Catalog._load_class(path)

    def test_load_class_with_method(self):
        path = "pytalog.base.data_sources.DataSource:read"
        result = Catalog._load_class(path)

        assert result == DataSource.read

    def test_parse_object(self):
        v = 10
        dct = {"callable": "tests.base.catalog.test_data_catalog.DummyDataSource", "args": {"v": v}}
        result = Catalog._parse_object(dct, create_object=True)

        assert isinstance(result, DummyDataSource)
        assert result.v == v

    def test_nested_parse_object(self):
        p = 2
        dct = {"callable": "tests.base.catalog.test_data_catalog.DummyDataSource:dummy_method", "args": {"p": p}}
        result = Catalog._parse_object(dct, create_object=True)

        assert result == 7

    def test_parse_object_uncreated(self):
        p = 2
        dct = {"callable": "tests.base.catalog.test_data_catalog.DummyDataSource", "args": {"p": p}}
        cl, args = Catalog._parse_object(dct, create_object=False)

        assert cl == DummyDataSource
        assert args == {"p": p}

    def test_from_yaml(self):
        path = Path(__file__).parent / "config.yml"

        catalog = Catalog.from_yaml(path)

        assert len(catalog) == 2
        assert "dataframe" in catalog
        assert "pandas_sql" in catalog

        # pandas_sql
        sql_source = catalog["pandas_sql"]
        assert sql_source.sql == "select * from database.table"
        assert sql_source.con == "http://<your database url>"

        # dataframe
        expected_df = pd.DataFrame(
            {
                "x": [1.0, 2.0],
                "y": ["a", "b"],
            }
        )
        assert_frame_equal(expected_df, catalog["dataframe"].read())

    def test_from_yaml_with_jinja(self):
        path = Path(__file__).parent / "config_with_jinja.yml"

        params = {
            "pandas_sql": {"sql": "select * from database.table", "con": "http://<your database url>"},
            "dataframe": {"x": 4.0},
        }
        catalog = Catalog.from_yaml(path, parameters=params)

        assert len(catalog) == 2
        assert "dataframe" in catalog
        assert "pandas_sql" in catalog

        # pandas_sql
        sql_source = catalog["pandas_sql"]
        assert sql_source.sql == "select * from database.table"
        assert sql_source.con == "http://<your database url>"

        # dataframe
        expected_df = pd.DataFrame(
            {
                "x": [1.0, 4.0],
                "y": ["a", "b"],
            }
        )
        assert_frame_equal(expected_df, catalog["dataframe"].read())

    def test_from_yaml_with_validation(self):
        path = Path(__file__).parent / "config_with_validations.yml"

        catalog = Catalog.from_yaml(path)

        assert len(catalog) == 3
        assert "dataframe" in catalog
        assert "bad_dataframe" in catalog
        assert "pandas_sql" in catalog

        # pandas_sql
        sql_source = catalog["pandas_sql"]
        assert sql_source.sql == "select * from database.table"
        assert sql_source.con == "http://<your database url>"

        # dataframe
        expected_df = pd.DataFrame(
            {
                "x": [1.0, 2.0],
                "y": ["a", "b"],
            }
        )

        df = catalog.read("dataframe")
        assert_frame_equal(expected_df, df)

        with pytest_assert(AssertionError, "Nope!"):
            catalog.read("bad_dataframe")
