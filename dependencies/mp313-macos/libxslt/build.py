import __mp__
import json
import shutil
import os
import sysconfig


def run(temp_dir: str):
    __mp__.download_extract("https://download.gnome.org/sources/libxslt/1.1/libxslt-1.1.35.tar.xz", temp_dir)

    os.chdir(os.path.join(temp_dir, "libxslt-1.1.35"))

    __mp__.run_with_output("/bin/bash",
                           "configure",
                           f"CC={sysconfig.get_config_var('CC')}",
                           f"CXX={sysconfig.get_config_var('CXX')}",
                           "--prefix=" + __mp__.find_dep_root("libxslt"),
                           "--with-libxml-prefix=" + __mp__.find_dep_root("libxml2"),
                           "--disable-shared")

    __mp__.run_with_output("make", f"-j{__mp__.get_num_jobs()}")
    __mp__.run_with_output("make", "install")

    with open(os.path.join(__mp__.find_dep_libs("libxslt"), "libexslt.a.link.json"), 'w') as f:
        json.dump({'libraries': ['gcrypt'], "library_dirs": []}, f)
