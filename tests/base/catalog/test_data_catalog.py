from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
from pandas.testing import assert_frame_equal
from pytest import mark

from pytalog.base.catalog import Catalog, DataSet
from pytalog.base.data_sources.data_source import DataSource, WriteableDataSource
from tests.utils import pytest_assert


class DummyDataSource(WriteableDataSource[int]):
    def __init__(self, v: int) -> None:
        super().__init__()
        self.v = v

    def read(self) -> int:
        return self.v

    @staticmethod
    def dummy_method(p):
        return p + 5

    def write(self, value: int) -> None:
        self.v = value


class PreInitSource(DataSource[float]):
    def __init__(self, a: int, alt: dict) -> None:
        super().__init__()
        self.a = a
        self.alt = alt

    def read(self) -> float:
        return self.a + self.alt["b"]


def dummy_func(a, b, *c, **d):
    return a + b


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

    def test_pre_initialised_parse_object(self):
        a = 2
        dct = {"callable": "tests.base.catalog.test_data_catalog.PreInitSource", "args": {}}
        result = Catalog._parse_object(dct, create_object=True, initialised_parameters={"alt": {"b": 932}, "a": a})

        assert isinstance(result, PreInitSource)
        assert result.read() == 932 + a

    def test_pre_initialised_parse_object_ignore_unnecessary_values(self):
        a = 2
        dct = {"callable": "tests.base.catalog.test_data_catalog.PreInitSource", "args": {}}
        result = Catalog._parse_object(
            dct, create_object=True, initialised_parameters={"alt": {"b": 932}, "a": a, "c": 32984}
        )

        assert isinstance(result, PreInitSource)
        assert result.read() == 932 + a

    def test_pre_initialised_parse_object_skip_present_values(self):
        a = 2
        #  'a' in dict is more important.
        dct = {"callable": "tests.base.catalog.test_data_catalog.PreInitSource", "args": {"a": a}}
        result = Catalog._parse_object(dct, create_object=True, initialised_parameters={"alt": {"b": 932}, "a": 23789})

        assert isinstance(result, PreInitSource)
        assert result.read() == 932 + a

    def test_pre_initialised_parse_object_ignore_kwargs(self):
        a = 2
        b = 9
        dct = {"callable": "tests.base.catalog.test_data_catalog.dummy_func", "args": {}}
        result = Catalog._parse_object(dct, create_object=True, initialised_parameters={"a": a, "b": b, "c": 2, "d": 0})

        assert result == b + a

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

    def test_from_yaml_with_jinja_and_preinitialised_values(self):
        path = Path(__file__).parent / "config_with_jinja_and_inits.yml"

        params = {
            "pandas_sql": {"sql": "select * from database.table", "con": "http://<your database url>"},
            "extra": {"a": 3},
        }
        initialised = {
            "alt": {"b": 4.0},
        }
        catalog = Catalog.from_yaml(path, parameters=params, initialised_parameters=initialised)

        assert len(catalog) == 2
        assert "extra" in catalog
        assert "pandas_sql" in catalog

        # pandas_sql
        sql_source = catalog["pandas_sql"]
        assert sql_source.sql == "select * from database.table"
        assert sql_source.con == "http://<your database url>"

        # extra
        expected_result = params["extra"]["a"] + initialised["alt"]["b"]
        assert expected_result == catalog["extra"].read()

    def test_from_yaml_with_jinja_and_functions(self):
        path = Path(__file__).parent / "config_with_jinja_and_functions.yml"

        params = {
            "pandas_sql": {"sql": "select * from database.table", "con": "http://<your database url>"},
            "extra": {"a": 3},
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
                "x": [1.0, 2.0],
                "y": ["15", "b"],
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

    def test_write(self):
        catalog = Catalog(name=DummyDataSource(8))

        assert catalog.read("name") == 8
        catalog.write("name", 9)
        assert catalog.read("name") == 9

    def test_write_assert(self):
        catalog = Catalog(name=PreInitSource(8, alt={"b": 9}))

        with pytest_assert(AssertionError, f"Can only write to a WriteableDataSource. Found {PreInitSource}"):
            catalog.write("name", 9)
