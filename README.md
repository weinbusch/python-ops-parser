# Python OPS Parser

A parser for EPO OPS XML files.

## Usage

```python
from python_ops_parser import xml_tree, world_patent_data

# Let xml_string be a string containing a EPO OPS XML file
tree = xml_tree(xml_string)
data = world_patent_data(tree)
```

`world_patent_data` is the top level parser for parsing the EPO OPS
XML tree. It returns a `dict` representing the OPS data.

This is how you extract the first register document:

```python
doc = data["register_search"]["register_documents"][0]
```

`doc` is another `dict`. For details on how to use the `doc`
dictionary, refer to the tests.


## Testing

First, download all sample xml data from OPS:

```bash
$ python test download-all
```

Then, run tests with `pytest`:

```bash
$ pytest .
```
