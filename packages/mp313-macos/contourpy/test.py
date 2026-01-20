"""
Basic sanity tests for contourpy package.
Tests C-backed functionality without extra dependencies.
"""

import numpy as np
import contourpy
from contourpy import contour_generator, LineType, FillType


def test_version():
    """Test version is accessible."""
    assert hasattr(contourpy, '__version__')
    assert contourpy.__version__ is not None


def test_contour_generator_creation():
    """Test contour generator creation (C-backed)."""
    x = np.linspace(0, 1, 10)
    y = np.linspace(0, 1, 10)
    X, Y = np.meshgrid(x, y)
    Z = X**2 + Y**2
    
    gen = contour_generator(X, Y, Z)
    assert gen is not None


def test_contour_lines():
    """Test contour line generation (C-backed)."""
    x = np.linspace(-2, 2, 50)
    y = np.linspace(-2, 2, 50)
    X, Y = np.meshgrid(x, y)
    Z = X**2 + Y**2
    
    gen = contour_generator(X, Y, Z, line_type=LineType.SeparateCode)
    
    # Get contour at level 1.0 (circle of radius 1)
    lines = gen.lines(1.0)
    assert lines is not None
    assert len(lines) == 2  # vertices and codes


def test_contour_filled():
    """Test filled contour generation (C-backed)."""
    x = np.linspace(-2, 2, 50)
    y = np.linspace(-2, 2, 50)
    X, Y = np.meshgrid(x, y)
    Z = X**2 + Y**2
    
    gen = contour_generator(X, Y, Z, fill_type=FillType.OuterCode)
    
    # Get filled contour between levels
    filled = gen.filled(0.5, 1.5)
    assert filled is not None


def test_multiple_levels():
    """Test multiple contour levels (C-backed)."""
    x = np.linspace(-3, 3, 100)
    y = np.linspace(-3, 3, 100)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X) * np.cos(Y)
    
    gen = contour_generator(X, Y, Z)
    
    levels = [-0.5, 0.0, 0.5]
    for level in levels:
        lines = gen.lines(level)
        assert lines is not None


def test_different_algorithms():
    """Test different contouring algorithms (C-backed)."""
    x = np.linspace(0, 1, 20)
    y = np.linspace(0, 1, 20)
    X, Y = np.meshgrid(x, y)
    Z = X * Y
    
    # Test mpl2005 algorithm
    gen_mpl2005 = contour_generator(X, Y, Z, name='mpl2005')
    lines = gen_mpl2005.lines(0.25)
    assert lines is not None
    
    # Test mpl2014 algorithm
    gen_mpl2014 = contour_generator(X, Y, Z, name='mpl2014')
    lines = gen_mpl2014.lines(0.25)
    assert lines is not None
    
    # Test serial algorithm
    gen_serial = contour_generator(X, Y, Z, name='serial')
    lines = gen_serial.lines(0.25)
    assert lines is not None


def test_line_types():
    """Test different line types (C-backed)."""
    x = np.linspace(0, 1, 30)
    y = np.linspace(0, 1, 30)
    X, Y = np.meshgrid(x, y)
    Z = X + Y
    
    # Separate
    gen = contour_generator(X, Y, Z, line_type=LineType.Separate)
    lines = gen.lines(1.0)
    assert lines is not None
    
    # SeparateCode
    gen = contour_generator(X, Y, Z, line_type=LineType.SeparateCode)
    lines = gen.lines(1.0)
    assert lines is not None


def test_fill_types():
    """Test different fill types (C-backed)."""
    x = np.linspace(0, 1, 30)
    y = np.linspace(0, 1, 30)
    X, Y = np.meshgrid(x, y)
    Z = X + Y
    
    # OuterCode
    gen = contour_generator(X, Y, Z, fill_type=FillType.OuterCode)
    filled = gen.filled(0.5, 1.0)
    assert filled is not None


def test_complex_surface():
    """Test with complex surface (C-backed)."""
    x = np.linspace(-np.pi, np.pi, 100)
    y = np.linspace(-np.pi, np.pi, 100)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X) * np.sin(Y)
    
    gen = contour_generator(X, Y, Z)
    
    # Multiple contour levels
    for level in np.linspace(-0.8, 0.8, 9):
        lines = gen.lines(level)
        assert lines is not None


if __name__ == "__main__":
    test_version()
    test_contour_generator_creation()
    test_contour_lines()
    test_contour_filled()
    test_multiple_levels()
    test_different_algorithms()
    test_line_types()
    test_fill_types()
    test_complex_surface()
    print("All contourpy tests passed!")

