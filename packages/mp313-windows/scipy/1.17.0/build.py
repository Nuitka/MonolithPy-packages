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
    env = os.environ.copy()
    env["FC"] = "flang-new.exe"
    env["FC_LD"] = "link.exe"
    env["CC"] = "clang-cl.exe"
    env["CC_LD"] = "link.exe"
    env["CXX"] = "clang-cl.exe"
    env["CXX_LD"] = "link.exe"
    env["FFLAGS"] = "-fms-runtime-lib=static"
    env["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep +
                          os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake.exe")) + os.pathsep +
                          os.path.dirname(__mp__.find_build_tool_exe("clang", "lld-link.exe")) + os.pathsep +
                          os.path.dirname(__mp__.find_build_tool_exe("flang", "flang-new.exe")) + os.pathsep + os.environ["PATH"])
    env["PEP517_BACKEND_PATH"] = os.pathsep.join([x for x in sys.path if not x.endswith(os.path.sep + "site")])
    env["LIB"] = os.environ["LIB"] + os.pathsep + __mp__.find_dep_libs("openblas")
    env["INCLUDE"] = os.environ["INCLUDE"] + os.pathsep + __mp__.find_dep_include("openblas")
    env["CMAKE_PREFIX_PATH"] = __mp__.find_dep_root("openblas")
    env["CFLAGS"] = "/DBYPASS_MP_EMBED"
    env["CXXFLAGS"] = "/DBYPASS_MP_EMBED"
    job_args = []
    if "MP_JOBS" in env:
        job_args += ["-Ccompile-args=-j" + env["MP_JOBS"]]
    __mp__.run(sys.executable, "-m", "build", "-w", "--no-isolation", "-Ccompile-args=-j6",
                           "-Csetup-args=-Dprefer_static=True", "-Csetup-args=-Db_vscrt=mt", *job_args, env=env)

    wheel_location = glob.glob(os.path.join("dist", "scipy-*.whl"))[0]

    env["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("7zip", "7z.exe")) + os.path.pathsep +
                   os.path.dirname(__mp__.find_build_tool_exe("mingw", "objdump.exe")) + os.path.pathsep + env["PATH"])
    os.environ.update(env)

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
