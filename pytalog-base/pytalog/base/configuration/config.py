from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

from pytalog.base.catalog import Catalog
from pytalog.base.utils.load_yaml import load_yaml_with_jinja
from pytalog.base.utils.logger import build_logger

ConfigClass = TypeVar("ConfigClass")


class Configuration(Generic[ConfigClass]):
    """A class to define project configuration and a data catalog in 1 go.

    Use `from_hierarchical_config` to initialise this class. This will allow you to stack
    different configuration files for different uses:
        - Development environment (dev, prod).
        - Common configuration.
        - Configuration for specific run versions.

    This allows you to flexibly switch between different environments and setups without
    elaborate manual steps.
    """

    config: Union[Dict, ConfigClass]
    catalog: Catalog

    def __init__(
        self,
        config: Union[Dict, ConfigClass],
        catalog: Catalog,
    ) -> None:
        """A class to help load project configuration and catalog in 1 go.

        We'd recommend to use `from_hierarchical_config` to initialise this class.

        Args:
            config (Union[Dict, ConfigClass]): The configuration object. Defaults to a dict,
                but you can type it if you want. If you don't want to use this, we'll type it as a dict.
            catalog (Catalog): The catalog object.
        """
        self.catalog = catalog
        self.config = config

    @classmethod
    def from_hierarchical_config(
        cls,
        parameters_paths: List[Path],
        catalog_path: Path,
        optional_parameters_paths: Optional[List[Path]] = None,
        config_converter: Optional[Callable[[Dict[str, Any]], ConfigClass]] = None,
    ) -> "Configuration[ConfigClass]":
        """Initialise the configuration and catalog from a hierarchical configuration.

        Args:
            parameters_paths (List[Path]): A list of parameter files. Each file will be jinja templated by the
                previous files and the environment file. Warning: if you import the same variable, the latest variable
                will be used!
            catalog_path (Path): Path to the catalog file. Will be jinja templated using the environment file and all
                parameter files.
            optional_parameters_paths (Optional[List[Path]]): Extra paths that contain optional parameters. If these
                files are not present, a warning will be issued, but no error will be thrown. Otherwise treated just
                like parameters_paths. This can be quite useful for testing purposes.
            config_converter (Optional[Callable[[Dict[str, Any]], T]], optional): A function to convert your config
                files. This can be useful to type your config. Defaults to None, meaning we don't convert anything.
        """
        logger = build_logger("from_hierarchical_config")

        if optional_parameters_paths is None:
            optional_parameters_paths = []

        # Load all parameter files in order.
        parameters: Dict[str, Any] = {}
        for param_path in parameters_paths:
            new_params = load_yaml_with_jinja(param_path, params=parameters.copy())
            parameters = cls._nested_update(parameters, new_params)

        for param_path in optional_parameters_paths:
            if param_path.exists():
                new_params = load_yaml_with_jinja(param_path, params=parameters.copy())
                parameters = cls._nested_update(parameters, new_params)

            else:
                logger.warning(f"Optional path {param_path} was not found.")

        # init global config without subconfigs
        config: Union[Dict, ConfigClass] = parameters
        if config_converter is not None:
            config = config_converter(parameters)

        # init catalog
        catalog = Catalog.from_yaml(
            path=catalog_path,
            parameters=parameters,
        )

        return cls(config=config, catalog=catalog)

    @classmethod
    def _nested_update(cls, d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = cls._nested_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d
