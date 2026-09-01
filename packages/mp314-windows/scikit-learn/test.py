"""
Basic sanity tests for scikit-learn package.
Tests C-backed functionality without extra dependencies.
"""

# --- TEMP DIAGNOSTIC (relink crash 0xC0000005 on the hosted runner) ---
# faulthandler on Windows dumps a Python traceback on a fatal access
# violation, so the CI log shows exactly which import / C-backed call the
# miscompiled interpreter faults in. The _step() markers are flushed before
# every operation so the last line printed pinpoints the fault even if the
# process dies without unwinding. Remove once the relink miscompile is fixed.
import faulthandler
import sys
faulthandler.enable(all_threads=True)


def _step(msg):
    print("STEP:", msg, flush=True)
    sys.stderr.flush()


_step("import numpy")
import numpy as np
_step("import sklearn.datasets")
from sklearn import datasets
_step("import sklearn.model_selection.train_test_split")
from sklearn.model_selection import train_test_split
_step("import sklearn.preprocessing.StandardScaler")
from sklearn.preprocessing import StandardScaler
_step("import sklearn.linear_model")
from sklearn.linear_model import LogisticRegression, LinearRegression
_step("import sklearn.tree")
from sklearn.tree import DecisionTreeClassifier
_step("import sklearn.ensemble.RandomForestClassifier")
from sklearn.ensemble import RandomForestClassifier
_step("import sklearn.cluster.KMeans")
from sklearn.cluster import KMeans
_step("import sklearn.decomposition.PCA")
from sklearn.decomposition import PCA
_step("import sklearn.metrics")
from sklearn.metrics import accuracy_score, mean_squared_error
_step("all imports OK")


def test_datasets():
    """Test dataset loading."""
    iris = datasets.load_iris()
    assert iris.data.shape == (150, 4)
    assert iris.target.shape == (150,)
    
    digits = datasets.load_digits()
    assert digits.data.shape[0] == 1797


def test_preprocessing():
    """Test preprocessing functions (C-backed)."""
    X = np.array([[1, 2], [3, 4], [5, 6]], dtype=np.float64)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    assert abs(X_scaled.mean()) < 1e-10
    assert abs(X_scaled.std() - 1.0) < 0.1


def test_train_test_split():
    """Test train/test split."""
    X = np.random.rand(100, 4)
    y = np.random.randint(0, 2, 100)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    assert len(X_train) == 80
    assert len(X_test) == 20


def test_logistic_regression():
    """Test logistic regression (C-backed liblinear)."""
    iris = datasets.load_iris()
    X, y = iris.data, iris.target
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    clf = LogisticRegression(max_iter=200, random_state=42)
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    assert accuracy > 0.8


def test_linear_regression():
    """Test linear regression (C-backed BLAS/LAPACK)."""
    X = np.array([[1], [2], [3], [4], [5]], dtype=np.float64)
    y = np.array([2, 4, 6, 8, 10], dtype=np.float64)
    
    reg = LinearRegression()
    reg.fit(X, y)
    
    assert abs(reg.coef_[0] - 2.0) < 1e-10
    assert abs(reg.intercept_) < 1e-10


def test_decision_tree():
    """Test decision tree (C-backed)."""
    iris = datasets.load_iris()
    X, y = iris.data, iris.target
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    clf = DecisionTreeClassifier(random_state=42)
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    assert accuracy > 0.8


def test_random_forest():
    """Test random forest (C-backed)."""
    iris = datasets.load_iris()
    X, y = iris.data, iris.target
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    clf = RandomForestClassifier(n_estimators=10, random_state=42)
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    assert accuracy > 0.8


def test_kmeans():
    """Test K-means clustering (C-backed)."""
    X = np.array([
        [1, 2], [1.5, 1.8], [5, 8], [8, 8],
        [1, 0.6], [9, 11], [8, 2], [10, 2], [9, 3]
    ])
    
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    kmeans.fit(X)
    
    assert len(kmeans.cluster_centers_) == 3
    assert len(kmeans.labels_) == 9


def test_pca():
    """Test PCA (C-backed LAPACK)."""
    X = np.random.rand(100, 10)
    
    pca = PCA(n_components=3)
    X_reduced = pca.fit_transform(X)
    
    assert X_reduced.shape == (100, 3)
    assert sum(pca.explained_variance_ratio_) <= 1.0


if __name__ == "__main__":
    # Each _step() marks the next C-backed entry point; the last STEP line in
    # the CI log before the process dies is the call the miscompiled interpreter
    # faulted in. (TEMP DIAGNOSTIC — see the faulthandler note at the top.)
    _step("test_datasets (numpy-backed dataset load)")
    test_datasets()
    _step("test_preprocessing (StandardScaler / sparsefuncs)")
    test_preprocessing()
    _step("test_train_test_split")
    test_train_test_split()
    _step("test_logistic_regression (liblinear)")
    test_logistic_regression()
    _step("test_linear_regression (BLAS/LAPACK)")
    test_linear_regression()
    _step("test_decision_tree (sklearn.tree C)")
    test_decision_tree()
    _step("test_random_forest (OpenMP)")
    test_random_forest()
    _step("test_kmeans (OpenMP prange)")
    test_kmeans()
    _step("test_pca (LAPACK)")
    test_pca()
    print("All scikit-learn tests passed!")

