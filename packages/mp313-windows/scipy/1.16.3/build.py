import __mp__
import glob
import shutil
import sys
import os
from tempfile import TemporaryDirectory

import setuptools.build_meta
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __mp__.setup_compiler_env()

    __mp__.run_build_tool_exe("patch", "patch.exe", "-p1", "-ui",
                              os.path.join(os.path.dirname(__file__), "scipy-static-patch.patch"))

    __mp__.filter_paths_containing("gfortran.exe")
    os.environ["FC"] = __mp__.find_build_tool_exe("flang", "flang-new.exe")
    os.environ["FC_LD"] = "lld-link"
    os.environ["CC"] = __mp__.find_build_tool_exe("clang", "clang-cl.exe")
    os.environ["CC_LD"] = "lld-link"
    os.environ["CXX"] = __mp__.find_build_tool_exe("clang", "clang-cl.exe")
    os.environ["CXX_LD"] = "lld-link"
    os.environ["FFLAGS"] = "-fms-runtime-lib=static"
    os.environ["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep +
                          os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake.exe")) + os.pathsep +
                          os.path.dirname(__mp__.find_build_tool_exe("clang", "lld-link.exe")) + os.pathsep +
                          os.path.dirname(__mp__.find_build_tool_exe("flang", "flang-new.exe")) + os.pathsep + os.environ["PATH"])
    os.environ["PEP517_BACKEND_PATH"] = os.pathsep.join([x for x in sys.path if not x.endswith(os.path.sep + "site")])
    os.environ["LIB"] = os.environ["LIB"] + os.pathsep + __mp__.find_dep_libs("openblas")
    os.environ["INCLUDE"] = os.environ["INCLUDE"] + os.pathsep + __mp__.find_dep_include("openblas")
    os.environ["CMAKE_PREFIX_PATH"] = __mp__.find_dep_root("openblas")
    os.environ["CFLAGS"] = "/DBYPASS_MP_EMBED"
    os.environ["CXXFLAGS"] = "/DBYPASS_MP_EMBED"

    job_args = []
    if "MP_JOBS" in os.environ:
        job_args += ["--config-settings=compile-args=-j" + os.environ["MP_JOBS"]]
    __mp__.run(sys.executable, "-m", "pip", "wheel", ".", "-v", "--config-settings=compile-args=-j6",
                           "--config-settings=setup-args=-Dprefer_static=True", "--config-settings=setup-args=-Db_vscrt=mt", *job_args)

    wheel_location = glob.glob("scipy-*.whl")[0]

    os.environ["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("7zip", "7z.exe")) + os.pathsep +
                   os.path.dirname(__mp__.find_build_tool_exe("mingw", "objdump.exe")) + os.pathsep + os.environ["PATH"])

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        __mp__.analyze_and_rename_library_symbols(tmpdir,
                                                  "scipy",
                                                  symbol_mapping={
                                                      "d1mach_": {
                                                          "use_definition_from": "libmach_lib.lib"
                                                      },
                                                      "_cdotc_": {
                                                          "use_definition_from": "libarnaud.lib",
                                                          "for_libraries": ["libdummy_g77_abi_wrappers.lib"]
                                                      },
                                                      "_zdotc_": {
                                                          "use_definition_from": "libarnaud.a",
                                                          "for_libraries": ["libdummy_g77_abi_wrappers.lib"]
                                                      }},
                                                  write_debug=True
                                                  )

        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
