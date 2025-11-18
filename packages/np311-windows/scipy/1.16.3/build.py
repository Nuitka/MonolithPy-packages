import __np__
import glob
import shutil
import sys
import os
from tempfile import TemporaryDirectory

import setuptools.build_meta
from wheel.wheelfile import WheelFile


def run(wheel_directory):
    __np__.setup_compiler_env()

    __np__.run_build_tool_exe("patch", "patch.exe", "-p1", "-ui",
                              os.path.join(os.path.dirname(__file__), "scipy-static-patch.patch"))

    __np__.filter_paths_containing("gfortran.exe")
    env = os.environ.copy()
    env["FC"] = "flang-new.exe"
    env["FC_LD"] = "link.exe"
    env["CC"] = "clang-cl.exe"
    env["CC_LD"] = "link.exe"
    env["CXX"] = "clang-cl.exe"
    env["CXX_LD"] = "link.exe"
    env["FFLAGS"] = "-fms-runtime-lib=static"
    env["PATH"] = (os.path.dirname(__np__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep +
                          os.path.dirname(__np__.find_build_tool_exe("cmake", "cmake.exe")) + os.pathsep +
                          os.path.dirname(__np__.find_build_tool_exe("clang", "lld-link.exe")) + os.pathsep +
                          os.path.dirname(__np__.find_build_tool_exe("flang", "flang-new.exe")) + os.pathsep + os.environ["PATH"])
    env["PEP517_BACKEND_PATH"] = os.pathsep.join([x for x in sys.path if not x.endswith(os.path.sep + "site")])
    env["LIB"] = os.environ["LIB"] + os.pathsep + __np__.find_dep_libs("openblas")
    env["INCLUDE"] = os.environ["INCLUDE"] + os.pathsep + __np__.find_dep_include("openblas")
    env["CMAKE_PREFIX_PATH"] = __np__.find_dep_root("openblas")
    env["CFLAGS"] = "/DBYPASS_NP_EMBED"
    env["CXXFLAGS"] = "/DBYPASS_NP_EMBED"
    job_args = []
    if "NP_JOBS" in env:
        job_args += ["-Ccompile-args=-j" + env["NP_JOBS"]]
    __np__.run(sys.executable, "-m", "build", "-w", "--no-isolation", "-Ccompile-args=-j6",
                           "-Csetup-args=-Dprefer_static=True", "-Csetup-args=-Db_vscrt=mt", *job_args, env=env)

    wheel_location = glob.glob(os.path.join("dist", "scipy-*.whl"))[0]

    env["PATH"] = (os.path.dirname(__np__.find_build_tool_exe("7zip", "7z.exe")) + os.path.pathsep +
                   os.path.dirname(__np__.find_build_tool_exe("mingw", "objdump.exe")) + os.path.pathsep + env["PATH"])
    os.environ.update(env)

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\optimize\\_lbfgsb.mp313-win_amd64.lib"), "scipy_optimize__lbfgsb_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\optimize\\_highspy\\_core.mp313-win_amd64.lib"), "scipy_optimize__highspy__core_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\interpolate\\_dfitpack.mp313-win_amd64.lib"), "scipy_interpolate__dfitpack_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\integrate\\_dop.mp313-win_amd64.lib"), "scipy_integrate__dop_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\integrate\\_vode.mp313-win_amd64.lib"), "scipy_integrate__vode_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\linalg\\_fblas.mp313-win_amd64.lib"), "scipy_linalg__fblas_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\fft\\_pocketfft\\pypocketfft.mp313-win_amd64.lib"),"scipy_fft__pocketfft_pypocketfft_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\optimize\\_pava_pybind.mp313-win_amd64.lib"), "scipy_stats_optimize__pava_pybind_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\spatial\\_distance_pybind.mp313-win_amd64.lib"), "scipy_stats_spatial__distance_pybind_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\optimize\\_highspy\\_highs_options.mp313-win_amd64.lib"),"scipy__highspy__highs_options_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\sparse\\linalg\\_propack\\_cpropack.mp313-win_amd64.lib"),"scipy_sparse_linalg__propack__cpropack_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\sparse\\linalg\\_propack\\_dpropack.mp313-win_amd64.lib"),"scipy_sparse_linalg__propack__dpropack_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\sparse\\linalg\\_propack\\_spropack.mp313-win_amd64.lib"),"scipy_sparse_linalg__propack__spropack_")
        # __np__.rename_symbols_in_file(os.path.join(tmpdir, "scipy\\sparse\\linalg\\_propack\\_zpropack.mp313-win_amd64.lib"),"scipy_sparse_linalg__propack__zpropack_")
        # __np__.rename_symbols_in_file(
        #     os.path.join(tmpdir, "scipy\\liblib__cpropack.lib"),
        #     "scipy_sparse_linalg__propack__zpropack_",
        #     protected_symbols=["clanbpro"])
        # __np__.rename_symbols_in_file(
        #     os.path.join(tmpdir, "scipy\\sparse\\linalg\\_propack\\_zpropack.mp313-win_amd64.lib"),
        #     "scipy_sparse_linalg__propack__zpropack_")

        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
