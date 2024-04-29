from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeVar

Data = TypeVar("Data")


class Validator:
    def __init__(self, callable: Callable[..., None], **kwargs: Any) -> None:
        """A class that validates incomming data.

        The data is validated using the function and kwargs provided to it.
        For a class-based version of this, see ValidatorObject.

        Args:
            callable (Callable[..., None]): The function to use in data evaluation.
            kwargs (Any): keyword arguments to be passed to the function besides the data.
        """
        self.kwargs = kwargs
        self.callable = callable

    def validate(self, data: Any) -> None:
        """Validates if the given data meets this validation setup.

        This should raise an Error if the data does not meet the criteria.

        Args:
            data (Data): The data to be checked.
        """
        self.callable(data, **self.kwargs)

    def get_name(self) -> str:
        """Return the name of this validator.

        By default, this is the name of the function.
        """
        return self.callable.__name__


class ValidatorObject(Generic[Data], Validator, ABC):
    def __init__(self) -> None:
        """A validator that can be used to instantiate validations as objects.

        This allows you to potentially store results.
        """
        super().__init__(callable=self._validate)

    @abstractmethod
    def _validate(self, data: Data) -> None:
        """Validates if the given data meets this validation setup.

        This should raise an Error if the data does not meet the criteria.

        Args:
            data (Data): The data to be checked.
        """
        raise NotImplementedError

    def get_name(self) -> str:
        """Return the name of this validator.

        For ValidatorObject's, this is the name of the class.
        """
        return self.__class__.__name__
