# tap-fulfil

This is a [Singer](https://singer.io) tap that produces JSON-formatted data
following the [Singer
spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md).

This tap:

- Pulls raw data from [Fulfil](https://www.fulfil.io)
- Extracts the following resources:
  - Contacts
  - Sales Orders
- Outputs the schema for each resource
- Incrementally pulls data based on the input state

## Installation

`pip install tap-fulfil`

From source code for development

```
git clone git@github.com:fulfilio/tap-fulfil.git
cd tap-fulfil
pip install -e .
```

## Adding more models (resources) to Tap

To add more resources, create a schema JSON file in the
schemas folder. This should be automatically discovered by
the script.

With every addition, remember to bump the version of the
tap.

---

Copyright &copy; 2018 Stitch

Copyright &copy; 2018 Fulfil.IO Inc.
