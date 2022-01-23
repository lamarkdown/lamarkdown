#!/usr/bin/python

from lamarkdown.lib import md_compiler
from lamarkdown.lib import build_params

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

    srcFile = os.path.abspath(args.input)
    baseName = srcFile.removesuffix('.md')

    buildParams = build_params.BuildParams(
        src_file = srcFile,
        target_file = args.output or (baseName + '.html'),
        build_files = [
            #os.path.join(os.path.dirname(os.path.realpath(__file__)), 'default_md_build.py'),
            os.path.abspath('md_build.py'),
            os.path.abspath(baseName + '.py'),
            os.path.abspath(args.build) if args.build else None
        ],
        build_dir = os.path.join('build', os.path.basename(srcFile) + '.tmp')
    )
    os.makedirs(buildParams.build_dir, exist_ok = True)

    md_compiler.compile(buildParams)

    if args.live:
        from lamarkdown.lib import live
        live.watchLive(buildParams)

if __name__ == "__main__":
    main()
