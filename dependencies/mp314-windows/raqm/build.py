import __mp__
import glob
import os
import shutil
import tempfile

from wheel.wheelfile import WheelFile


SHEENBIDI_VERSION = "3.0.0"
SHEENBIDI_URL = (
    "https://github.com/Tehreer/SheenBidi/archive/refs/tags/"
    "v{0}/sheenbidi-{0}.tar.gz".format(SHEENBIDI_VERSION)
)

RAQM_VERSION = "0.10.5"


def _build_sheenbidi(work_dir, env):
    """Build SheenBidi as a static /MT library via its own (CMake) build."""
    src_root = os.path.join(work_dir, "sheenbidi-src")
    os.makedirs(src_root, exist_ok=True)
    __mp__.download_extract(SHEENBIDI_URL, src_root)
    entries = [e for e in os.listdir(src_root) if not e.startswith(".")]
    src_dir = os.path.join(src_root, entries[0])

    build_dir = os.path.join(work_dir, "sheenbidi-build")
    os.makedirs(build_dir)
    install_dir = os.path.join(work_dir, "sheenbidi-install")
    os.makedirs(install_dir)

    __mp__.run_build_tool_exe(
        "cmake", "cmake.exe",
        "-G", "Ninja",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_PREFIX=" + install_dir,
        "-DBUILD_SHARED_LIBS=OFF",
        # Static CRT (/MT) to match matplotlib's b_vscrt=mt and the other deps.
        "-DCMAKE_POLICY_DEFAULT_CMP0091=NEW",
        "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded",
        "-DSB_CONFIG_UNITY=ON",
        "-DBUILD_TESTING=OFF",
        "-DBUILD_GENERATOR=OFF",
        src_dir,
        cwd=build_dir, env=env,
    )
    __mp__.run_build_tool_exe("ninja", "ninja.exe", cwd=build_dir, env=env)
    __mp__.run_build_tool_exe("ninja", "ninja.exe", "install", cwd=build_dir, env=env)
    return install_dir


def run(wheel_directory):
    raqm_src = os.getcwd()  # raqm sdist, extracted here by MonolithPy

    __mp__.setup_compiler_env()

    env = os.environ.copy()
    # meson drives ninja (its backend); SheenBidi's CMake build needs it too.
    env["PATH"] = (
        os.path.dirname(__mp__.find_build_tool_exe("ninja", "ninja.exe")) + os.pathsep +
        env.get("PATH", "")
    )
    env["PKG_CONFIG"] = "/disabled"

    work_dir = tempfile.mkdtemp(prefix="mpy-raqm-")
    sb_prefix = _build_sheenbidi(work_dir, env)
    sb_lib = (glob.glob(os.path.join(sb_prefix, "lib", "*[Ss]heen[Bb]idi*.lib")) or
              glob.glob(os.path.join(sb_prefix, "lib", "*.lib")))[0]
    sb_inc = os.path.join(sb_prefix, "include")

    # Feed our prebuilt deps to raqm via meson's subproject fallbacks. The stub
    # versions only need to satisfy raqm's minimum checks (freetype2 >= 24.0.18
    # -- its pkg-config/libtool version, ~26.x for FreeType 2.13.x; harfbuzz
    # >= 3.0.0); the real libraries are resolved at the final relink. raqm's own
    # meson adds -DRAQM_SHEENBIDI_GT_2_9 because the sheenbidi stub reports >= 2.9.
    subp = os.path.join(raqm_src, "subprojects")
    __mp__.write_meson_dep_subproject(
        subp, "freetype2", "freetype_dep",
        include_dirs=[__mp__.find_dep_include("freetype")],
        link_libs=[os.path.join(__mp__.find_dep_libs("freetype"), "freetype.lib")],
        version="26.2.20", options=["png", "bzip2", "zlib", "harfbuzz"])
    __mp__.write_meson_dep_subproject(
        subp, "harfbuzz", "libharfbuzz_dep",
        include_dirs=[__mp__.find_dep_include("harfbuzz")],
        link_libs=[glob.glob(os.path.join(__mp__.find_dep_libs("harfbuzz"), "*.lib"))[0]],
        version="10.2.0",
        options=["freetype", "glib", "gobject", "cairo", "icu", "tests"])
    __mp__.write_meson_dep_subproject(
        subp, "sheenbidi", "sheenbidi_dep",
        include_dirs=[sb_inc], link_libs=[sb_lib], version=SHEENBIDI_VERSION)

    build_dir = os.path.join(work_dir, "raqm-build")
    install_dir = os.path.join(work_dir, "raqm-install")
    __mp__.meson(
        "setup", build_dir,
        "-Dsheenbidi=true", "-Ddefault_library=static", "-Dtests=false",
        "-Db_vscrt=mt",
        "--force-fallback-for=freetype2,harfbuzz,sheenbidi",
        "--wrap-mode=nodownload",
        "--prefix=" + install_dir,
        cwd=raqm_src, env=env,
    )
    __mp__.meson("compile", "-C", build_dir, cwd=raqm_src, env=env)
    __mp__.meson("install", "-C", build_dir, cwd=raqm_src, env=env)

    lib_dir = os.path.join(install_dir, "lib")
    include_dir = os.path.join(install_dir, "include")

    # Normalize the meson output name to raqm.lib (matches freetype.lib etc.).
    built = (glob.glob(os.path.join(lib_dir, "*raqm*.lib")) or
             glob.glob(os.path.join(lib_dir, "*raqm*.a")))
    if not built:
        raise RuntimeError("meson did not produce a raqm static library")
    if os.path.basename(built[0]) != "raqm.lib":
        shutil.copy(built[0], os.path.join(lib_dir, "raqm.lib"))
        os.remove(built[0])

    # raqm.h is installed by meson; make sure the generated raqm-version.h is too.
    if not os.path.exists(os.path.join(include_dir, "raqm-version.h")):
        gen = glob.glob(os.path.join(build_dir, "**", "raqm-version.h"), recursive=True)
        if gen:
            shutil.copy(gen[0], include_dir)

    # Ship SheenBidi alongside raqm (resolved at the final interpreter relink).
    shutil.copy(sb_lib, os.path.join(lib_dir, "libsheenbidi.lib"))
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
