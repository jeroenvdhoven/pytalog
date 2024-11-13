from pytalog.base.data_sources.data_source import DataSource
from pytalog.base.utils import load_object
from tests.utils import pytest_assert


def test_load_object():
    path = "pytalog.base.data_sources.DataSource"
    result = load_object(path)

    assert result == DataSource


def test_load_object_assert():
    path = "pytalog.base.data_sources.DataSource:read:failure"

    with pytest_assert(AssertionError, f"{path}: Catalogs do not accept paths with more than 1 `:`"):
        load_object(path)


def test_load_object_with_method():
    path = "pytalog.base.data_sources.DataSource:read"
    result = load_object(path)

    assert result == DataSource.read
