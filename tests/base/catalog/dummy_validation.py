import pandas as pd


def dummy_check(df: pd.DataFrame, z: int):
    assert all(df["x"] < z), "Nope!"
