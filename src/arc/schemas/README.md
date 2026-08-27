# Auto-generated schemas and parsers for ARC usage with ADTL

The two scripts in this file (`isaric_schema.py` and `draft_parser.py`) will auto-generate
a long table schema and a generic parser file for use with 
[ADTL](https://github.com/globaldothealth/adtl), respectively.

These scripts will run automatically when a new git tag is generated associated with a 
new ARC version. However, they can also be run manually should you wish to.

If you wish to generate a parser for a specific study which uses one of the ARC presets,
you can use this within the script to reduce the size of the generated file.