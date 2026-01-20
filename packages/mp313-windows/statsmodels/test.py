"""
Basic sanity tests for statsmodels package.
Tests C-backed functionality without extra dependencies.
"""

import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson


def test_ols_regression():
    """Test OLS regression (C-backed BLAS/LAPACK)."""
    np.random.seed(42)
    
    # Generate data
    X = np.random.rand(100, 2)
    X = sm.add_constant(X)
    y = 1 + 2 * X[:, 1] + 3 * X[:, 2] + np.random.randn(100) * 0.1
    
    # Fit model
    model = sm.OLS(y, X)
    results = model.fit()
    
    assert results is not None
    assert len(results.params) == 3
    assert abs(results.params[0] - 1) < 0.5  # Intercept ~1
    assert abs(results.params[1] - 2) < 0.5  # Coef1 ~2
    assert abs(results.params[2] - 3) < 0.5  # Coef2 ~3


def test_wls_regression():
    """Test WLS regression (C-backed)."""
    np.random.seed(42)
    
    X = np.random.rand(50, 1)
    X = sm.add_constant(X)
    y = 1 + 2 * X[:, 1] + np.random.randn(50) * 0.1
    weights = np.ones(50)
    
    model = sm.WLS(y, X, weights=weights)
    results = model.fit()
    
    assert results is not None
    assert len(results.params) == 2


def test_glm():
    """Test GLM (C-backed)."""
    np.random.seed(42)
    
    # Poisson regression
    X = np.random.rand(100, 1)
    X = sm.add_constant(X)
    y = np.random.poisson(lam=np.exp(0.5 + X[:, 1]), size=100)
    
    model = sm.GLM(y, X, family=sm.families.Poisson())
    results = model.fit()
    
    assert results is not None
    assert len(results.params) == 2


def test_logistic_regression():
    """Test logistic regression (C-backed)."""
    np.random.seed(42)
    
    X = np.random.rand(100, 2)
    X = sm.add_constant(X)
    prob = 1 / (1 + np.exp(-(0.5 + X[:, 1] - X[:, 2])))
    y = (np.random.rand(100) < prob).astype(int)
    
    model = sm.Logit(y, X)
    results = model.fit(disp=False)
    
    assert results is not None
    assert len(results.params) == 3


def test_time_series_acf():
    """Test autocorrelation function (C-backed)."""
    np.random.seed(42)
    
    # Generate AR(1) process
    n = 200
    y = np.zeros(n)
    y[0] = np.random.randn()
    for i in range(1, n):
        y[i] = 0.7 * y[i-1] + np.random.randn()
    
    # Compute ACF
    acf_values = acf(y, nlags=10)
    assert len(acf_values) == 11
    assert acf_values[0] == 1.0  # ACF at lag 0 is always 1


def test_time_series_pacf():
    """Test partial autocorrelation function (C-backed)."""
    np.random.seed(42)
    
    y = np.random.randn(100)
    
    pacf_values = pacf(y, nlags=10)
    assert len(pacf_values) == 11


def test_adf_test():
    """Test Augmented Dickey-Fuller test (C-backed)."""
    np.random.seed(42)
    
    # Stationary series
    y = np.random.randn(100)
    
    result = adfuller(y, maxlag=5)
    assert result is not None
    assert len(result) >= 4  # statistic, pvalue, usedlag, nobs, ...


def test_durbin_watson():
    """Test Durbin-Watson statistic (C-backed)."""
    np.random.seed(42)
    
    residuals = np.random.randn(100)
    
    dw = durbin_watson(residuals)
    assert 0 <= dw <= 4  # DW statistic is between 0 and 4


def test_heteroscedasticity():
    """Test Breusch-Pagan test (C-backed)."""
    np.random.seed(42)
    
    X = np.random.rand(100, 2)
    X = sm.add_constant(X)
    y = 1 + 2 * X[:, 1] + np.random.randn(100) * 0.1
    
    model = sm.OLS(y, X)
    results = model.fit()
    
    bp_test = het_breuschpagan(results.resid, X)
    assert len(bp_test) == 4  # LM stat, LM pvalue, F stat, F pvalue


def test_summary():
    """Test model summary generation."""
    np.random.seed(42)
    
    X = np.random.rand(50, 1)
    X = sm.add_constant(X)
    y = 1 + 2 * X[:, 1] + np.random.randn(50) * 0.1
    
    model = sm.OLS(y, X)
    results = model.fit()
    
    summary = results.summary()
    assert summary is not None
    summary_str = str(summary)
    assert 'R-squared' in summary_str


if __name__ == "__main__":
    test_ols_regression()
    test_wls_regression()
    test_glm()
    test_logistic_regression()
    test_time_series_acf()
    test_time_series_pacf()
    test_adf_test()
    test_durbin_watson()
    test_heteroscedasticity()
    test_summary()
    print("All statsmodels tests passed!")

