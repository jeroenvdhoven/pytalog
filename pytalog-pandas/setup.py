import sys
from setuptools import find_namespace_packages, setup

if __name__ == "__main__":
    version = "0.0.1"

    deps = [
        f"pytalog-base=={version}",
        "pandas>=1.4.3",
        "openpyxl>=3.1.2",
        "pyarrow>=14.0.1",
    ]
    strict_deps = [s.replace(">=", "==") for s in deps]

    python_version = sys.version_info
    if python_version[0] == 3 and python_version[1] == 9:
        # Older python can't handle pandas 1.4.3 and numpy >= 2
        strict_deps.append("numpy<2.0")

    setup(
        name="pytalog-pandas",
        install_requires=deps,
        extras_require={"dev": strict_deps, "strict": strict_deps},
        packages=find_namespace_packages(include=["pytalog.*"]),
        version=version,
    )
