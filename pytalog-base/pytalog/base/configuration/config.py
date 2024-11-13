from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

from pytalog.base.catalog import Catalog
from pytalog.base.utils.load_yaml import load_yaml_with_jinja
from pytalog.base.utils.logger import build_logger

ConfigClass = TypeVar("ConfigClass")


def read_config_and_catalog(
    parameters_paths: List[Path],
    catalog_path: Path,
    optional_parameters_paths: Optional[List[Path]] = None,
    config_converter: Optional[Callable[[Dict[str, Any]], ConfigClass]] = None,
    initialised_parameters: Optional[Dict[str, Any]] = None,
) -> Tuple[Union[ConfigClass, Dict[str, Any]], Catalog]:
    """Initialise the configuration and catalog from a hierarchical configuration.

    This function will allow you to stack different configuration files for different uses:
        - Development environment (dev, prod).
        - Common configuration.
        - Configuration for specific run versions.

    This allows you to flexibly switch between different environments and setups without
    elaborate manual steps.

    These yaml files are also templated using Jinja, so you can reuse variables from
    already read files in subsequent files. This hierarchy is based on the order
    of the files in parameters_paths.

    We also provide the convenience function `call_func` to run
    python functions in a Jinja template. This is useful for doing
    operations on-the-fly, e.g. fetching secrets. Assume you have:
        - A python function in the file project/main.py called get_secrets
        - It requires a parameter called `name`
        - You want to fetch the secret called 'foo'.

    ```yaml
    - secret: {{ call_func('project.main.get_secrets', name='foo') }}
    ```

    Args:
        parameters_paths (List[Path]): A list of parameter files. Each file will be jinja templated by the
            previous files and the environment file. Warning: if you import the same variable, the latest variable
            will be used!
        catalog_path (Path): Path to the catalog file. Will be jinja templated using the environment file and all
            parameter files.
        optional_parameters_paths (Optional[List[Path]]): Extra paths that contain optional parameters. If these
            files are not present, a warning will be issued, but no error will be thrown. Otherwise treated just
            like parameters_paths. This can be quite useful for testing purposes.
        config_converter (Optional[Callable[[Dict[str, Any]], ConfigClass]], optional): A function to convert your
            config files. This can be useful to type your config. Defaults to None, meaning we don't convert
            anything.
        initialised_parameters (Optional[Dict[str, Any]]): Python objects that need to be available as well while
            loading the catalog. These will not be stored in the configuration object. This can be useful for
            objects like SparkSessions.

    Returns:
        Tuple[Union[ConfigClass, Dict[str, Any]], Catalog]: Consists of 2 objects:
            - The configuration object, typed if you provided `config_converter`. Otherwise, a dict.
            - The catalog object.
    """
    parameters = _read_config(
        parameters_paths=parameters_paths,
        optional_parameters_paths=optional_parameters_paths,
    )
    config = _convert_config(config=parameters, config_converter=config_converter)

    # init catalog
    catalog = Catalog.from_yaml(
        path=catalog_path,
        parameters=parameters,
        initialised_parameters=initialised_parameters,
    )

    return config, catalog


def read_config(
    parameters_paths: List[Path],
    optional_parameters_paths: Optional[List[Path]] = None,
    config_converter: Optional[Callable[[Dict[str, Any]], ConfigClass]] = None,
) -> Union[ConfigClass, Dict[str, Any]]:
    """Initialise the configuration from a hierarchical configuration.

    This function will allow you to stack different configuration files for different uses:
        - Development environment (dev, prod).
        - Common configuration.
        - Configuration for specific run versions.

    This allows you to flexibly switch between different environments and setups without
    elaborate manual steps.

    Args:
        parameters_paths (List[Path]): A list of parameter files. Each file will be jinja templated by the
            previous files and the environment file. Warning: if you import the same variable, the latest variable
            will be used!
        optional_parameters_paths (Optional[List[Path]]): Extra paths that contain optional parameters. If these
            files are not present, a warning will be issued, but no error will be thrown. Otherwise treated just
            like parameters_paths. This can be quite useful for testing purposes.
        config_converter (Optional[Callable[[Dict[str, Any]], ConfigClass]], optional): A function to convert your
            config files. This can be useful to type your config. Defaults to None, meaning we don't convert
            anything.

    Returns:
        Union[ConfigClass, Dict[str, Any]]: The configuration object as a dictionary, or as a typed object if
            you provided `config_converter`.
    """
    config = _read_config(
        parameters_paths=parameters_paths,
        optional_parameters_paths=optional_parameters_paths,
    )
    return _convert_config(config, config_converter)


def _read_config(
    parameters_paths: List[Path],
    optional_parameters_paths: Optional[List[Path]] = None,
) -> Dict[str, Any]:
    """Read the configuration from a hierarchical configuration.

    Args:
        parameters_paths (List[Path]): A list of parameter files. Each file will be jinja templated by the
            previous files and the environment file. Warning: if you import the same variable, the latest variable
            will be used!
        optional_parameters_paths (Optional[List[Path]]): Extra paths that contain optional parameters. If these
            files are not present, a warning will be issued, but no error will be thrown. Otherwise treated just
            like parameters_paths. This can be quite useful for testing purposes.

    Returns:
        Dict[str, Any]: _description_
    """
    logger = build_logger("from_hierarchical_config")

    if optional_parameters_paths is None:
        optional_parameters_paths = []

    # Load all parameter files in order.
    parameters: Dict[str, Any] = {}
    for param_path in parameters_paths:
        new_params = load_yaml_with_jinja(param_path, params=parameters.copy())
        parameters = _nested_update(parameters, new_params)

    for param_path in optional_parameters_paths:
        if param_path.exists():
            new_params = load_yaml_with_jinja(param_path, params=parameters.copy())
            parameters = _nested_update(parameters, new_params)

        else:
            logger.warning(f"Optional path {param_path} was not found.")
    return parameters


def _nested_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = _nested_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def _convert_config(
    config: Dict[str, Any], config_converter: Optional[Callable[[Dict[str, Any]], ConfigClass]] = None
) -> Union[ConfigClass, Dict[str, Any]]:
    if config_converter is not None:
        return config_converter(config)
    return config
