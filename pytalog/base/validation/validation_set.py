import logging
from typing import Any, Dict, List, TypeVar

from pytalog.base.validation.validator import Validator

Data = TypeVar("Data")


class ValidationSet(Dict[str, List[Validator]]):
    def __init__(self, **kwargs: Any) -> None:
        """Validates data using customisable functions."""
        super().__init__(**kwargs)
        self.logger = logging.getLogger(__name__)

    def validate_data(self, name: str, data: Data) -> Data:
        """
        Method to validate data after reading from the data source or before writing to the data source.

        Args:
            table_name (str): Name of the table to validate.
            data (Data): Data source object.

        Raises:
            AssertionError: If any of the expectations fail.

        Returns:
            Data: Data source object.
        """
        if name in self.keys():
            self.logger.info(f">>> Validating data: {name}")
            for validation in self[name]:
                function_name = validation.get_name()

                self.logger.info(f">>> - For expectation: {function_name}")
                validation.validate(data)
                self.logger.info(f">>> - Expectation {function_name} passed!")

            self.logger.info(f"Table {name} validated successfully!")

        return data
