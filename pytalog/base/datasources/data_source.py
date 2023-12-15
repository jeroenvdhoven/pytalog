from abc import ABC, abstractmethod
from typing import Generic, TypeVar

Data = TypeVar("Data")


class DataSource(ABC, Generic[Data]):
    """An abstract base class for a data source."""

    @abstractmethod
    def read(self) -> Data:
        """Read data from a given source.

        This method should be build ideally such that it provides consistent
        datasets every time it is called.

        Returns:
            Data: Data to be returned once read.
        """
        raise NotImplementedError


class DataSink(ABC, Generic[Data]):
    """An abstract base class for a way to write data."""

    @abstractmethod
    def write(self, data: Data) -> None:
        """Writes data to a given source."""
        raise NotImplementedError


class WriteableDataSource(DataSource[Data], DataSink[Data], ABC):
    """An abstract base class for a data source that can also be written to."""
