"""
Basic sanity tests for numpy package.
Tests C-backed functionality without extra dependencies.
"""

import numpy as np


def test_array_creation():
    """Test basic array creation (C-backed)."""
    arr = np.array([1, 2, 3, 4, 5])
    assert arr.shape == (5,)
    assert arr.dtype == np.int_
    
    arr_2d = np.zeros((3, 4))
    assert arr_2d.shape == (3, 4)
    
    arr_ones = np.ones((2, 3), dtype=np.float64)
    assert arr_ones.sum() == 6.0


def test_array_operations():
    """Test array operations (C-backed BLAS/LAPACK)."""
    a = np.array([[1, 2], [3, 4]], dtype=np.float64)
    b = np.array([[5, 6], [7, 8]], dtype=np.float64)
    
    # Matrix multiplication (uses BLAS)
    c = np.dot(a, b)
    assert c[0, 0] == 19
    assert c[1, 1] == 50
    
    # Element-wise operations
    d = a + b
    assert d[0, 0] == 6
    
    e = a * b
    assert e[0, 0] == 5


def test_linear_algebra():
    """Test linear algebra functions (C-backed LAPACK)."""
    a = np.array([[1, 2], [3, 4]], dtype=np.float64)
    
    # Determinant
    det = np.linalg.det(a)
    assert abs(det - (-2.0)) < 1e-10
    
    # Inverse
    inv = np.linalg.inv(a)
    identity = np.dot(a, inv)
    assert abs(identity[0, 0] - 1.0) < 1e-10
    
    # Eigenvalues
    eigenvalues = np.linalg.eigvals(a)
    assert len(eigenvalues) == 2


def test_fft():
    """Test FFT functions (C-backed)."""
    x = np.array([1, 2, 3, 4])
    fft_result = np.fft.fft(x)
    assert len(fft_result) == 4
    
    # Inverse FFT
    ifft_result = np.fft.ifft(fft_result)
    assert np.allclose(ifft_result.real, x)


def test_random():
    """Test random number generation (C-backed)."""
    np.random.seed(42)
    
    # Uniform random
    uniform = np.random.rand(100)
    assert uniform.shape == (100,)
    assert 0 <= uniform.min() and uniform.max() <= 1
    
    # Normal distribution
    normal = np.random.randn(100)
    assert normal.shape == (100,)


def test_sorting():
    """Test sorting functions (C-backed)."""
    arr = np.array([3, 1, 4, 1, 5, 9, 2, 6])
    sorted_arr = np.sort(arr)
    assert sorted_arr[0] == 1
    assert sorted_arr[-1] == 9
    
    # Argsort
    indices = np.argsort(arr)
    assert arr[indices[0]] == 1


def test_ufuncs():
    """Test universal functions (C-backed)."""
    x = np.array([0, np.pi/2, np.pi])
    
    # Trigonometric
    sin_x = np.sin(x)
    assert abs(sin_x[0]) < 1e-10
    assert abs(sin_x[1] - 1.0) < 1e-10
    
    # Exponential
    exp_x = np.exp(np.array([0, 1, 2]))
    assert abs(exp_x[0] - 1.0) < 1e-10


def test_dtype_operations():
    """Test dtype operations (C-backed)."""
    # Different dtypes
    int_arr = np.array([1, 2, 3], dtype=np.int32)
    float_arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    complex_arr = np.array([1+2j, 3+4j], dtype=np.complex128)
    
    assert int_arr.dtype == np.int32
    assert float_arr.dtype == np.float32
    assert complex_arr.dtype == np.complex128


if __name__ == "__main__":
    test_array_creation()
    test_array_operations()
    test_linear_algebra()
    test_fft()
    test_random()
    test_sorting()
    test_ufuncs()
    test_dtype_operations()
    print("All numpy tests passed!")

