---
orphan: true
---

# Example: mapping a COVID-19 dataset to the ISARIC schema

This folder contains the example files for the
[Writing a Custom Parser](../sources/writing-a-parser.rst) tutorial in the ARC documentation.

| File | Description |
|------|-------------|
| `example_data.csv` | Synthetic COVID-19 source dataset (5 patients) |
| `example_parser.toml` | Worked ADTL parser mapping to the ISARIC core and long tables |
| `covid-study-core.csv` | Expected core table output (one row per patient) |
| `covid-study-long.csv` | Expected long table output (one row per observation) |

## Running the example

From the repository root:

```bash
pip install adtl
adtl docs/examples/example_parser.toml docs/examples/example_data.csv
```

See the [full tutorial](../sources/writing-a-parser.rst) and the
[ADTL documentation](https://adtl.readthedocs.io/en/latest/index.html) for details.
