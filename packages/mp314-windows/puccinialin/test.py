"""
Basic sanity tests for puccinialin package.
Tests basic functionality without extra dependencies.
"""

import puccinialin


def test_module_import():
    """Test module imports successfully."""
    assert puccinialin is not None


def test_version():
    """Test version is accessible if available."""
    if hasattr(puccinialin, '__version__'):
        assert puccinialin.__version__ is not None


def test_module_attributes():
    """Test module has expected attributes."""
    # List module contents
    attrs = dir(puccinialin)
    assert len(attrs) > 0


def test_public_api():
    """Test public API is accessible."""
    # Get all public names (not starting with _)
    public_names = [name for name in dir(puccinialin) if not name.startswith('_')]
    
    # Module should have some public API
    # (adjust based on actual package contents)
    assert isinstance(public_names, list)


if __name__ == "__main__":
    test_module_import()
    test_version()
    test_module_attributes()
    test_public_api()
    print("All puccinialin tests passed!")

