from setuptools import find_namespace_packages, setup

if __name__ == "__main__":
    version = "0.1.1"

    deps = [
        f"pytalog-base=={version}",
        # We will provide absolute no guarantees that our integration will work with
        # EVERY version of pyspark. This has been developed under pyspark==3.2.1.
        "pyspark>=3.2.1",
    ]
    strict_deps = [s.replace(">=", "==") for s in deps]
    test_deps = ["pandas"]

    setup(
        name="pytalog-spark",
        install_requires=deps,
        extras_require={"dev": strict_deps + test_deps, "test": strict_deps + test_deps, "strict": strict_deps},
        packages=find_namespace_packages(include=["pytalog.*"]),
        version=version,
    )
