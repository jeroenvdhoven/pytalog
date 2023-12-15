from contextlib import contextmanager
from typing import Optional

import numpy as np
import pandas as pd


class AnyArg:
    def __eq__(self, __o: object) -> bool:
        return True


@contextmanager
def pytest_assert(error_class, message: Optional[str] = None, exact: bool = True):
    try:
        yield
        raise ValueError("No error was raised!")
    except error_class as e:
        if message is not None:
            error_message: str = e.args[0]
            if exact:
                assert error_message == message
            else:
                assert message in error_message


def are_dataframes_equal(
    expected: pd.DataFrame,
    result: pd.DataFrame,
    **kwargs,
) -> None:
    """Strongly recommended simplification of checking if 2 datasets are equal.

    Args:
        expected (pd.DataFrame): The expected DataFrame.
        result (pd.DataFrame): The testable DataFrame.
        kwargs: Any arguments to be passed to assert_frame_equal
    """
    assert expected.shape[1] == result.shape[1], f"Shapes, expected vs actual: {expected.shape[1]} != {result.shape[1]}"
    assert np.all(
        np.isin(expected.columns, result.columns)
    ), f"Missing columns: {expected.columns[~np.isin(expected.columns, result.columns)]}"

    # only sort on basic types. E.g. lists would fail.
    sort_cols = [
        col
        for col in expected.columns.tolist()
        if
        # not a list / dict / tuple
        (
            pd.api.types.is_string_dtype(expected[col])
            & (not any([isinstance(v, (list, dict, tuple)) for v in expected[col]]))
        )
        | pd.api.types.is_numeric_dtype(expected[col])
        | pd.api.types.is_bool(expected[col])
    ]
    pd.testing.assert_frame_equal(
        expected.sort_values(sort_cols).reset_index(drop=True),
        result[expected.columns].sort_values(sort_cols).reset_index(drop=True),
        **kwargs,
    )
