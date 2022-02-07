#!/usr/bin/python

from lamarkdown.lib import md_compiler
from lamarkdown.lib.build_params import BuildParams

import argparse
import os.path
import time

def main():
    parser = argparse.ArgumentParser(
        description='Compile .md (markdown) files to .html using the Python Markdown library. See README.md for key details.')

    parser.add_argument('input', metavar='INPUT.md', type=str,
                        help='Input markdown (.md) file')

    parser.add_argument('-o', '--output', metavar='OUTPUT.html', type=str,
                        help='Output HTML file. (By default, this is based on the input filename.)')

    parser.add_argument('-b', '--build', metavar='BUILD.py', type=str,
                        help='A build .py file to override markdown/css settings.')

    parser.add_argument('-l', '--live', action='store_true',
                        help='Keep running, recompile automatically when source changes are detected, and serve the resulting file from localhost.')

    args = parser.parse_args()

    src_file = os.path.abspath(args.input)
    base_name = src_file.rsplit('.', 1)[0]

    build_params = BuildParams(
        src_file = src_file,
        target_file = args.output or (base_name + '.html'),
        build_files = [
            os.path.abspath('md_build.py'),
            os.path.abspath(base_name + '.py'),
            os.path.abspath(args.build) if args.build else None
        ],
        build_dir = os.path.join('build', os.path.basename(src_file) + '.tmp')
    )
    os.makedirs(build_params.build_dir, exist_ok = True)

    md_compiler.compile(build_params)

    if args.live:
        from lamarkdown.lib import live
        live.watch_live(build_params)

if __name__ == "__main__":
    main()
