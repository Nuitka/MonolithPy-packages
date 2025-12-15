import __mp__
import glob
import shutil
import sys
import os
from tempfile import TemporaryDirectory

import setuptools.build_meta
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __mp__.run_build_tool_exe("patch", "-p1", "-ui",
                              os.path.join(os.path.dirname(__file__), "scipy-static-patch.patch"))

    

    env = os.environ.copy()
    env["MACOSX_DEPLOYMENT_TARGET"] = "10.9"
    env["PEP517_BACKEND_PATH"] = os.pathsep.join([x for x in sys.path if not x.endswith(os.path.sep + "site")])
    env["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake")) + os.pathsep +
                   os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep + os.environ["PATH"])
    env["FC"] = __mp__.find_build_tool_exe("gcc", "gfortran-nuitka")
    env["LIB"] = __mp__.find_dep_libs("openblas")
    env["INCLUDE"] = __mp__.find_dep_include("openblas")
    env["CMAKE_PREFIX_PATH"] = __mp__.find_dep_root("openblas")
    env["FFLAGS"] = "-static-libgcc"
    env["CFLAGS"] = "-DBYPASS_MP_EMBED"
    env["CXXFLAGS"] = "-DBYPASS_MP_EMBED"
    env["PKG_CONFIG"] = "/disabled"
    __mp__.run(sys.executable, "-m", "build", "-w", "--no-isolation",
                            "-Csetup-args=-Dprefer_static=True", "-Csetup-args=-Dblas=openblas", 
                            "-Csetup-args=-Dlapack=openblas", "-Csetup-args=-Dbuildtype=debug",
                            "-Csetup-args=-Dfortran_link_args=-static-libgcc -L/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/usr/lib",
                            "-Cbuild-dir=build",
               env=env)

    wheel_location = glob.glob(os.path.join("dist", "scipy-*.whl"))[0]

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
                                                      "_d1mach_": {
                                                          "use_definition_from": "libmach_lib.a"
                                                      }},
                                                  #protected_symbol_patterns=[".*f2py.*"],
                                                  write_debug=True
                                                  )

        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
