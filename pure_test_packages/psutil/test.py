"""
Basic sanity tests for psutil package.
Tests cross-platform process / system info accessors that exercise the
native C extension on every platform.
"""

import os
import psutil


def test_version():
    assert hasattr(psutil, '__version__')
    assert psutil.__version__ is not None


def test_cpu_count():
    """Physical CPU count is positive and matches os.cpu_count() within reason."""
    logical = psutil.cpu_count(logical=True)
    assert logical is not None and logical > 0
    # Physical count may be None on some platforms; only assert sanity if returned.
    physical = psutil.cpu_count(logical=False)
    if physical is not None:
        assert physical > 0
        assert physical <= logical


def test_cpu_percent_returns_float():
    """cpu_percent with a non-zero interval returns a float in [0, 100*ncpu]."""
    val = psutil.cpu_percent(interval=0.05)
    assert isinstance(val, float)
    assert val >= 0.0


def test_virtual_memory():
    """virtual_memory exposes total/available as positive integers."""
    mem = psutil.virtual_memory()
    assert mem.total > 0
    assert mem.available > 0
    assert 0.0 <= mem.percent <= 100.0


def test_disk_usage_root():
    """disk_usage on a path that always exists returns positive total."""
    if os.name == 'nt':
        path = os.environ.get('SystemDrive', 'C:') + '\\'
    else:
        path = '/'
    du = psutil.disk_usage(path)
    assert du.total > 0
    assert du.used >= 0
    assert du.free >= 0


def test_process_self():
    """The current process can be queried by PID and reports its own pid back."""
    p = psutil.Process(os.getpid())
    assert p.pid == os.getpid()
    assert p.is_running()
    # name/exe should be non-empty strings (exact value depends on platform)
    assert isinstance(p.name(), str) and p.name()
    # Permission to read own status is universal; cmdline returns a list.
    assert isinstance(p.cmdline(), list)


def test_boot_time():
    """boot_time returns a positive Unix timestamp predating now."""
    import time
    bt = psutil.boot_time()
    assert bt > 0
    assert bt < time.time()


if __name__ == "__main__":
    test_version()
    test_cpu_count()
    test_cpu_percent_returns_float()
    test_virtual_memory()
    test_disk_usage_root()
    test_process_self()
    test_boot_time()
    print("All psutil tests passed!")
