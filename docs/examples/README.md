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

It also contains the `one-row-pp-covid.toml` parser, which is used to convert ISARIC's
existing one-row-per-patient processed Covid-19 dataset into the ISARIC schema. This file can be
used as an additional reference point, as well as the auto-generated parser(s) in the `schemas/` folder.

## Running the example

From the repository root:

```bash
pip install adtl
adtl parse docs/examples/example_parser.toml docs/examples/example_data.csv --include-transform schemas/isaric_transformations.py
```

See the [full tutorial](../sources/writing-a-parser.rst) and the
[ADTL documentation](https://adtl.readthedocs.io/en/latest/index.html) for details.
