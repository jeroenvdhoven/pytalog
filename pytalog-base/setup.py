from setuptools import find_namespace_packages, setup

if __name__ == "__main__":
    version = "0.0.2"

    dev_deps = [
        "pre-commit",
        "build==0.8.0",
        "pypiserver==1.5.1",
        "twine==4.0.1",
        "pdoc==13.1.0",
        "importlib-metadata<8.0.0",
    ]
    test_deps = ["pytest", "pytest-cov"]
    deps = [
        "PyYAML==6.0.1",
        "jinja2==3.1.2",
    ]
    strict_deps = [s.replace(">=", "==") for s in deps]

    setup(
        name="pytalog-base",
        install_requires=deps,
        python_requires=">=3.9,<3.12",
        extras_require={
            "dev": strict_deps + dev_deps + test_deps,
            "test": strict_deps + test_deps,
            "strict": strict_deps,
        },
        packages=find_namespace_packages(include=["pytalog.*"]),
        version=version,
    )
