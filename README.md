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

---

Copyright &copy; 2018 Stitch
Copyright &copy; 2018 Fulfil.IO Inc.
