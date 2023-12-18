import importlib
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union

import yaml
from jinja2 import Template

from pytalog.base.catalog.dataset import DataSet
from pytalog.base.data_sources import DataSource

Data = TypeVar("Data")


class Catalog(Dict[str, DataSource[Data]]):
    """A collection of data_sources that together form a DataSet when loaded."""

    def read_all(self) -> DataSet:
        """Read all data_sources and generate a DataSet.

        Names of data_sources are preserved when loading the data.

        Returns:
            DataSet: The DataSet constructed from the data_sources.
        """
        return DataSet.from_dict({name: data.read() for name, data in self.items()})

    def __str__(self, indents: int = 0) -> str:
        """Create string representation of this Catalog.

        Args:
            indents (int, optional): The number of preceding tabs. Defaults to 0.

        Returns:
            str: A string representation of this Catalog.
        """
        tab = "\t" * indents
        return "\n".join([f"{tab}{name}: {source}" for name, source in self.items()])

    def read(self, name: str) -> Data:
        """Read a particular dataset from this Catalog.

        Args:
            name (str): The name of the dataset to read.

        Returns:
            Data: The data returned by the DataSource tied to `name`.
        """
        return self[name].read()

    @classmethod
    def from_yaml(cls, path: Union[str, Path], parameters: Optional[Dict[str, Any]] = None) -> "Catalog":
        """Read a catalog in from a configuration YAML file.

        We expect the following format:
        ```
        <dataset name>:
            callable: <python path to class, method on a class, or function.
                Should produce a DataSource.
            args:
                <name of argument>: <value>
        ```

        Values can be a plain value (like string, bool, etc) or a complex object.
        These will follow the same format as the callable-args structure of the
        DataSource's, but don't need to be DataSource's. e.g.:

        ```
        dataframe:
            callable: pytalog.sklearn.data.DataFrameSource
            args:
                df:
                    callable: pandas.DataFrame
                    args:
                        data:
                            x:
                                - 1.0
                                - 2.0
                            y:
                                - "a"
                                - "b"
        ```

        To use a method on a class, use `path.to.class:function`. This will only work for
        static or class methods.

        For security reasons, please make sure you trust any YAML file you read using this
        method! It will lead to code execution based on the imports, which can be abused.

        Parameters from the optional dictionary will be used for Jinja templating of
        strings in any of the arguments. To ensure non-string values are properly parsed,
        make sure they aren't surrounded by quotation marks in the YAML.

        Args:
            path (Union[str, Path]): The path to the YAML file.
            parameters (Optional[Dict[str, Any]]): an optional set of parameters to be used to
                do jinja templating on the YAML file's strings.

        Returns:
            Catalog: A Catalog with data_sources based on the YAML file.
        """
        data_sources = {}
        if parameters is None:
            parameters = {}

        path = Path(path)
        with open(path, "r") as f:
            contents = f.read()

            parsed_contents = Template(contents).render(parameters)
            configuration = yaml.safe_load(parsed_contents)
        assert isinstance(configuration, dict), "Cannot process YAML as Catalog: should be a dictionary."

        for dataset_name, dataset_params in configuration.items():
            dataset = cls._parse_object(dataset_params)
            assert isinstance(
                dataset, DataSource
            ), "Please make sure objects in your Catalog only translate to data_sources."
            data_sources[dataset_name] = dataset
        return Catalog(**data_sources)

    @classmethod
    def _parse_object(cls, dct: Dict[str, Any]) -> Any:
        """Recursively parse a complex dictionary to create objects.

        Args:
            dct (Dict[str, Any]): A dictionary containing 2 fields:
                - callable: A python path to a class or static/class method on a class.
                    Used to initiate the object.
                - args: a dictionary of args to instantiate the object with or call the
                    method with. Can be another complex object.

        Returns:
            Any: The object returned by calling `callable`
        """
        assert cls._is_valid_parseable_object(
            dct
        ), "Catalog: any dictionary parsed should have a `callable` and `args` entry."

        callable_ = cls._load_class(dct["callable"])
        args = dct["args"]
        assert isinstance(args, dict), "Arguments to a parseable object should be a dict."

        # Parse arguments recursively
        parsed_args = {}
        for arg_name, arg_value in args.items():
            if cls._is_valid_parseable_object(arg_value):
                parsed_value = cls._parse_object(arg_value)
            else:
                parsed_value = arg_value

            parsed_args[arg_name] = parsed_value

        return callable_(**parsed_args)

    @staticmethod
    def _load_class(full_path: str) -> Callable:
        """Load a callable from a Python import path.

        Supported functionality includes:
        - Importing a class, e.g. pandas.DataFrame.
        - Importing a static / class method, e.g. pytalog.base.catalog.Catalog:from_yaml

        Args:
            full_path (str): The path leading to the class or function to import.

        Returns:
            Callable: The class or function described in the `full_path` variable.
        """
        # check if we need to import a method.
        method_split = full_path.split(":")
        assert len(method_split) <= 2, f"{full_path}: Catalogs do not accept paths with more than 1 `:`"
        callable_path = method_split[0]

        # for importing we need to split out the last part of the string.
        split_path = callable_path.split(".")
        module_path = ".".join(split_path[:-1])
        class_path = split_path[-1]

        # Import the module and get the class.
        module = importlib.import_module(module_path)
        callable = getattr(module, class_path)

        # Return the method if that was requested, otherwise just return the class.
        if len(method_split) > 1:
            return getattr(callable, method_split[1])
        else:
            return callable

    @staticmethod
    def _is_valid_parseable_object(dct: Dict[str, Any]) -> bool:
        return isinstance(dct, dict) and len(dct) == 2 and "callable" in dct and "args" in dct
