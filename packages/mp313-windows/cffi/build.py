import __mp__
import glob
import shutil
import sys
import os
import setuptools.build_meta
from tempfile import TemporaryDirectory

from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __mp__.setup_compiler_env()

    __mp__.run_build_tool_exe("patch", "patch.exe", "--binary", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "cffi-static-patch.patch"))

    __mp__.run_with_output(sys.executable, "-m", "pip", "wheel", ".", "--verbose")

    wheel_location = glob.glob("cffi-*.whl")[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)

        # Pack win64.obj into _cffi_backend.lib so symbols are available
        cffi_lib = None
        for filename in wheel_files:
            if "_cffi_backend" in filename and filename.endswith(".lib"):
                cffi_lib = os.path.join(tmpdir, filename)
                break

        win64_obj = "src/c/libffi_x86_x64/win64.obj"
        if cffi_lib and os.path.exists(win64_obj):
            __mp__.run_with_output("lib.exe", "/OUT:" + cffi_lib, cffi_lib, win64_obj)

        __mp__.analyze_and_rename_library_symbols(tmpdir,
                                                  "cffi")
        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                if os.path.exists(os.path.join(tmpdir, filename)):
                    wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
