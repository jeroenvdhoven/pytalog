from typing import Any

from pytalog.base.validation import Validator, ValidatorObject
from tests.utils import pytest_assert


def dummy_check(i: int, z: int):
    assert i < z, "Nope!"


class DummyValidator(ValidatorObject):
    def __init__(self, z: int) -> None:
        super().__init__()
        self.z = z

    def _validate(self, data: Any) -> None:
        assert data < self.z, "Nope!"


class TestValidator:
    def test_validate(self):
        validator = Validator(callable=dummy_check, z=4)

        validator.validate(2)

        with pytest_assert(AssertionError, "Nope!", exact=False):
            validator.validate(10)

    def test_get_name(self):
        validator = Validator(callable=dummy_check, z=4)

        assert validator.get_name() == "dummy_check"


class TestValidatorObject:
    def test_validate(self):
        validator = DummyValidator(z=4)

        validator.validate(2)

        with pytest_assert(AssertionError, "Nope!", exact=False):
            validator.validate(10)

    def test_get_name(self):
        validator = DummyValidator(z=4)

        assert validator.get_name() == "DummyValidator"
