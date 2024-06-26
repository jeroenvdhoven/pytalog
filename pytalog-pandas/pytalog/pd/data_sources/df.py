import pandas as pd

from pytalog.base.data_sources.data_source import DataSource


class DataFrameSource(DataSource[pd.DataFrame]):
    def __init__(self, df: pd.DataFrame) -> None:
        """A DataSource based around a created DataFrame.

        Good for testing purposes, but please use other sources for actual usage.

        Args:
            df (pd.DataFrame): The DataFrame to use as a source.
        """
        super().__init__()
        self.df = df

    def read(self) -> pd.DataFrame:
        """Returns the DataFrame given as input before.

        Returns:
            pd.DataFrame: The DataFrame used to initialise this object.
        """
        return self.df
