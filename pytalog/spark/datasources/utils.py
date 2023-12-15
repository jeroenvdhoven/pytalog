from typing import Optional

from pyspark.sql import SparkSession


def guarantee_spark(spark: Optional[SparkSession] = None) -> SparkSession:
    """Guarantees a spark session is returned.

    Returns the same spark session if it's not None and SparkSession object.
    Otherwise, get the currently activate session.

    Args:
        spark (Optional[SparkSession], optional): _description_. Defaults to None.

    Returns:
        SparkSession: _description_
    """
    if spark is None:
        spark = SparkSession.getActiveSession()
    assert spark is not None, "SparkSession was not properly initialised."
    return spark
