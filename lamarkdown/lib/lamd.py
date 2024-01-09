#!/usr/bin/python

from . import md_compiler
from . import live
from .build_params import BuildParams
from .progress import Progress

import diskcache  # type: ignore
import platformdirs

import argparse
import os
import os.path
import re

DIRECTORY_BUILD_FILE = 'md_build.py'

VERSION = '0.10'


def readable_file_type(a: str) -> str:
    if not os.path.exists(a):
        raise argparse.ArgumentTypeError(f'"{a}" not found')

    if not os.path.isfile(a):
        raise argparse.ArgumentTypeError(f'"{a}" is not a file')

    if not os.access(a, os.R_OK):
        raise argparse.ArgumentTypeError(f'"{a}" is not readable')
    return a


def port_range_type(s: str) -> range:
    match = re.fullmatch('(?P<start>[0-9]+)(-(?P<end>[0-9]+))?', s)
    if not match:
        raise argparse.ArgumentTypeError(
            'Must be a non-negative integer (e.g., 8000), or integer range (e.g., 8000-8010)')

    start = int(match['start'])
    end = int(match['end'] or start)
    if not (1024 <= start <= end <= 65535):
        # Should we restrict ports less than 1024 (privileged ports)? This can't affect ordinary
        # use, particularly as users don't have access to such ports anyway. It may help to hint
        # at the fact that live-update mode is not designed to be a public-facing web server.
        raise argparse.ArgumentTypeError(
            'Port range must be within the range 1024-65535, with start <= end')

    return range(start, end + 1)


def main():
    fetch_cache_dir = platformdirs.user_cache_dir(appname = 'lamarkdown', version = VERSION)

    parser = argparse.ArgumentParser(
        prog        = 'lamd',
        description = ('Compile .md (markdown) files to .html using the Python Markdown library. '
                       'See README.md for key details.'),
        formatter_class = argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '-v', '--version', action = 'version',
        version = f'Lamarkdown {VERSION}\n(fetch cache: {fetch_cache_dir})')

    parser.add_argument(
        'input', metavar = 'INPUT.md', type = readable_file_type,
        help = 'Input markdown (.md) file')

    parser.add_argument(
        '-o', '--output', metavar = 'OUTPUT.html', type = str,
        help = 'Output HTML file. (By default, this is based on the input filename.)')

    parser.add_argument(
        '-b', '--build', metavar = 'BUILD.py', type = readable_file_type, action = 'append',
        help = ('Manually specify a build (.py) file, which itself specifies extensions (to '
                'Python-Markdown), CSS, JavaScript, etc.'))

    parser.add_argument(
        '-B', '--no-auto-build-files', action = 'store_true',
        help = ('Suppresses build file auto-detection, so that only build files specified with '
                '-b/--build will be loaded. Lamarkdown will not automatically read "md_build.py" '
                'or "<source>.py" in this case.'))

    parser.add_argument(
        '-e', '--allow-exec', action = 'store_true',
        help = ('Allows execution of code from a markdown document, if/when requested (not just '
                'from the build files).'))

    parser.add_argument(
        '-D', '--no-build-defaults', action = 'store_true',
        help = ('Suppresses the automatic default settings in case no build files exist. Has no '
                'effect if any build files are found and read.'))

    parser.add_argument(
        '--clean', action = 'store_true',
        help = 'Clear the build cache before compiling the document.')

    parser.add_argument(
        '-l', '--live', action = 'store_true',
        help = ('Keep running, recompile automatically when source changes are detected, and '
                'serve the resulting file from a local web server.'))

    parser.add_argument(
        '--address', metavar = 'IP_HOST|"any"', type = str,
        help = ('In live mode, have the server listen at the given address, or all addresses if '
                '"any" is specified. By default, the server listens only on 127.0.0.1 (loopback). '
                '*USE WITH CAUTION!* Do not use this option to expose the built-in web server to '
                'the public internet, or other untrusted parties. (Upload the output HTML file to '
                'a proper production web server for that.)'))

    parser.add_argument(
        '--port', metavar = 'PORT[-PORT]', type = port_range_type,
        help = ('In live mode, listen on the first available port in this range. By default, this '
                f'is {live.DEFAULT_PORT_RANGE.start}-{live.DEFAULT_PORT_RANGE.stop}.'))

    parser.add_argument(
        '-W', '--no-browser', action = 'store_true',
        help = 'Do not automatically launch a web browser when starting live mode with -l/--live.')


    args = parser.parse_args()

    src_file = os.path.abspath(args.input)
    src_dir = os.path.dirname(src_file)
    base_name = src_file.rsplit('.', 1)[0]
    build_dir = os.path.join(src_dir, 'build', os.path.basename(src_file))
    build_cache_dir = os.path.join(build_dir, 'cache')

    progress = Progress()
    if args.output:
        if os.path.isdir(args.output):
            target_file = os.path.join(args.output, os.path.basename(base_name)) + '.html'
        else:
            target_file = args.output
    else:
        target_file = base_name + '.html'

    for f in [target_file, os.path.dirname(os.path.abspath(target_file))]:
        if not os.access(f, os.W_OK):
            progress.warning('output', msg = f'"{f}" is not writable')


    # Changing into the source directory (in case we're not in it) means that further file paths
    # referenced during the build process will be relative to the source file, and not
    # (necessarily) whatever arbitrary directory we started in.
    os.chdir(src_dir)

    base_build_params = BuildParams(
        src_file = src_file,
        target_file = target_file,
        build_files = (
            (args.build or []) if args.no_auto_build_files
            else [
                os.path.join(src_dir, DIRECTORY_BUILD_FILE),
                os.path.join(src_dir, base_name + '.py'),
                *(args.build or [])
            ]),
        build_dir = build_dir,
        build_defaults = not args.no_build_defaults,
        build_cache = diskcache.Cache(build_cache_dir),
        fetch_cache = diskcache.Cache(fetch_cache_dir),
        progress = progress,
        is_live = args.live is True,
        allow_exec_cmdline = args.allow_exec is True,
        allow_exec         = args.allow_exec is True
    )
    os.makedirs(build_dir, exist_ok = True)

    if args.clean:
        base_build_params.build_cache.clear()

    complete_build_params = md_compiler.compile(base_build_params)

    if args.live:
        address = (
            live.ANY_ADDRESS
            if args.address == 'any'
            else (args.address or live.LOOPBACK_ADDRESS))
        port_range = args.port or live.DEFAULT_PORT_RANGE

        live.LiveUpdater(
            base_build_params,
            complete_build_params
        ).run(
            address = address,
            port_range = port_range,
            launch_browser = args.no_browser is not True
        )


if __name__ == "__main__":
    main()
