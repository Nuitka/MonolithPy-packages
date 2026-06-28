import __mp__
import glob
import os
import platform
import shutil
import subprocess
import tempfile

from wheel.wheelfile import WheelFile


SHEENBIDI_VERSION = "3.0.0"
SHEENBIDI_URL = (
    "https://github.com/Tehreer/SheenBidi/archive/refs/tags/"
    "v{0}/sheenbidi-{0}.tar.gz".format(SHEENBIDI_VERSION)
)

RAQM_VERSION = "0.10.5"


def _deployment_target():
    return "11.0" if platform.machine() == "arm64" else "10.13"


def _build_sheenbidi(work_dir, env):
    """Build SheenBidi as a static library via its own (CMake) build."""
    src_root = os.path.join(work_dir, "sheenbidi-src")
    os.makedirs(src_root, exist_ok=True)
    __mp__.download_extract(SHEENBIDI_URL, src_root)
    entries = [e for e in os.listdir(src_root) if not e.startswith(".")]
    src_dir = os.path.join(src_root, entries[0])

    build_dir = os.path.join(work_dir, "sheenbidi-build")
    os.makedirs(build_dir)
    install_dir = os.path.join(work_dir, "sheenbidi-install")
    os.makedirs(install_dir)

    arch = platform.machine()
    cmake_arch_args = ["-DCMAKE_OSX_ARCHITECTURES=" + arch,
                       "-DCMAKE_OSX_DEPLOYMENT_TARGET=" + _deployment_target()]

    __mp__.run_build_tool_exe(
        "cmake", "cmake",
        "-G", "Ninja",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_PREFIX=" + install_dir,
        "-DBUILD_SHARED_LIBS=OFF",
        "-DSB_CONFIG_UNITY=ON",
        "-DBUILD_TESTING=OFF",
        "-DBUILD_GENERATOR=OFF",
        *cmake_arch_args,
        src_dir,
        cwd=build_dir, env=env,
    )
    __mp__.run_build_tool_exe("ninja", "ninja", cwd=build_dir, env=env)
    __mp__.run_build_tool_exe("ninja", "ninja", "install", cwd=build_dir, env=env)
    return install_dir


def run(wheel_directory):
    raqm_src = os.getcwd()  # raqm sdist, extracted here by MonolithPy

    env = os.environ.copy()
    env["MACOSX_DEPLOYMENT_TARGET"] = _deployment_target()
    # MonolithPy's LLVM clang needs the macOS SDK to compile/link; the darwin
    # driver adds -isysroot from SDKROOT (meson would otherwise fail its sanity
    # check at link time).
    env["SDKROOT"] = subprocess.check_output(
        ["xcrun", "--show-sdk-path"], text=True).strip()
    env["PATH"] = (
        os.path.dirname(__mp__.find_build_tool_exe("cmake", "cmake")) + os.pathsep +
        os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja")) + os.pathsep +
        os.path.dirname(__mp__.find_build_tool_exe("clang", "clang")) + os.pathsep +
        env.get("PATH", "")
    )
    env["PKG_CONFIG"] = "/disabled"

    work_dir = tempfile.mkdtemp(prefix="mpy-raqm-")
    sb_prefix = _build_sheenbidi(work_dir, env)
    sb_lib = glob.glob(os.path.join(sb_prefix, "lib", "lib[Ss]heen[Bb]idi*.a"))[0]
    sb_inc = os.path.join(sb_prefix, "include")

    # freetype/harfbuzz come from MonolithPy's bundled dependency_libs/base.
    base = __mp__.find_dep_root("base")
    ft_lib = glob.glob(os.path.join(base, "lib", "libfreetype*.a"))[0]
    hb_lib = glob.glob(os.path.join(base, "lib", "libharfbuzz*.a"))[0]

    # Feed our prebuilt deps to raqm via meson's subproject fallbacks. The stub
    # versions only need to satisfy raqm's minimum checks (freetype2 >= 24.0.18
    # -- its pkg-config/libtool version, ~26.x for FreeType 2.13.x; harfbuzz
    # >= 3.0.0); the real libraries are resolved at the final relink. raqm's own
    # meson adds -DRAQM_SHEENBIDI_GT_2_9 because the sheenbidi stub reports >= 2.9.
    subp = os.path.join(raqm_src, "subprojects")
    __mp__.write_meson_dep_subproject(
        subp, "freetype2", "freetype_dep",
        include_dirs=[os.path.join(base, "include"),
                      os.path.join(base, "include", "freetype2")],
        link_libs=[ft_lib],
        version="26.2.20", options=["png", "bzip2", "zlib", "harfbuzz"])
    __mp__.write_meson_dep_subproject(
        subp, "harfbuzz", "libharfbuzz_dep",
        include_dirs=[os.path.join(base, "include"),
                      os.path.join(base, "include", "harfbuzz")],
        link_libs=[hb_lib],
        version="10.0.0",
        options=["freetype", "glib", "gobject", "cairo", "icu", "tests"])
    __mp__.write_meson_dep_subproject(
        subp, "sheenbidi", "sheenbidi_dep",
        include_dirs=[sb_inc], link_libs=[sb_lib], version=SHEENBIDI_VERSION)

    build_dir = os.path.join(work_dir, "raqm-build")
    install_dir = os.path.join(work_dir, "raqm-install")
    __mp__.meson(
        "setup", build_dir,
        "-Dsheenbidi=true", "-Ddefault_library=static", "-Dtests=false",
        "--force-fallback-for=freetype2,harfbuzz,sheenbidi",
        "--wrap-mode=nodownload",
        "--prefix=" + install_dir,
        cwd=raqm_src, env=env,
    )
    __mp__.meson("compile", "-C", build_dir, cwd=raqm_src, env=env)
    __mp__.meson("install", "-C", build_dir, cwd=raqm_src, env=env)

    lib_dir = os.path.join(install_dir, "lib")
    include_dir = os.path.join(install_dir, "include")

    # meson produces libraqm.a (Unix convention); keep that name.
    if not glob.glob(os.path.join(lib_dir, "libraqm*.a")):
        raise RuntimeError("meson did not produce a raqm static library")

    if not os.path.exists(os.path.join(include_dir, "raqm-version.h")):
        gen = glob.glob(os.path.join(build_dir, "**", "raqm-version.h"), recursive=True)
        if gen:
            shutil.copy(gen[0], include_dir)

    # Ship SheenBidi alongside raqm (resolved at the final interpreter relink).
    shutil.copy(sb_lib, os.path.join(lib_dir, "libsheenbidi.a"))
    for root, dirs, files in os.walk(sb_inc):
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), sb_inc)
            dst = os.path.join(include_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(os.path.join(root, name), dst)

    result_wheel = os.path.join(
        wheel_directory, __mp__.get_wheel_name("mpy_dep_raqm", RAQM_VERSION))
    with WheelFile(result_wheel, 'w') as w:
        __mp__.add_wheel_manifest(w, "mpy-dep-raqm", RAQM_VERSION)
        __mp__.add_wheel_dep_libs(
            w, "raqm", os.path.join(lib_dir, "*"), base_dir=lib_dir)
        __mp__.add_wheel_dep_include(
            w, "raqm", os.path.join(include_dir, "*"), base_dir=include_dir)

    return result_wheel
