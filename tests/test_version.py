"""Test version information."""

from venv_py import __version__


def test_version():
    """Test version is a string."""
    assert isinstance(__version__, str)
