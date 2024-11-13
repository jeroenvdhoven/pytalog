import importlib
from typing import Callable


def load_object(full_path: str) -> Callable:
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
    callable_ = getattr(module, class_path)

    # Return the method if that was requested, otherwise just return the class.
    if len(method_split) > 1:
        return getattr(callable_, method_split[1])
    else:
        return callable_
