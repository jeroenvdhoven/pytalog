from unittest.mock import MagicMock

from pytest import fixture

from pytalog.base.validation import ValidationSet


class TestValidationSet:
    @fixture
    def validations(self) -> ValidationSet:
        return ValidationSet(
            x=[
                MagicMock(),
                MagicMock(),
            ],
            y=[MagicMock()],
        )

    def test_not_present(self, validations: ValidationSet):
        validations.validate_data("z", 1)

        for vals in validations.values():
            for v in vals:
                v.validate.assert_not_called()

    def test_multiple_checks(self, validations: ValidationSet):
        data = 3
        validations.validate_data("x", data)

        for v in validations["y"]:
            v.validate.assert_not_called()
        for v in validations["x"]:
            v.validate.assert_called_once_with(data)
