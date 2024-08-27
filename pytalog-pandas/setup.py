from setuptools import find_namespace_packages, setup

if __name__ == "__main__":
    version = "0.1.0"

    deps = [
        f"pytalog-base=={version}",
        "pandas>=1.5.0",
        "openpyxl>=3.1.2",
        "pyarrow>=14.0.1",
        "numpy<2.0",
    ]
    strict_deps = [s.replace(">=", "==") for s in deps]

    setup(
        name="pytalog-pandas",
        install_requires=deps,
        extras_require={"dev": strict_deps, "strict": strict_deps},
        packages=find_namespace_packages(include=["pytalog.*"]),
        version=version,
    )
