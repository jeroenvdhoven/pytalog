from unittest.mock import MagicMock, patch

from pytalog.spark.datasources.spark import SparkSqlSource


class Test_SparkSqlSource:
    def test(self):
        session = MagicMock()
        query = "select * from table"

        source = SparkSqlSource(query, session)
        result = source.read()

        session.sql.assert_called_once_with(query)
        assert result == session.sql.return_value

    def test_without_session(self):
        query = "select * from table"

        with patch("pytalog.spark.datasources.spark.SparkSession.getActiveSession") as mock_active_session:
            source = SparkSqlSource(query)
            result = source.read()

        mock_active_session.assert_called_once_with()
        session = mock_active_session.return_value

        session.sql.assert_called_once_with(query)
        assert result == session.sql.return_value
