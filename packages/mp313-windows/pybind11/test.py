"""
Basic sanity tests for pybind11 package.
Tests that pybind11 is properly installed and accessible.
Note: pybind11 is a header-only library for creating Python bindings,
so we test its Python-side utilities and configuration.
"""

import pybind11
import os


def test_version():
    """Test version is accessible."""
    assert hasattr(pybind11, '__version__')
    assert pybind11.__version__ is not None
    assert len(pybind11.__version__) > 0


def test_get_include():
    """Test include path retrieval."""
    include_path = pybind11.get_include()
    assert include_path is not None
    assert os.path.isdir(include_path)
    
    # Check that pybind11.h exists
    pybind11_header = os.path.join(include_path, 'pybind11', 'pybind11.h')
    assert os.path.isfile(pybind11_header)


def test_get_cmake_dir():
    """Test CMake directory retrieval."""
    cmake_dir = pybind11.get_cmake_dir()
    assert cmake_dir is not None
    assert os.path.isdir(cmake_dir)


def test_header_files_exist():
    """Test that essential header files exist."""
    include_path = pybind11.get_include()
    pybind11_dir = os.path.join(include_path, 'pybind11')
    
    essential_headers = [
        'pybind11.h',
        'attr.h',
        'buffer_info.h',
        'cast.h',
        'chrono.h',
        'complex.h',
        'functional.h',
        'numpy.h',
        'operators.h',
        'options.h',
        'pytypes.h',
        'stl.h',
    ]
    
    for header in essential_headers:
        header_path = os.path.join(pybind11_dir, header)
        assert os.path.isfile(header_path), f"Missing header: {header}"


def test_detail_headers_exist():
    """Test that detail header files exist."""
    include_path = pybind11.get_include()
    detail_dir = os.path.join(include_path, 'pybind11', 'detail')
    
    assert os.path.isdir(detail_dir)
    
    detail_headers = [
        'common.h',
        'descr.h',
        'init.h',
        'internals.h',
        'type_caster_base.h',
        'typeid.h',
    ]
    
    for header in detail_headers:
        header_path = os.path.join(detail_dir, header)
        assert os.path.isfile(header_path), f"Missing detail header: {header}"


def test_stl_bind_headers():
    """Test STL bind headers exist."""
    include_path = pybind11.get_include()
    pybind11_dir = os.path.join(include_path, 'pybind11')
    
    stl_headers = [
        'stl_bind.h',
    ]
    
    for header in stl_headers:
        header_path = os.path.join(pybind11_dir, header)
        assert os.path.isfile(header_path), f"Missing STL header: {header}"


def test_cmake_files_exist():
    """Test that CMake configuration files exist."""
    cmake_dir = pybind11.get_cmake_dir()
    
    cmake_files = [
        'pybind11Config.cmake',
        'pybind11ConfigVersion.cmake',
        'pybind11Targets.cmake',
    ]
    
    for cmake_file in cmake_files:
        file_path = os.path.join(cmake_dir, cmake_file)
        assert os.path.isfile(file_path), f"Missing CMake file: {cmake_file}"


def test_module_attributes():
    """Test module attributes."""
    # Check that common attributes exist
    assert hasattr(pybind11, 'get_include')
    assert hasattr(pybind11, 'get_cmake_dir')
    assert callable(pybind11.get_include)
    assert callable(pybind11.get_cmake_dir)


def test_version_info():
    """Test version info structure."""
    version = pybind11.__version__
    
    # Version should be in format X.Y.Z or similar
    parts = version.split('.')
    assert len(parts) >= 2
    
    # Major and minor should be numeric
    assert parts[0].isdigit()
    assert parts[1].isdigit() or parts[1].split('-')[0].isdigit()


if __name__ == "__main__":
    test_version()
    test_get_include()
    test_get_cmake_dir()
    test_header_files_exist()
    test_detail_headers_exist()
    test_stl_bind_headers()
    test_cmake_files_exist()
    test_module_attributes()
    test_version_info()
    print("All pybind11 tests passed!")

