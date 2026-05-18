"""
Basic sanity tests for meson-python package.
Tests meson-python build backend functionality without extra dependencies.
"""

import mesonpy


def test_version():
    """Test version is accessible."""
    assert hasattr(mesonpy, '__version__')
    assert mesonpy.__version__ is not None


def test_module_import():
    """Test module imports successfully."""
    assert mesonpy is not None


def test_build_backend_interface():
    """Test PEP 517 build backend interface exists."""
    # meson-python should provide these PEP 517 hooks
    assert hasattr(mesonpy, 'build_wheel')
    assert hasattr(mesonpy, 'build_sdist')
    assert callable(mesonpy.build_wheel)
    assert callable(mesonpy.build_sdist)


def test_get_requires_for_build_wheel():
    """Test get_requires_for_build_wheel hook."""
    if hasattr(mesonpy, 'get_requires_for_build_wheel'):
        requires = mesonpy.get_requires_for_build_wheel()
        assert isinstance(requires, list)


def test_get_requires_for_build_sdist():
    """Test get_requires_for_build_sdist hook."""
    if hasattr(mesonpy, 'get_requires_for_build_sdist'):
        requires = mesonpy.get_requires_for_build_sdist()
        assert isinstance(requires, list)


def test_prepare_metadata():
    """Test prepare_metadata_for_build_wheel hook exists."""
    if hasattr(mesonpy, 'prepare_metadata_for_build_wheel'):
        assert callable(mesonpy.prepare_metadata_for_build_wheel)


if __name__ == "__main__":
    test_version()
    test_module_import()
    test_build_backend_interface()
    test_get_requires_for_build_wheel()
    test_get_requires_for_build_sdist()
    test_prepare_metadata()
    print("All meson-python tests passed!")

