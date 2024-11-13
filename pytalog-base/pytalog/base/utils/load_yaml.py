from pathlib import Path
from typing import Any, Dict, Union

import yaml
from jinja2 import Template

from pytalog.base.utils.load_object import load_object


def load_yaml_with_jinja(file_path: Union[str, Path], params: Dict[str, Any] = {}) -> Any:
    """Load a YAML file and apply jinja templating to it."""
    with open(file_path, "r") as file:
        file_content = file.read()
    rendered_file_content = _apply_jinja(file_content, params)
    return yaml.safe_load(rendered_file_content)


def _apply_jinja(string: str, configuration: Dict[str, Any]) -> str:
    """A basic wrapper to apply Jinga templating to a string.

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
        string (str): The string with Jinja formatting
        configuration (Dict[str, Any]): The configuration dict
            to use to replace values in the string.

    Returns:
        str: `string`, but with Jinja templating applied using the
            configuration dictionary.
    """
    template = Template(string)
    template.globals.update(call_func=_run_python_function_in_jinja)
    return template.render(configuration)


def _run_python_function_in_jinja(func_path: str, *args: Any, **kwargs: Any) -> Any:
    """Run a python function in a Jinja template."""
    func = load_object(func_path)
    return func(*args, **kwargs)
