import tomllib
from pathlib import Path
import da_vinci


def test_version_matches_pyproject():
    """Ensure __version__ matches pyproject.toml version."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    pyproject_version = pyproject["project"]["version"]

    assert da_vinci.__version__ == pyproject_version, \
        f"__version__ ({da_vinci.__version__}) must match pyproject.toml ({pyproject_version})"
