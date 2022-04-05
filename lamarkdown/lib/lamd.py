#!/usr/bin/python

from . import md_compiler
from .build_params import BuildParams
from .progress import Progress

import diskcache

import argparse
import os.path
import time

DIRECTORY_BUILD_FILE = 'md_build.py'


def existing_file(a: str) -> str:
    if not os.path.exists(a):
        raise ValueError(f'File "{a}" not found')
    return a


def main():
    parser = argparse.ArgumentParser(
        description='Compile .md (markdown) files to .html using the Python Markdown library. See README.md for key details.')

    parser.add_argument('input', metavar='INPUT.md', type=str,
                        help='Input markdown (.md) file')

    parser.add_argument('-o', '--output', metavar='OUTPUT.html', type=str,
                        help='Output HTML file. (By default, this is based on the input filename.)')

    parser.add_argument('-b', '--build', metavar='BUILD.py', type=existing_file, action='append',
                        help='Manually specify a build (.py) file, which itself specifies extensions (to Python-Markdown), CSS, JavaScript, etc.')

    parser.add_argument('-B', '--no-auto-build-files', action='store_true',
                        help='Suppresses build file auto-detection, so that only build files specified with -b/--build will be loaded. Lamarkdown will not automatically read "md_build.py" or "<source>.py" in this case.')

    parser.add_argument('-D', '--no-build-defaults', action='store_true',
                        help='Suppresses the automatic default settings in case no build files exist. Has no effect if any build files are read.')

    parser.add_argument('-l', '--live', action='store_true',
                        help='Keep running, recompile automatically when source changes are detected, and serve the resulting file from localhost.')
    
    parser.add_argument('--clean', action='store_true',
                        help='Clear the cache before compiling the document.')

    args = parser.parse_args()

    src_file = os.path.abspath(args.input)
    src_dir = os.path.dirname(src_file)
    base_name = src_file.rsplit('.', 1)[0]
    build_dir = os.path.join(src_dir, 'build', os.path.basename(src_file))
    
    # Changing into the source directory (in case we're not in it) means that further file paths
    # referenced during the build process will be relative to the source file, and not 
    # (necessarily) whatever arbitrary directory we started in.
    os.chdir(src_dir)

    build_params = BuildParams(
        src_file = src_file,
        target_file = args.output or (base_name + '.html'),
        build_files =
            (args.build or []) if args.no_auto_build_files
            else [
                os.path.join(src_dir, DIRECTORY_BUILD_FILE),
                os.path.join(src_dir, base_name + '.py'),
                *(args.build or [])
            ],
        build_dir = build_dir,
        build_defaults = not args.no_build_defaults,
        cache = diskcache.Cache(os.path.join(build_dir, 'cache')),
        progress = Progress(),
        is_live = args.live is True
    )
    os.makedirs(build_dir, exist_ok = True)
    
    if args.clean:
        build_params.cache.clear()

    all_build_params = md_compiler.compile(build_params)

    if args.live:
        from lamarkdown.lib import live
        live.watch_live(build_params, all_build_params)

if __name__ == "__main__":
    main()
