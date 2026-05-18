"""
Basic sanity tests for cffi package.
Tests C FFI functionality without extra dependencies.
"""

import cffi


def test_version():
    """Test version is accessible."""
    assert hasattr(cffi, '__version__')
    assert cffi.__version__ is not None


def test_ffi_creation():
    """Test FFI object creation."""
    ffi = cffi.FFI()
    assert ffi is not None


def test_cdef_basic():
    """Test basic C definitions."""
    ffi = cffi.FFI()
    
    # Define a simple struct
    ffi.cdef("""
        typedef struct {
            int x;
            int y;
        } Point;
    """)
    
    # Create instance
    point = ffi.new("Point *")
    point.x = 10
    point.y = 20
    
    assert point.x == 10
    assert point.y == 20


def test_primitive_types():
    """Test primitive C types."""
    ffi = cffi.FFI()
    
    # Integer types
    i = ffi.new("int *", 42)
    assert i[0] == 42
    
    # Float types
    f = ffi.new("float *", 3.14)
    assert abs(f[0] - 3.14) < 0.001
    
    # Double types
    d = ffi.new("double *", 2.718281828)
    assert abs(d[0] - 2.718281828) < 1e-9


def test_arrays():
    """Test C arrays."""
    ffi = cffi.FFI()
    
    # Integer array
    arr = ffi.new("int[5]")
    for i in range(5):
        arr[i] = i * 10
    
    assert arr[0] == 0
    assert arr[4] == 40
    
    # Array with initializer
    arr2 = ffi.new("int[3]", [1, 2, 3])
    assert arr2[0] == 1
    assert arr2[2] == 3


def test_strings():
    """Test C strings."""
    ffi = cffi.FFI()
    
    # Create C string
    s = ffi.new("char[]", b"Hello, World!")
    assert ffi.string(s) == b"Hello, World!"
    
    # String with specific size
    s2 = ffi.new("char[20]", b"Test")
    assert ffi.string(s2) == b"Test"


def test_sizeof():
    """Test sizeof operation."""
    ffi = cffi.FFI()
    
    # Basic types
    assert ffi.sizeof("char") == 1
    assert ffi.sizeof("int") >= 2
    assert ffi.sizeof("double") == 8


def test_cast():
    """Test type casting."""
    ffi = cffi.FFI()
    
    # Cast integer to pointer and back
    i = ffi.cast("int", 42)
    assert int(i) == 42
    
    # Cast between numeric types
    f = ffi.cast("float", 3)
    assert float(f) == 3.0


def test_buffer():
    """Test buffer interface."""
    ffi = cffi.FFI()
    
    # Create buffer
    arr = ffi.new("unsigned char[10]")
    for i in range(10):
        arr[i] = i
    
    # Get buffer
    buf = ffi.buffer(arr)
    assert len(buf) == 10
    # buffer returns bytes, so compare with bytes
    assert buf[0:1] == b'\x00'
    assert buf[9:10] == b'\x09'


def test_nested_struct():
    """Test nested structures."""
    ffi = cffi.FFI()
    
    ffi.cdef("""
        typedef struct {
            int x;
            int y;
        } Point;
        
        typedef struct {
            Point top_left;
            Point bottom_right;
        } Rectangle;
    """)
    
    rect = ffi.new("Rectangle *")
    rect.top_left.x = 0
    rect.top_left.y = 0
    rect.bottom_right.x = 100
    rect.bottom_right.y = 50
    
    assert rect.top_left.x == 0
    assert rect.bottom_right.x == 100


def test_null_pointer():
    """Test NULL pointer handling."""
    ffi = cffi.FFI()
    
    null = ffi.NULL
    assert null == ffi.cast("void *", 0)
    
    # Check if pointer is NULL
    ptr = ffi.new("int *")
    assert ptr != ffi.NULL


if __name__ == "__main__":
    test_version()
    test_ffi_creation()
    test_cdef_basic()
    test_primitive_types()
    test_arrays()
    test_strings()
    test_sizeof()
    test_cast()
    test_buffer()
    test_nested_struct()
    test_null_pointer()
    print("All cffi tests passed!")

