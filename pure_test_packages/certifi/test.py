"""
Basic sanity tests for certifi package.
Tests certificate bundle functionality without extra dependencies.
"""

import certifi
import os


def test_version():
    """Test version is accessible."""
    assert hasattr(certifi, '__version__')
    assert certifi.__version__ is not None


def test_where():
    """Test certificate bundle path retrieval."""
    ca_bundle_path = certifi.where()
    
    assert ca_bundle_path is not None
    assert isinstance(ca_bundle_path, str)
    assert os.path.isfile(ca_bundle_path)


def test_contents():
    """Test certificate bundle contents."""
    ca_bundle_path = certifi.where()
    
    with open(ca_bundle_path, 'r') as f:
        contents = f.read()
    
    # Should contain certificate markers
    assert '-----BEGIN CERTIFICATE-----' in contents
    assert '-----END CERTIFICATE-----' in contents


def test_bundle_size():
    """Test certificate bundle has reasonable size."""
    ca_bundle_path = certifi.where()
    
    size = os.path.getsize(ca_bundle_path)
    
    # Bundle should be at least 100KB (contains many certificates)
    assert size > 100000


def test_multiple_certificates():
    """Test bundle contains multiple certificates."""
    ca_bundle_path = certifi.where()
    
    with open(ca_bundle_path, 'r') as f:
        contents = f.read()
    
    # Count certificates
    cert_count = contents.count('-----BEGIN CERTIFICATE-----')
    
    # Should have many root CA certificates
    assert cert_count > 50


def test_path_consistency():
    """Test path is consistent across calls."""
    path1 = certifi.where()
    path2 = certifi.where()
    
    assert path1 == path2


if __name__ == "__main__":
    test_version()
    test_where()
    test_contents()
    test_bundle_size()
    test_multiple_certificates()
    test_path_consistency()
    print("All certifi tests passed!")

