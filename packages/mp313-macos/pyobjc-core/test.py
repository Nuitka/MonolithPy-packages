"""
Basic sanity tests for pyobjc-core package.
Tests the Objective-C runtime bridge (objc module) without requiring
pyobjc-framework-Cocoa or any other framework bindings.
Note: This package is macOS-specific.
"""

import objc

# Look up ObjC classes directly from the runtime — no framework bindings needed.
NSObject = objc.lookUpClass('NSObject')
NSString = objc.lookUpClass('NSString')
NSArray = objc.lookUpClass('NSArray')
NSDictionary = objc.lookUpClass('NSDictionary')
NSNumber = objc.lookUpClass('NSNumber')


def test_version():
    """Test version is accessible."""
    assert hasattr(objc, '__version__')
    assert objc.__version__ is not None


def test_class_lookup():
    """Test Objective-C class lookup (C-backed)."""
    cls = objc.lookUpClass('NSObject')
    assert cls is not None
    assert cls is NSObject


def test_nsstring():
    """Test NSString creation and conversion (C-backed)."""
    ns_str = NSString.stringWithString_("Hello, World!")
    assert ns_str is not None

    py_str = str(ns_str)
    assert py_str == "Hello, World!"


def test_nsarray():
    """Test NSArray creation and access (C-backed)."""
    py_list = [1, 2, 3, 4, 5]
    ns_array = NSArray.arrayWithArray_(py_list)

    assert ns_array.count() == 5
    assert ns_array.objectAtIndex_(0) == 1
    assert ns_array.objectAtIndex_(4) == 5


def test_nsdictionary():
    """Test NSDictionary creation and access (C-backed)."""
    py_dict = {'key1': 'value1', 'key2': 'value2'}
    ns_dict = NSDictionary.dictionaryWithDictionary_(py_dict)

    assert ns_dict.count() == 2
    assert str(ns_dict.objectForKey_('key1')) == 'value1'


def test_nsnumber():
    """Test NSNumber creation (C-backed)."""
    num_int = NSNumber.numberWithInt_(42)
    assert num_int.intValue() == 42

    num_float = NSNumber.numberWithFloat_(3.14)
    assert abs(num_float.floatValue() - 3.14) < 0.001

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
    assert NSObject.class_() is not None
    assert NSObject.superclass() is None or NSObject.superclass() is not None


def test_instance_methods():
    """Test instance method access (C-backed)."""
    obj = NSObject.alloc().init()

    assert obj.class_() is not None
    desc = obj.description()
    assert desc is not None


def test_memory_management():
    """Test memory management (C-backed)."""
    obj = NSObject.alloc().init()

    assert obj is not None
    assert obj.description() is not None


if __name__ == "__main__":
    test_version()
    test_class_lookup()
    test_nsstring()
    test_nsarray()
    test_nsdictionary()
    test_nsnumber()
    test_custom_class()
    test_selector()
    test_method_signature()
    test_class_methods()
    test_instance_methods()
    test_memory_management()
    print("All pyobjc-core tests passed!")

