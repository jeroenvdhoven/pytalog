import logging
from typing import Any, Dict, List, TypeVar

from pytalog.base.validation.validator import Validator

Data = TypeVar("Data")


class ValidationSet(Dict[str, List[Validator]]):
    def __init__(self, **kwargs: Any) -> None:
        """Provides a set of data validations.

        Args:
            **kwargs (Any): name-Validation pairs of dataset names and the corresponding list
                of data validations.
        """
        super().__init__(**kwargs)
        self.logger = logging.getLogger(__name__)

    def validate_data(self, name: str, data: Data) -> Data:
        """
        Method to validate data after reading from the data source or before writing to the data source.

        Args:
            name (str): Name of the dataset to validate. Only used in logging.
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
