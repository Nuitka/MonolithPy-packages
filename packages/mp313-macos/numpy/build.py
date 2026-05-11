import __mp__
import glob
import shutil
import sys
import os
import sysconfig
import setuptools.build_meta
from tempfile import TemporaryDirectory
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    build_dir = os.getcwd()

    with open(os.path.join("numpy", "_core", "src", "multiarray", "dtypemeta.h"), "r") as f:
        api_table = f.read() + os.linesep

    with open(os.path.join("numpy", "_core", "src", "multiarray", "abstractdtypes.h"), "r") as f:
        api_table += f.read()

    with open(os.path.join("numpy", "_core", "include", "numpy", "_public_dtype_api_table.h"), "w") as f:
        f.write(api_table)

    __mp__.run_with_output("patch", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "numpy-static-patch.patch"))

    env = os.environ.copy()
    env["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    env["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake")) + os.pathsep +
                   os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + env.get("PATH", ""))
    env["FC"] = __mp__.find_build_tool_exe("gcc", "gfortran-nuitka")
    env["LIB"] = os.pathsep + __mp__.find_dep_libs("openblas")
    env["INCLUDE"] = os.pathsep + __mp__.find_dep_include("openblas")
    env["CMAKE_PREFIX_PATH"] = __mp__.find_dep_root("openblas")
    env["FFLAGS"] = "-static-libgcc"
    env["PKG_CONFIG"] = "/disabled"
    __mp__.run(sys.executable, "-m", "build", "-w", "--no-isolation", "-o", ".",
               "-Csetup-args=-Dblas=openblas", "-Csetup-args=-Dlapack=openblas", env=env)

    wheel_location = glob.glob("numpy-*.whl")[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)

        ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, f"numpy/_core/_multiarray_tests{ext_suffix}"),
                                      "np_multiarray_tests_")
        __mp__.analyze_and_rename_library_symbols(tmpdir, "numpy",
                                                  protected_symbol_patterns=["_?PyUFunc.+", "_?npy_.+", "_?PyArray.+", "_?Py.+_Type"],
                                                  exclude_libraries=["_multiarray_umath*"])

        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)
    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
