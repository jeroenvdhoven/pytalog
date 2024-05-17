# Pytalog

This project focusses on making data catalogs, allowing you to define a jinja-temlated YAML file that you can use to read in data.
This has a few advantages:
- A single way of reading (and writing) your datasets, without having to know how exactly they are read, allows people to
    more easily onboard on new projects, since all datasets are defined in the catalog YAML.
- Templating allows you to swap between different environments, configurations, etc. without having to change your catalog file.
    This setup is hierarchical, allowing top-level config yamls to template lower levels, creating a manageable hierarchy of configuration.

## Usage

### The Catalog file
You can define a catalog YAML file as a starting point. The structure is as follows:
```yaml
<dataset name>:
    callable: <python path to class, method on a class, or function. Should produce a pytalog.base.data_sources.DataSource.
    args:
        <name of argument 1>: <value 1>
        <name of argument 2>: <value 2>
    validations:
        - callable: <python path to a ValidatorObject class or function that takes a dataset and kwargs>
            args:
                <name of argument>: <value>
```
The core consists of :
- The name of the dataset. This will be used later to read in your data.
- The `callable`. This is a path to a python importable class or function. When called with the args in `args`, it should return a `DataSource`.
- The `args`. These are values that will be passed to the `callable` to create the final `DataSource`. Values can be a plain value (like string, bool, etc) or a complex object. These will follow the same format as the callable-args structure of the DataSource's, but don't need to be DataSource's. They can be arbitrary python objects instead.


`DataSource`s are *not* the data itself: they are the *method* for obtaining the data. For instance, a SQL based `DataSource` would contain
the SQL query, database connection string, etc, but it would only execute
the query when you actually call the `.read()` method on the class. This
allows you to make a very lightweight and quickly imported catalog that has access to all the data in your project.

The data validations are an optional part. If present, these will be executed every time you read the dataset. Consider them a useful tool to
preemptively find potential issues with your data before doing anything else. They should all take one dataset as input and extra keyword arguments
(defaults) can be provided using the `args` part.

An example of a catalog is the following:
```yaml
pandas_sql:
  # please make sure the class is an importable callable
  # this can be a class constructor or a function.
  callable: pytalog.pd.data_sources.SqlSource
  args:
    sql: select * from database.table
    con: http://<your database url>
dataframe:
  # This will create a fixed DataFrame to read using this source.
  callable: pytalog.pd.data_sources.DataFrameSource
  args:
    df:
      # We can instantiate complex objects in the same way 
      # DataSource's are instantiated:
      callable: pandas.DataFrame
      args:
        data:
          x: 
            - 1.0
            - 2.0
          y:
            - "a"
            - "b"
```

These catalog can be 

### Reading in a Catalog
Say you have stored a `catalog.yaml` file like the one above. Then you can create a catalog and read data from it using:
```python
from pytalog.base.catalog import Catalog

catalog = Catalog.from_yaml("catalog.yaml")

# To read a dataset:
data = catalog.read("dataframe")
```

### Adding configuration
It is quite common to have different locations, paths, URL, etc depending on a dev/prod environment configuration. You can also imagine other parts of your solution that can change where data can be found or how it should be read in, like a country-level configuration. For this, `pytalog` gives options as well through Jinja templating:

```yaml
# The catalog:
pandas_sql:
  # please make sure the class is an importable callable
  # this can be a class constructor or a function.
  callable: pytalog.pd.data_sources.SqlSource
  args:
    sql: select * from database.table
    con: {{ database_connection }}
dataframe:
  # This will create a fixed DataFrame to read using this source.
  callable: pytalog.pd.data_sources.DataFrameSource
  args:
    df:
      # We can instantiate complex objects in the same way 
      # DataSource's are instantiated:
      callable: pandas.DataFrame
      args:
        data:
          x: 
            - 1.0
            - {{dataframe.x}}
          y:
            - "a"
            - "b"
```
And in python:
```python
from pytalog.base.catalog import Catalog

catalog = Catalog.from_yaml(
    "catalog.yaml", 
    parameters={
        "database_connection": "http://connection",
        "dataframe": {"x": 10}
    }
)

# To read a dataset:
data = catalog.read("dataframe")
```

The values you provide in `parameters` are automatically templated into the catalog file before loading it in. Keep in mind that this method is limited to the complexity that Jinja allows: complex Python objects can't be effectively passed to the `parameters` argument since they'll be stringified and inserted into the YAML file before being read back in.

### The Configuration object
This `parameters` would still leave you with the responsibility of reading in the parameters, doing any hierarchical processing, and then passing it all on to the Catalog object. To solve this, there is the Configuration object, which you can provide with multiple configuration YAML files and a catalog file. In turn, it provides you with the hierarchically templated configuration object and resulting Catalog:

```yaml
# Environment config
env: dev
database_connection: http://dev-database.now
```

```yaml
# Base configuration that uses info from the environment config
database_name: database-{{ env }}
dataframe:
    x: 2.5
```

```yaml
# The catalog:
pandas_sql:
  # please make sure the class is an importable callable
  # this can be a class constructor or a function.
  callable: pytalog.pd.data_sources.SqlSource
  args:
    sql: select * from {{ database_name }}.table
    con: {{ database_connection }}
dataframe:
  # This will create a fixed DataFrame to read using this source.
  callable: pytalog.pd.data_sources.DataFrameSource
  args:
    df:
      # We can instantiate complex objects in the same way 
      # DataSource's are instantiated:
      callable: pandas.DataFrame
      args:
        data:
          x: 
            - 1.0
            - {{dataframe.x}}
          y:
            - "a"
            - "b"
```

This can be loaded in using the Configuration object:

```python
from pytalog.base.configuration.config import Configuration

# This will contain 2 objects: 
# - a config dictionary, for all (parsed) configuration
# - a Catalog object based on the catalog.yaml
cf = Configuration.from_hierarchical_config(
    parameters_paths=["environment.yaml", "base.yaml"],
    catalog_path="catalog.yaml",
)

catalog = cf.catalog

# To read a dataset:
data = catalog.read("dataframe")
```

I'd recommend using the Configuration object to get started to give you as much flexibility as possible when using your catalog file.