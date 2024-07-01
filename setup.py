from setuptools import find_namespace_packages, setup

setup(
    name="pytalog",
    packages=find_namespace_packages(include=["pytalog.*"]),
    python_requires=">=3.9",
    version="0.0.1",
    license="MIT",
    author="Jeroen van den Hoven",
    url="https://github.com/jeroenvdhoven/pytalog",
)
