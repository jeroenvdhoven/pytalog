from unittest.mock import MagicMock

from pytalog.spark.data_sources.spark import SparkFileSource


class TestSparkFileSource:
    def test_read(self):
        path = "some path"
        format = "__tmp__"
        args = {"a": 3, "index": False}
        mock_spark = MagicMock()

        source = SparkFileSource(path=path, format=format, spark_session=mock_spark, read_args=args)
        result = source.read()

        mock_spark.read.format.assert_called_once_with(format)
        mock_format = mock_spark.read.format.return_value

        mock_format.load.assert_called_once_with(path=path, **args)

        assert result == mock_format.load.return_value

    def test_write(self):
        path = "some path"
        format = "__tmp__"
        mode = "some mode"
        args = {"a": 3, "index": False}
        mock_spark = MagicMock()
        mock_df = MagicMock()

        source = SparkFileSource(path=path, format=format, spark_session=mock_spark, write_args=args, mode=mode)
        source.write(mock_df)

        mock_df.write.format.assert_called_once_with(format)
        mock_format = mock_df.write.format.return_value

        mock_format.mode.assert_called_once_with(mode)
        mock_mode = mock_format.mode.return_value

        mock_mode.option.assert_called_once_with("mergeSchema", True)
        mock_merge_option = mock_mode.option.return_value

        mock_merge_option.save.assert_called_once_with(path, **args)

    def test_overwrite(self):
        path = "some path"
        format = "__tmp__"
        mode = "overwrite"
        args = {"a": 3, "index": False}
        mock_spark = MagicMock()
        mock_df = MagicMock()

        source = SparkFileSource(path=path, format=format, spark_session=mock_spark, write_args=args, mode=mode)
        source.write(mock_df)

        mock_df.write.format.assert_called_once_with(format)
        mock_format = mock_df.write.format.return_value

        mock_format.mode.assert_called_once_with(mode)
        mock_mode = mock_format.mode.return_value

        mock_mode.option.assert_called_once_with("mergeSchema", True)
        mock_merge_option = mock_mode.option.return_value

        mock_merge_option.option.assert_called_once_with("overwriteSchema", True)
        mock_overwrite_option = mock_merge_option.option.return_value

        mock_overwrite_option.save.assert_called_once_with(path, **args)
