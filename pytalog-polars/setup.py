from setuptools import find_namespace_packages, setup

if __name__ == "__main__":
    version = "0.1.0"

    deps = [f"pytalog-base=={version}", "polars>=1.1.0"]
    strict_deps = [s.replace(">=", "==") for s in deps]
    dev_deps = ["xlsxwriter==3.2.0", "fastexcel==0.11.5", "sqlalchemy==2.0.31"]

    setup(
        name="pytalog-polars",
        install_requires=deps,
        extras_require={"dev": strict_deps + dev_deps, "strict": strict_deps},
        packages=find_namespace_packages(include=["pytalog.*"]),
        version=version,
    )
