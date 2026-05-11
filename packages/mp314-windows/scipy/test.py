"""
Basic sanity tests for scipy package.
Tests C/Fortran-backed functionality without extra dependencies.
"""

import numpy as np
import scipy
import scipy.linalg
import scipy.sparse
import scipy.fft
import scipy.special
import scipy.optimize
import scipy.interpolate
import scipy.integrate
import scipy.signal


def test_linalg():
    """Test linear algebra functions (Fortran LAPACK-backed)."""
    a = np.array([[1, 2], [3, 4]], dtype=np.float64)
    
    # LU decomposition
    lu, piv = scipy.linalg.lu_factor(a)
    assert lu.shape == (2, 2)
    
    # Solve linear system
    b = np.array([5, 6], dtype=np.float64)
    x = scipy.linalg.lu_solve((lu, piv), b)
    assert np.allclose(np.dot(a, x), b)
    
    # SVD
    u, s, vh = scipy.linalg.svd(a)
    assert len(s) == 2
    
    # Cholesky (for positive definite matrix)
    pd = np.array([[4, 2], [2, 5]], dtype=np.float64)
    L = scipy.linalg.cholesky(pd, lower=True)
    assert np.allclose(np.dot(L, L.T), pd)


def test_sparse():
    """Test sparse matrix operations (C-backed)."""
    # Create sparse matrix
    row = np.array([0, 0, 1, 2, 2])
    col = np.array([0, 2, 1, 0, 2])
    data = np.array([1, 2, 3, 4, 5])
    sparse_mat = scipy.sparse.csr_matrix((data, (row, col)), shape=(3, 3))
    
    assert sparse_mat.nnz == 5
    assert sparse_mat.shape == (3, 3)
    
    # Convert to dense
    dense = sparse_mat.toarray()
    assert dense[0, 0] == 1
    assert dense[2, 2] == 5


def test_fft():
    """Test FFT functions (C-backed)."""
    x = np.array([1, 2, 3, 4, 5, 6, 7, 8])
    
    # FFT
    fft_result = scipy.fft.fft(x)
    assert len(fft_result) == 8
    
    # Inverse FFT
    ifft_result = scipy.fft.ifft(fft_result)
    assert np.allclose(ifft_result.real, x)
    
    # DCT
    dct_result = scipy.fft.dct(x.astype(float))
    assert len(dct_result) == 8


def test_special():
    """Test special functions (C/Fortran-backed)."""
    # Bessel functions
    j0 = scipy.special.j0(1.0)
    assert abs(j0 - 0.7651976865579666) < 1e-10
    
    # Gamma function
    gamma_5 = scipy.special.gamma(5)
    assert abs(gamma_5 - 24.0) < 1e-10
    
    # Error function
    erf_1 = scipy.special.erf(1.0)
    assert 0.84 < erf_1 < 0.85


def test_optimize():
    """Test optimization functions (C/Fortran-backed)."""
    # Minimize scalar function
    def f(x):
        return (x - 2) ** 2
    
    result = scipy.optimize.minimize_scalar(f)
    assert abs(result.x - 2.0) < 1e-5
    
    # Root finding
    def g(x):
        return x ** 2 - 4
    
    root = scipy.optimize.brentq(g, 0, 3)
    assert abs(root - 2.0) < 1e-10


def test_interpolate():
    """Test interpolation functions (C-backed)."""
    x = np.array([0, 1, 2, 3, 4])
    y = np.array([0, 1, 4, 9, 16])
    
    # Linear interpolation
    f = scipy.interpolate.interp1d(x, y)
    assert abs(f(2.5) - 6.5) < 1e-10
    
    # Cubic spline
    cs = scipy.interpolate.CubicSpline(x, y)
    assert cs(2.0) == 4.0


def test_integrate():
    """Test integration functions (Fortran QUADPACK-backed)."""
    # Numerical integration
    def f(x):
        return x ** 2
    
    result, error = scipy.integrate.quad(f, 0, 1)
    assert abs(result - 1/3) < 1e-10


def test_signal():
    """Test signal processing functions (C-backed)."""
    # Convolution
    a = np.array([1, 2, 3])
    b = np.array([0, 1, 0.5])
    conv = scipy.signal.convolve(a, b)
    assert len(conv) == 5
    
    # Filter design
    b, a = scipy.signal.butter(4, 0.5)
    assert len(b) == 5
    assert len(a) == 5


if __name__ == "__main__":
    test_linalg()
    test_sparse()
    test_fft()
    test_special()
    test_optimize()
    test_interpolate()
    test_integrate()
    test_signal()
    print("All scipy tests passed!")

