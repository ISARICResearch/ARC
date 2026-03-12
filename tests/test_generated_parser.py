import adtl
import pandas as pd
import tomli

from pathlib import Path
from schemas.draft_parser import generate_parser


def test_parser_format(tmp_path):
    file = tmp_path / "test_parser"
    generate_parser("test", filename=file)
    adtl.validate_specification(f"{file}.toml")


def test_arc_form_equality(tmp_path):
    file = tmp_path / "test_parser"
    generate_parser("test", filename=file)

    with Path(f"{file}.toml").open("rb") as fp:
        parser = tomli.load(fp)

    arc = pd.read_csv("ARC.csv")

    missing_forms = set(arc["Form"].unique().tolist()) - set(
        parser["adtl"]["defs"].keys()
    )

    assert not missing_forms, f"Missing forms in parser: {', '.join(missing_forms)}"
