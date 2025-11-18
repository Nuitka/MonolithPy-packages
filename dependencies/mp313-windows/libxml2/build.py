import __np__
import shutil
import os


def run(temp_dir: str):
    __np__.download_extract("https://github.com/GNOME/libxml2/archive/refs/tags/v2.9.12.zip", temp_dir)

    os.chdir(os.path.join(temp_dir, "libxml2-2.9.12", "win32"))

    __np__.run_compiler_exe(
        "cscript.exe", "configure.js",
        "compiler=msvc",
        "prefix=" + os.path.join(temp_dir, "install_tmp"),
        "cruntime=/MT",
        "include=" + __np__.find_dep_include("iconv"),
        "lib=" + __np__.find_dep_libs("iconv"))

    __np__.setup_compiler_env()

    __np__.nmake("/f", "Makefile.msvc")
    __np__.nmake("/f", "Makefile.msvc", "install")

    shutil.copy(os.path.join(temp_dir, "install_tmp", "lib", "libxml2_a.lib"), os.path.join(temp_dir, "libxml2.lib"))
    shutil.copy(os.path.join(temp_dir, "install_tmp", "lib", "libxml2_a.lib"), os.path.join(temp_dir, "libxml2_a.lib"))

    __np__.prepend_to_file(os.path.join(temp_dir, "install_tmp", "include", "libxml2", "libxml", "xmlexports.h"), "#define LIBXML_STATIC\n")

    __np__.install_dep_libs("libxml2", os.path.join(temp_dir, "libxml2.lib"), os.path.join(temp_dir, "libxml2_a.lib"))
    __np__.install_dep_include("libxml2", os.path.join(temp_dir, "install_tmp", "include", "libxml2", "*"))
