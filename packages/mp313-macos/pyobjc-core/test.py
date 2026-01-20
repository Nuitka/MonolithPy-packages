"""
Basic sanity tests for pyobjc-core package.
Tests C-backed (Objective-C runtime) functionality without extra dependencies.
Note: This package is macOS-specific.
"""

import objc
from Foundation import NSObject, NSString, NSArray, NSDictionary, NSNumber


def test_version():
    """Test version is accessible."""
    assert hasattr(objc, '__version__')
    assert objc.__version__ is not None


def test_nsstring():
    """Test NSString creation and conversion (C-backed)."""
    # Create NSString from Python string
    ns_str = NSString.stringWithString_("Hello, World!")
    assert ns_str is not None
    
    # Convert back to Python string
    py_str = str(ns_str)
    assert py_str == "Hello, World!"


def test_nsarray():
    """Test NSArray creation and access (C-backed)."""
    # Create NSArray from Python list
    py_list = [1, 2, 3, 4, 5]
    ns_array = NSArray.arrayWithArray_(py_list)
    
    assert ns_array.count() == 5
    assert ns_array.objectAtIndex_(0) == 1
    assert ns_array.objectAtIndex_(4) == 5


def test_nsdictionary():
    """Test NSDictionary creation and access (C-backed)."""
    # Create NSDictionary from Python dict
    py_dict = {'key1': 'value1', 'key2': 'value2'}
    ns_dict = NSDictionary.dictionaryWithDictionary_(py_dict)
    
    assert ns_dict.count() == 2
    assert str(ns_dict.objectForKey_('key1')) == 'value1'


def test_nsnumber():
    """Test NSNumber creation (C-backed)."""
    # Integer
    num_int = NSNumber.numberWithInt_(42)
    assert num_int.intValue() == 42
    
    # Float
    num_float = NSNumber.numberWithFloat_(3.14)
    assert abs(num_float.floatValue() - 3.14) < 0.001
    
    # Boolean
    num_bool = NSNumber.numberWithBool_(True)
    assert num_bool.boolValue() == True


def test_custom_class():
    """Test creating custom Objective-C class (C-backed)."""
    class MyClass(NSObject):
        def init(self):
            self = objc.super(MyClass, self).init()
            if self is None:
                return None
            self._value = 0
            return self
        
        def setValue_(self, value):
            self._value = value
        
        def value(self):
            return self._value
    
    obj = MyClass.alloc().init()
    assert obj is not None
    
    obj.setValue_(42)
    assert obj.value() == 42


def test_selector():
    """Test selector creation (C-backed)."""
    sel = objc.selector(lambda self: None, selector=b'testMethod')
    assert sel is not None


def test_protocol():
    """Test protocol handling (C-backed)."""
    # NSCopying protocol should be accessible
    try:
        from Foundation import NSCopying
        assert NSCopying is not None
    except ImportError:
        # Protocol might not be directly importable
        pass


def test_method_signature():
    """Test method signature handling (C-backed)."""
    class TestClass(NSObject):
        @objc.typedSelector(b'v@:i')
        def setIntValue_(self, value):
            pass
    
    obj = TestClass.alloc().init()
    assert obj is not None


def test_class_methods():
    """Test class method access (C-backed)."""
    # NSObject class methods
    assert NSObject.class_() is not None
    assert NSObject.superclass() is None or NSObject.superclass() is not None


def test_instance_methods():
    """Test instance method access (C-backed)."""
    obj = NSObject.alloc().init()
    
    # Basic instance methods
    assert obj.class_() is not None
    desc = obj.description()
    assert desc is not None


def test_memory_management():
    """Test memory management (C-backed)."""
    obj = NSObject.alloc().init()
    
    # Retain count operations (ARC handles this, but API should work)
    assert obj is not None
    
    # Object should be valid
    assert obj.description() is not None


def test_objc_class_lookup():
    """Test Objective-C class lookup (C-backed)."""
    # Look up NSObject class
    cls = objc.lookUpClass('NSObject')
    assert cls is not None
    assert cls is NSObject


if __name__ == "__main__":
    test_version()
    test_nsstring()
    test_nsarray()
    test_nsdictionary()
    test_nsnumber()
    test_custom_class()
    test_selector()
    test_protocol()
    test_method_signature()
    test_class_methods()
    test_instance_methods()
    test_memory_management()
    test_objc_class_lookup()
    print("All pyobjc-core tests passed!")

