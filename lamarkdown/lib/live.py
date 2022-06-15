'''
Implements the '--live/-l' mode, to give the user immediate feedback while editing.

We launch a simple web server, open a web browser, monitor source files (both the .md file and .py
build modules), and reload the page when anything changes.

*DO NOT* make this web server publically accessible. It is intended only as a productivity
improvement for a single local user, and is not designed for security or performance.
'''

from lamarkdown.lib import md_compiler
from lamarkdown.lib.build_params import BuildParams, Variant

import watchdog.observers
import watchdog.events

import datetime
import http.server
import os.path
import re
import threading
import time
import traceback
import webbrowser
from typing import List


DEFAULT_PORT_RANGE = range(8000, 8020)

ANY_ADDRESS = '' # The empty string will cause the server to listen on all interfaces, as per the
                 # socket documentation https://docs.python.org/3/library/socket.html
LOOPBACK_ADDRESS = '127.0.0.1'


class Content:
    def __init__(self, build_params):
        self.filename = {}
        self.title = {}
        self.full_html = {}
        self.update_n = 0
        self.path = {}
        self.base_variant = None
        self.build_params = build_params
        self.compile_lock = threading.Lock()

    def update(self, all_build_params: List[BuildParams]):
        self.title = {}
        self.full_html = {}
        self.base_variant = all_build_params[0].name
        for build_params in all_build_params:
            name = build_params.name
            output_file = build_params.output_file

            with open(output_file) as f:
                full_html = f.read()

            match = re.search('<title[^>]*>(.*?)</\s*title\s*>', full_html, flags = re.IGNORECASE | re.DOTALL)
            self.title[name] = match[1] if match else '[No Title]'
            self.full_html[name] = full_html
            self.filename[name] = os.path.basename(output_file)
            self.path[name] = os.path.dirname(output_file)

        self.update_n += 1

    def clear_cache(self):
        self.build_params.progress.warning('Live updating', 'Clearing cache')
        self.build_params.cache.clear()

    def recompile(self):
        self.compile_lock.acquire()
        try:
            self.update(md_compiler.compile(self.build_params))
        except Exception as e:
            self.build_params.progress.error_from_exception('Live updating', e)
        finally:
            self.compile_lock.release()



def get_handler(content: Content):

    control_panel_style = re.sub('(\n\s+)+', ' ', '''
        <style>
            @media print {
                #_lamd_control_panel { display: none; }
            }
            @media screen {
                #_lamd_control_panel {
                    position: fixed;
                    background: white;
                    color: black;
                    font-family: sans-serif;
                    font-size: small;
                    line-height: 1.5;
                    border-radius: 0.5ex;
                    padding: 1em;
                    right: 1ex;
                    top: 1ex;
                    overflow-wrap: anywhere;
                    overflow-y: auto;
                    max-width: 20%;
                    max-height: 90%;
                    z-index: 1000;
                }
                #_lamd_control_panel button {
                    margin-top: 1ex;
                }
                #_lamd_msg[data-msg]::before {
                    content: attr(data-msg);
                    display: block;
                    margin-bottom: 1em;
                    color: red;
                    font-weight: bold;
                }
            }
        </style>
        '''
    ).strip()

    favicon_data = re.sub('\s+', '', '''
        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''')

    favicon_link = f'<link rel="icon" type="image/png" href="data:;base64,{favicon_data}" />'

    CHECK_INTERVAL       = 500 # milliseconds
    ERROR_COUNTDOWN      = 5   # times the check interval
    DISCONNECT_COUNTDOWN = 30  # times the check interval

    POST_RESPONSE = 'ok'

    VARIANT_QUERY_REGEX = re.compile('/(?P<variant>[^/]*)/?index.html')
    VARIANT_FILE_QUERY_REGEX = re.compile('/(?P<variant>[^/]*)/(?P<file>.+)')
    BASE_FILE_QUERY_REGEX = re.compile('/(?P<file>.+)')


    class _handler(http.server.BaseHTTPRequestHandler):

        def send_main_content(self, variant_name: str):
            self.send_response(200)
            self.send_header('ContentType', 'text/html')
            self.end_headers()

            # JS code to poll this server for updates, and reload if an update is detected.
            update_script = re.sub('(\n\s+)+', ' ', f'''
                <script>
                    (() => {{
                        let errorCountdown = {ERROR_COUNTDOWN};
                        let disconnectCountdown = {DISCONNECT_COUNTDOWN};

                        function showError(user_msg, internal_detail)
                        {{
                            console.log(user_msg);
                            console.log(internal_detail);
                            document.getElementById('_lamd_msg').dataset.msg = user_msg;
                        }}

                        function update()
                        {{
                            if(disconnectCountdown > 0)
                            {{
                                fetch('/query')
                                    .then(response => response.text())
                                    .then(text =>
                                    {{
                                        if(text != '{content.update_n}')
                                        {{
                                            document.location.reload();
                                        }}
                                        setTimeout(update, {CHECK_INTERVAL});
                                        errorCountdown = {ERROR_COUNTDOWN};
                                        disconnectCountdown = {DISCONNECT_COUNTDOWN};
                                    }})
                                    .catch(error =>
                                    {{
                                        if(errorCountdown > 0)
                                        {{
                                            errorCountdown--;
                                            if(errorCountdown == 0)
                                            {{
                                                showError('Unable to contact server.', error.message);
                                            }}
                                        }}
                                        else
                                        {{
                                            disconnectCountdown--;
                                            if(disconnectCountdown == 0)
                                            {{
                                                showError('Disconnected from server. Reload the page to resume, once the server is running again.',
                                                          error.message);
                                            }}
                                        }}
                                    }});
                            }}
                        }};
                        setTimeout(update, {CHECK_INTERVAL});

                        document.getElementById('_lamd_cleanbuild_btn').onclick = (event) =>
                        {{
                            fetch('/cleanbuild', {{method: 'POST'}})
                                .then(response => response.text())
                                .then(text =>
                                {{
                                    if(text != '{POST_RESPONSE}')
                                    {{
                                        showError('Server returned unexpected response', `"${{text}}"`);
                                    }}
                                }})
                                .catch(error => showError('Unable to contact server.', error.message));
                            event.preventDefault();
                        }};

                        document.getElementById('_lamd_timestamp').innerHTML = 'Last updated:<br/>' + new Date().toLocaleString();
                    }})();
                </script>
            ''').strip()

            control_panel = re.sub('(\n\s+)+', ' ', '''
                <div id="_lamd_control_panel">
                    <div id="_lamd_timestamp"></div>
                    <div id="_lamd_msg"></div>
                    <form><button id="_lamd_cleanbuild_btn">Clean Build</button></form>
                ''')
            if len(content.title) >= 2:
                control_panel += (
                    '<hr/><strong>Variants</strong><br/>' +
                    '<br/>'.join(f'<a href="/{v}{"/" if v else ""}index.html">{f}</a>'
                                for v, f in content.filename.items())
                )
            control_panel += '</div>'

            message = content.full_html[variant_name] \
                .replace('</head>', f'{favicon_link}\n{control_panel_style}\n</head>') \
                .replace('<body>', f'<body>\n{control_panel}') \
                .replace('</body>', f'{update_script}\n</body>')

            self.wfile.write(message.encode('utf-8'))


        def send_file(self, path: str):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(open(path, 'rb').read())


        def do_POST(self):
            if self.path == '/cleanbuild':
                self.send_response(200)
                self.send_header('ContentType', 'text/plain')
                self.end_headers()
                self.wfile.write(POST_RESPONSE.encode('utf-8'))
                def clean_build():
                    content.clear_cache()
                    content.recompile()
                threading.Thread(target = clean_build).start()
            else:
                self._no()


        def do_GET(self):
            if self.path == '/':
                # Try to show the default variant (named '') if there is one, or else just pick
                # whichever variant comes out first.

                if content.base_variant:
                    self.send_main_content(content.base_variant)
                else:
                    self.send_main_content(next(iter(content.title.keys())))
                return

            if self.path == '/query':
                self.send_response(200)
                self.send_header('ContentType', 'text/plain')
                self.end_headers()
                self.wfile.write(str(content.update_n).encode('utf-8'))
                return

            re_match = VARIANT_QUERY_REGEX.fullmatch(self.path)
            if re_match:
                variant_name = re_match['variant']
                if variant_name in content.title:
                    self.send_main_content(variant_name)
                    return

            re_match = VARIANT_FILE_QUERY_REGEX.fullmatch(self.path)
            if re_match:
                variant_name = re_match['variant']
                full_path = os.path.join(content.path[variant_name],
                                         re_match['file'].replace('/', os.sep))
                if variant_name in content.title and os.path.isfile(full_path):
                    self.send_file(full_path)
                    return

            re_match = BASE_FILE_QUERY_REGEX.fullmatch(self.path)
            if re_match:
                full_path = os.path.join(content.path[''], re_match['file'].replace('/', os.sep))
                if '' in content.title and os.path.isfile(full_path):
                    self.send_file(full_path)
                    return

            self._no()

        def _no(self):
            self.send_response(404)
            self.send_header('ContentType', 'text/plain')
            self.end_headers()
            self.wfile.write('404 - Yeah nah mate.'.encode('utf-8'))

        def log_message(self, format, *args):
            pass

    return _handler



def watch_live(build_params    : BuildParams,
               all_build_params: List[BuildParams],
               address         : str   = LOOPBACK_ADDRESS,
               port_range      : range = DEFAULT_PORT_RANGE,
               launch_browser  : bool  = True):

    content = Content(build_params)
    content.update(all_build_params)

    class SourceFileEventHandler(watchdog.events.FileSystemEventHandler):
        def on_closed(self, event): # When something else finishes writing to a file
            if event.src_path == build_params.src_file or event.src_path in build_params.build_files:
                content.recompile()

    paths = {os.path.dirname(p) for p in [build_params.src_file] + build_params.build_files if p}

    handler = SourceFileEventHandler()
    observer = watchdog.observers.Observer()
    for path in paths:
        observer.schedule(handler, path)
    observer.start()

    try:
        main_thread = threading.current_thread()

        # Iterate over a port range, and pick the first free port.
        port = None
        for try_port in port_range:
            try:
                # Create the server. This attempts to bind to the given port.
                server = http.server.HTTPServer((address, try_port), get_handler(content))
                port = try_port
                break
            except OSError: # Port in use; try next one.
                build_params.progress.warning('Live updating', f'Port {try_port} appears to be in use.')

        if port:
            build_params.progress.progress('Live updating', 'Launching server and browser, and monitoring changes to source/build files.',
                f'Browse to http://{address or "localhost"}:{port}\nPress Ctrl-C to quit.')

            if launch_browser:
                # We want to open a web browser at the address we're serving, but not before the
                # server is running. Hence, we start a new thread, which waits 0.5 secs while the
                # main thread calls serve_forever(), then runs the browser.
                def open_browser():
                    time.sleep(0.5)
                    webbrowser.open(f'http://localhost:{port}')
                    main_thread.join()

                threading.Thread(target = open_browser).start()

            server.serve_forever()
        else:
            build_params.progress.error(
                'Live updating',
                f'Cannot launch server: all ports in range {port_range.start}-{port_range.stop - 1} are in use.')

    except KeyboardInterrupt: # Ctrl-C
        pass

    finally:
        observer.stop()
        observer.join()
