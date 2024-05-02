from pathlib import Path
from typing import Any, Dict, Union

import yaml
from jinja2 import Template


def load_yaml_with_jinja(file_path: Union[str, Path], params: Dict[str, Any] = {}) -> Any:
    """Load a YAML file and apply jinja templating to it."""
    with open(file_path, "r") as file:
        file_content = file.read()
    rendered_file_content = _apply_jinja(file_content, params)
    return yaml.safe_load(rendered_file_content)


def _apply_jinja(string: str, configuration: Dict[str, Any]) -> str:
    """A basic wrapper to apply Jinga templating to a string.

    Please make sure any template strings are prefaced with `configs.`, e.g.
    `configs.content` if you wish to insert `content` from your configuration:

    "Will apply {{ configs.content }} by inserting `content`."

    Args:
        string (str): The string with Jinja formatting
        configuration (Dict[str, Any]): The configuration dict
            to use to replace values in the string.

    Returns:
        str: `string`, but with Jinja templating applied using the
            configuration dictionary.
    """
    return Template(string).render(configuration)
