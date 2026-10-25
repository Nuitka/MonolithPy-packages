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
    __mp__.setup_compiler_env()

    build_dir = os.getcwd()

    with open(os.path.join("numpy", "_core", "src", "multiarray", "dtypemeta.h"), "r") as f:
        api_table = f.read() + "\n"

    with open(os.path.join("numpy", "_core", "src", "multiarray", "abstractdtypes.h"), "r") as f:
        api_table += f.read()

    with open(os.path.join("numpy", "_core", "include", "numpy", "_public_dtype_api_table.h"), "w") as f:
        f.write(api_table)

    __mp__.run_build_tool_exe("patch", "patch.exe", "-p1", "-i",
                              os.path.join(os.path.dirname(__file__), "numpy-static-patch.patch"))

    __mp__.filter_paths_containing("gfortran.exe")
    env = os.environ.copy()
    env["PATH"] = os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep + env["PATH"]
    env["LIB"] = env["LIB"] + os.pathsep + __mp__.find_dep_libs("openblas")
    env["INCLUDE"] = env["INCLUDE"] + os.pathsep + __mp__.find_dep_include("openblas")
    # Build with clang-cl: MSVC miscompiles numpy's float-predicate SIMD kernel's
    # 0-d/scalar broadcast path (isfinite/isnan/isinf wrong on scalars -> arange
    # "cannot compute length"); clang-cl (LLVM, like macOS) compiles it correctly.
    env["CC"] = __mp__.find_build_tool_exe("clang", "clang-cl.exe")
    env["CXX"] = env["CC"]
    env["CC_LD"] = "lld-link"
    env["CXX_LD"] = "lld-link"
    env["PATH"] = (os.path.dirname(__mp__.find_build_tool_exe("clang", "lld-link.exe"))
                   + os.pathsep + env["PATH"])
    # meson's run-time config checks link python314.lib's patched /MT CRT (mp_open
    # in mp_embed.lib + nuitka_embed_* in mp_embed_data.lib); MSVC auto-links them,
    # clang-cl doesn't -> link them + /FORCE:UNRESOLVED past POSIX-only refs.
    _libs = os.path.join(sysconfig.get_config_var("base"), "libs")
    _embed = " ".join(os.path.join(_libs, l).replace("\\", "/")
                      for l in ("mp_embed.lib", "mp_embed_data.lib"))
    env["LDFLAGS"] = (env.get("LDFLAGS", "") + " " + _embed
                      + " Shlwapi.lib /FORCE:UNRESOLVED").strip()
    config_args = ["-Csetup-args=-Dblas=openblas", "-Csetup-args=-Dlapack=openblas",
                   "-Csetup-args=-Db_lto=false"]
    if "MP_JOBS" in env:
        config_args += ["-Ccompile-args=-j" + env["MP_JOBS"]]
    __mp__.run(sys.executable, "-m", "build", "-w", "--no-isolation", "-o", ".", *config_args, env=env)

    wheel_location = glob.glob("numpy-*.whl")[0]

    wheel_files = []
    with TemporaryDirectory() as tmpdir:
        with WheelFile(wheel_location) as wf:
            for filename in wf.namelist():
                wheel_files.append(filename)
                wf.extract(filename, tmpdir)

        ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
        __mp__.rename_symbols_in_file(os.path.join(tmpdir, f"numpy\\_core\\_multiarray_tests{ext_suffix}"),
                                      "np_multiarray_tests_")
        __mp__.analyze_and_rename_library_symbols(tmpdir, "numpy",
                                                  protected_symbol_patterns=["_?PyUFunc.+", "_?npy_.+", "_?PyArray.+",
                                                                             "_?Py.+_Type"],
                                                  exclude_libraries=["_multiarray_umath*"])

        with WheelFile(wheel_location, 'w') as wf:
            for filename in wheel_files:
                wf.write(os.path.join(tmpdir, filename), filename)

    wheel_name = os.path.basename(wheel_location)
    shutil.copy(wheel_location, os.path.join(wheel_directory, wheel_name))
    return os.path.join(wheel_directory, wheel_name)
