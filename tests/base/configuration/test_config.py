from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from pytest import fixture

from pytalog.base.configuration.config import read_config, read_config_and_catalog
from pytalog.pd.data_sources.sql import SqlSource


@fixture
def this_folder() -> Path:
    return Path(__file__).parent


@dataclass
class SqlConfig:
    sql: str
    con: str


@dataclass
class DataFrameConfig:
    x: float


@dataclass
class DummyConfig:
    pandas_sql: SqlConfig
    dataframe: DataFrameConfig

    @classmethod
    def from_config(cls, config: dict) -> "DummyConfig":
        return cls(
            pandas_sql=SqlConfig(**config["pandas_sql"]),
            dataframe=DataFrameConfig(**config["dataframe"]),
        )


class Test_read_config_and_catalog:
    def test_config(self, this_folder: Path):
        config, catalog = read_config_and_catalog(
            parameters_paths=[this_folder / "base_config.yml"],
            catalog_path=this_folder / "catalog.yml",
        )

        expected_dict = {
            "pandas_sql": {"sql": "select my from table", "con": "http://<your database url>"},
            "dataframe": {"x": 9.0},
        }

        assert config == expected_dict
        assert len(catalog) == 2

        sql = catalog["pandas_sql"]
        assert isinstance(sql, SqlSource)
        assert sql.sql == "select my from table"
        assert sql.con == "http://<your database url>"

        x = catalog.read("dataframe")
        expected_df = pd.DataFrame({"x": [1.0, 9.0], "y": ["a", "b"]})
        pd.testing.assert_frame_equal(expected_df, x)

    def test_config_multi_path(self, this_folder: Path):
        config, catalog = read_config_and_catalog(
            parameters_paths=[this_folder / "base_config.yml", this_folder / "extra_config.yml"],
            catalog_path=this_folder / "catalog.yml",
        )

        expected_dict = {
            "pandas_sql": {"sql": "select a different thing from table", "con": "http://<your database url>"},
            "dataframe": {"x": 9.0},
        }

        assert config == expected_dict
        assert len(catalog) == 2

        sql = catalog["pandas_sql"]
        assert isinstance(sql, SqlSource)
        assert sql.sql == "select a different thing from table"
        assert sql.con == "http://<your database url>"

        x = catalog.read("dataframe")
        expected_df = pd.DataFrame({"x": [1.0, 9.0], "y": ["a", "b"]})
        pd.testing.assert_frame_equal(expected_df, x)

    def test_config_optional_path(self, this_folder: Path):
        config, catalog = read_config_and_catalog(
            parameters_paths=[this_folder / "base_config.yml"],
            optional_parameters_paths=[this_folder / "optional_config.yml", this_folder / "missing_config.yml"],
            catalog_path=this_folder / "catalog.yml",
        )

        expected_dict = {
            "pandas_sql": {"sql": "select my from table", "con": "http://<your database url>"},
            "dataframe": {"x": 3.4},
        }

        assert config == expected_dict
        assert len(catalog) == 2

        sql = catalog["pandas_sql"]
        assert isinstance(sql, SqlSource)
        assert sql.sql == "select my from table"
        assert sql.con == "http://<your database url>"

        x = catalog.read("dataframe")
        expected_df = pd.DataFrame({"x": [1.0, 3.4], "y": ["a", "b"]})
        pd.testing.assert_frame_equal(expected_df, x)

    def test_config_converter(self, this_folder: Path):
        config, catalog = read_config_and_catalog(
            parameters_paths=[this_folder / "base_config.yml"],
            catalog_path=this_folder / "catalog.yml",
            config_converter=DummyConfig.from_config,
        )

        expected_res = DummyConfig(
            pandas_sql=SqlConfig(sql="select my from table", con="http://<your database url>"),
            dataframe=DataFrameConfig(x=9.0),
        )

        assert config == expected_res
        assert len(catalog) == 2

        sql = catalog["pandas_sql"]
        assert isinstance(sql, SqlSource)
        assert sql.sql == "select my from table"
        assert sql.con == "http://<your database url>"

        x = catalog.read("dataframe")
        expected_df = pd.DataFrame({"x": [1.0, 9.0], "y": ["a", "b"]})
        pd.testing.assert_frame_equal(expected_df, x)

    def test_config_initialised_params(self, this_folder: Path):
        ip = {"a": 34}

        with patch("pytalog.base.configuration.config.Catalog.from_yaml") as mock_from_yaml:
            read_config_and_catalog(
                parameters_paths=[this_folder / "base_config.yml"],
                catalog_path=this_folder / "catalog.yml",
                config_converter=DummyConfig.from_config,
                initialised_parameters=ip,
            )
        mock_from_yaml.assert_called_once_with(
            path=this_folder / "catalog.yml",
            parameters={
                "pandas_sql": {
                    "sql": "select my from table",
                    "con": "http://<your database url>",
                },
                "dataframe": {"x": 9.0},
            },
            initialised_parameters=ip,
        )


def test_read_config(this_folder: Path):
    config = read_config(
        parameters_paths=[this_folder / "base_config.yml"],
        optional_parameters_paths=[this_folder / "optional_config.yml", this_folder / "missing_config.yml"],
    )

    expected_dict = {
        "pandas_sql": {"sql": "select my from table", "con": "http://<your database url>"},
        "dataframe": {"x": 3.4},
    }

    assert config == expected_dict


def test_read_config_with_conversion(this_folder: Path):
    config = read_config(
        parameters_paths=[this_folder / "base_config.yml"],
        optional_parameters_paths=[this_folder / "optional_config.yml", this_folder / "missing_config.yml"],
        config_converter=DummyConfig.from_config,
    )

    expected_config = DummyConfig(
        pandas_sql=SqlConfig(sql="select my from table", con="http://<your database url>"),
        dataframe=DataFrameConfig(x=3.4),
    )

    assert config == expected_config
