import __np__
from typing import *
from pip._internal.req.req_install import InstallRequirement

import os


def run(req: InstallRequirement,
        temp_dir: str,
        source_dir: str,
        install_options: List[str],
        global_options: Optional[Sequence[str]],
        root: Optional[str],
        home: Optional[str],
        prefix: Optional[str],
        warn_script_location: bool,
        use_user_site: bool,
        pycompile: bool
        ):

    __np__.setup_compiler_env()

    os.chdir(source_dir)

    os.environ["LXML_STATIC_INCLUDE_DIRS"] = os.pathsep.join([
        __np__.find_dep_include("iconv"),
        __np__.find_dep_include("libxml2"),
        __np__.find_dep_include("libxslt")
    ])

    os.environ["LXML_STATIC_LIBRARY_DIRS"] = os.pathsep.join([
        __np__.find_dep_libs("iconv"),
        __np__.find_dep_libs("libxml2"),
        __np__.find_dep_libs("libxslt"),
        __np__.find_dep_libs("zlib")
    ])

    __np__.run_with_output("python.exe", os.path.join(source_dir, "setup.py"), "--static", "install")
