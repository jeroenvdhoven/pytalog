import importlib
import inspect
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union

import yaml
from jinja2 import Template

from pytalog.base.catalog.dataset import DataSet
from pytalog.base.data_sources import DataSource
from pytalog.base.data_sources.data_source import WriteableDataSource
from pytalog.base.validation import ValidationSet, Validator, ValidatorObject

Data = TypeVar("Data")


class Catalog(Dict[str, DataSource[Data]]):
    def __init__(self, *args: Any, validation_set: Optional[ValidationSet] = None, **kwargs: Any):
        """A collection of data_sources that together form a DataSet when loaded."""
        super().__init__(*args, **kwargs)

        if validation_set is None:
            validation_set = ValidationSet()
        self.validation_set = validation_set

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

    def read(self, name: str, skip_validation: bool = False) -> Data:
        """Read a particular dataset from this Catalog.

        Args:
            name (str): The name of the dataset to read.
            skip_validation (bool): Boolean indicating if validation needs to be skipped.
                Useful when debugging your dataset.

        Returns:
            Data: The data returned by the DataSource tied to `name`.
        """
        data = self[name].read()
        if not skip_validation:
            self.validation_set.validate_data(name, data)
        return data

    def write(self, name: str, data: Data) -> None:
        """Write a particular dataset to this Catalog.

        Args:
            name (str): The name of the dataset to write.
            data (Data): The data to write.
        """
        writeable_source = self[name]
        assert isinstance(
            writeable_source, WriteableDataSource
        ), f"Can only write to a WriteableDataSource. Found {type(writeable_source)}"
        writeable_source.write(data)

    @classmethod
    def from_yaml(
        cls,
        path: Union[str, Path],
        parameters: Optional[Dict[str, Any]] = None,
        initialised_parameters: Optional[Dict[str, Any]] = None,
    ) -> "Catalog":
        """Read a catalog in from a configuration YAML file.

        We expect the following format:
        ```
        <dataset name>:
            callable: <python path to class, method on a class, or function.
                Should produce a DataSource.
            args:
                <name of argument>: <value>
            <optional parts>
            validations:
                - callable: <python path to a ValidatorObject class or function that takes a dataset and kwargs>
                  args:
                    <name of argument>: <value>
        ```

        The data validations are an optional part.

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

        Initialised objects can be passed as a dict using `initialised_parameters`. These will be
        passed to the callable as well if:
            - The same variable name appears in the arguments for that callable.
            - The same variable name doesn't appear already in the list of provided arguments for that callable.

        Args:
            path (Union[str, Path]): The path to the YAML file.
            parameters (Optional[Dict[str, Any]]): an optional set of parameters to be used to
                do jinja templating on the YAML file's strings.
            initialised_parameters (Optional[Dict[str, Any]]): Python objects that need to be available as well while
                loading the catalog. These variables will be passed to DataSource callables as well, following the
                conditions layed out above.

        Returns:
            Catalog: A Catalog with data_sources based on the YAML file.
        """
        data_sources = {}
        validation_set = ValidationSet()

        if parameters is None:
            parameters = {}
        if initialised_parameters is None:
            initialised_parameters = {}

        path = Path(path)
        with open(path, "r") as f:
            contents = f.read()

            parsed_contents = Template(contents).render(parameters)
            configuration = yaml.safe_load(parsed_contents)
        assert isinstance(configuration, dict), "Cannot process YAML as Catalog: should be a dictionary."

        for dataset_name, dataset_params in configuration.items():
            dataset = cls._parse_data_source(dataset_params, initialised_parameters)
            assert isinstance(
                dataset, DataSource
            ), "Please make sure objects in your Catalog only translate to data_sources."
            data_sources[dataset_name] = dataset

            if "validations" in dataset_params:
                validations_raw = dataset_params["validations"]
                assert isinstance(validations_raw, list)

                validation_set[dataset_name] = [cls._parse_validation(validation) for validation in validations_raw]

        return Catalog(validation_set=validation_set, **data_sources)

    @classmethod
    def _parse_data_source(cls, dct: Dict[str, Any], initialised_parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Creates a data source out of the dictionary."""
        return cls._parse_object(dct, create_object=True, initialised_parameters=initialised_parameters)

    @classmethod
    def _parse_validation(cls, dct: Dict[str, Any]) -> Validator:
        """Creates a Validator out of the dictionary."""
        callable, args = cls._parse_object(dct, create_object=False)
        if inspect.isclass(callable):
            assert issubclass(callable, ValidatorObject)
            return callable(**args)
        else:
            return Validator(callable=callable, **args)

    @classmethod
    def _parse_object(
        cls,
        dct: Dict[str, Any],
        create_object: bool,
        initialised_parameters: Optional[Dict[str, Any]] = None,
    ) -> Union[Any, Tuple[Callable, Dict[str, Any]]]:
        """Recursively parse a complex dictionary to create objects.

        This has 2 options:
            - create_object=True: Creates objects out of the parsed data.
            - create_object=False: Only returns the function and arguments required to create the object.
        This only returns the function and the arguments. You can combine the 2 to create

        Args:
            dct (Dict[str, Any]): A dictionary containing 2 fields:
                - callable: A python path to a class or static/class method on a class.
                    Used to initiate the object.
                - args: a dictionary of args to instantiate the object with or call the
                    method with. Can be another complex object.
            create_object (bool): Whether to create the object or just return the function and arguments.
            initialised_parameters (Optional[Dict[str, Any]]): Python objects that may to be available as well while
                loading an object.

        Returns:
            Union[Any, Tuple[Callable, Dict[str, Any]]]: This returns either:
                If create_object=True:
                    Tuple[Callable, Dict[str, Any]]:
                        - The callable function.
                        - The arguments to said function.
                Else:
                    Any: The object created by combining the function and arguments.
        """
        assert cls._is_valid_parseable_object(
            dct
        ), "Catalog: any dictionary parsed should have a `callable` and `args` entry."

        callable_ = cls._load_class(dct["callable"])
        args = dct["args"]
        assert isinstance(args, dict), "Arguments to a parseable object should be a dict."

        if initialised_parameters is None:
            initialised_parameters = {}

        # Parse arguments recursively
        parsed_args = {}
        for arg_name, arg_value in args.items():
            if cls._is_valid_parseable_object(arg_value):
                parsed_value = cls._parse_object(arg_value, create_object=True)
            else:
                parsed_value = arg_value

            parsed_args[arg_name] = parsed_value

        # Only add a initialised parameter if:
        # 1. it matches an argument name in this callable
        # 2. AND it doesn't have a value yet.
        argspec = inspect.getfullargspec(callable_)
        for arg_name in argspec[0]:
            if arg_name in initialised_parameters and arg_name not in parsed_args:
                parsed_args[arg_name] = initialised_parameters[arg_name]

        if create_object:
            return callable_(**parsed_args)
        else:
            return callable_, parsed_args

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
        if not isinstance(dct, dict):
            return False
        opts = [["callable", "args"], ["callable", "args", "validations"]]

        return any([len(dct) == len(opt) and all([p in dct for p in opt]) for opt in opts])
