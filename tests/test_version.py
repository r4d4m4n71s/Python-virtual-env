"""Test version information."""

from virtual_env import __version__


def test_version():
    """Test version is a string."""
    assert isinstance(__version__, str)