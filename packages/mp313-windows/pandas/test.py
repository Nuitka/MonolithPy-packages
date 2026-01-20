"""
Basic sanity tests for pandas package.
Tests C-backed functionality without extra dependencies.
"""

import numpy as np
import pandas as pd


def test_dataframe_creation():
    """Test DataFrame creation (C-backed)."""
    # From dict
    df = pd.DataFrame({
        'A': [1, 2, 3],
        'B': [4.0, 5.0, 6.0],
        'C': ['x', 'y', 'z']
    })
    assert df.shape == (3, 3)
    assert list(df.columns) == ['A', 'B', 'C']
    
    # From numpy array
    arr = np.array([[1, 2], [3, 4], [5, 6]])
    df2 = pd.DataFrame(arr, columns=['X', 'Y'])
    assert df2.shape == (3, 2)


def test_series_operations():
    """Test Series operations (C-backed)."""
    s = pd.Series([1, 2, 3, 4, 5])
    
    assert s.sum() == 15
    assert s.mean() == 3.0
    assert s.std() > 0
    assert s.min() == 1
    assert s.max() == 5


def test_indexing():
    """Test indexing operations (C-backed)."""
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [10, 20, 30, 40, 50]
    })
    
    # iloc
    assert df.iloc[0, 0] == 1
    assert df.iloc[2, 1] == 30
    
    # loc
    df.index = ['a', 'b', 'c', 'd', 'e']
    assert df.loc['a', 'A'] == 1
    
    # Boolean indexing
    filtered = df[df['A'] > 2]
    assert len(filtered) == 3


def test_groupby():
    """Test groupby operations (C-backed)."""
    df = pd.DataFrame({
        'category': ['A', 'B', 'A', 'B', 'A'],
        'value': [1, 2, 3, 4, 5]
    })
    
    grouped = df.groupby('category')['value'].sum()
    assert grouped['A'] == 9
    assert grouped['B'] == 6


def test_merge():
    """Test merge operations (C-backed)."""
    df1 = pd.DataFrame({
        'key': ['a', 'b', 'c'],
        'value1': [1, 2, 3]
    })
    df2 = pd.DataFrame({
        'key': ['a', 'b', 'd'],
        'value2': [4, 5, 6]
    })
    
    merged = pd.merge(df1, df2, on='key', how='inner')
    assert len(merged) == 2
    assert 'value1' in merged.columns
    assert 'value2' in merged.columns


def test_sorting():
    """Test sorting operations (C-backed)."""
    df = pd.DataFrame({
        'A': [3, 1, 2],
        'B': [6, 4, 5]
    })
    
    sorted_df = df.sort_values('A')
    assert sorted_df.iloc[0]['A'] == 1
    assert sorted_df.iloc[2]['A'] == 3


def test_datetime():
    """Test datetime operations (C-backed)."""
    dates = pd.date_range('2023-01-01', periods=5, freq='D')
    assert len(dates) == 5
    
    df = pd.DataFrame({
        'date': dates,
        'value': [1, 2, 3, 4, 5]
    })
    assert df['date'].dtype == 'datetime64[ns]'


def test_string_operations():
    """Test string operations (C-backed)."""
    s = pd.Series(['hello', 'world', 'test'])
    
    upper = s.str.upper()
    assert upper[0] == 'HELLO'
    
    contains = s.str.contains('o')
    assert contains[0] == True
    assert contains[2] == False


def test_missing_data():
    """Test missing data handling (C-backed)."""
    df = pd.DataFrame({
        'A': [1, np.nan, 3],
        'B': [4, 5, np.nan]
    })
    
    assert df.isna().sum().sum() == 2
    
    filled = df.fillna(0)
    assert filled.isna().sum().sum() == 0
    
    dropped = df.dropna()
    assert len(dropped) == 1


def test_aggregation():
    """Test aggregation functions (C-backed)."""
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [10, 20, 30, 40, 50]
    })
    
    agg = df.agg(['sum', 'mean', 'std'])
    assert agg.loc['sum', 'A'] == 15
    assert agg.loc['mean', 'B'] == 30.0


if __name__ == "__main__":
    test_dataframe_creation()
    test_series_operations()
    test_indexing()
    test_groupby()
    test_merge()
    test_sorting()
    test_datetime()
    test_string_operations()
    test_missing_data()
    test_aggregation()
    print("All pandas tests passed!")

