import pytest
from schemas.isaric_schema import generate_long_schema


@pytest.mark.critical
def test_generate_long_schema_runs(tmp_path):
    # Check schema generation runs with no errors and creates a file
    output = tmp_path / "arc_test_isaric_long.schema.json"
    generate_long_schema("test", output_path=output)
    assert output.exists()
