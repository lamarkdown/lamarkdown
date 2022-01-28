'''
Implements the '--live/-l' mode, to give the user immediate feedback while editing.

We launch a simple web server, open a web browser, monitor source files (both the .md file and .py
build modules), and reload the page when anything changes.

*DO NOT* make this web server publically accessible. It is intended only as a productivity
improvement for a single local user, and is not designed for security or performance.
'''

from lamarkdown.lib import md_compiler, build_params

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


PORT_RANGE = range(8000, 8020)

class Content:
    def __init__(self):
        self.filename = {}
        self.title = {}
        self.fullHtml = {}
        self.updateN = 0
        self.path = {}

    def update(self, buildParams: build_params.BuildParams):
        self.title = {}
        self.fullHtml = {}
        for variant, targetFile in buildParams.target_files.items():
            with open(targetFile) as f:
                fullHtml = f.read()

            match = re.search('<title[^>]*>(.*?)</\s*title\s*>', fullHtml, flags = re.IGNORECASE | re.DOTALL)
            self.title[variant] = match[1] if match else '[No Title]'
            self.fullHtml[variant] = fullHtml
            self.filename[variant] = os.path.basename(targetFile)
            self.path[variant] = os.path.dirname(targetFile)

        self.updateN += 1



def getHandler(content: Content):

    class _handler(http.server.BaseHTTPRequestHandler):

        def send_main_content(self, variant: str):
            self.send_response(200)
            self.send_header('ContentType', 'text/html')
            self.end_headers()

            # Insert JS code to poll this server for updates, and reload if an update is detected.
            message = re.sub(
                '</\s*head\s*>',
                f'''
                    <script>
                        setInterval(
                            () => {{
                                fetch('/query')
                                    .then(response => response.text())
                                    .then(text =>
                                    {{
                                        if(text != '{content.updateN}')
                                        {{
                                            document.location.reload();
                                        }}
                                    }})
                            }},
                            500
                        );
                    </script>
                    </head>
                ''',
                content.fullHtml[variant]
            )

            if len(content.title) >= 2:

                # If we have at least two variants, insert a special panel showing a link to each separate variant.
                message = message.replace(
                    '</head>',
                    '''
                    <style>
                        @media print {
                            #variantspanel { display: none; }
                        }

                        @media screen {
                            #variantspanel { position: fixed; background: white; border-radius: 0.5ex; color: black; padding: 1em; right: 1ex; top: 1ex; }
                        }
                    </style>
                    </head>
                    '''
                )

                message = message.replace(
                    '<body>',
                    '<body><div id="variantspanel">' +
                        '<strong>Variants</strong><br>' +
                        '<br>'.join(f'<a href="/{v}{"/" if v else ""}index.html">{f}</a>' for v, f in content.filename.items()) +
                        '</div>',
                )

            self.wfile.write(message.encode('utf-8'))


        def send_file(self, path: str):
            self.send_response(200)
            #self.send_header('ContentType', 'text/plain')
            self.end_headers()
            self.wfile.write(open(path, 'rb').read())


        def do_GET(self):
            if self.path == '/':
                # Try to show the default variant (named '') if there is one, or else just pick
                # whichever variant comes out first.

                if '' in content.title:
                    self.send_main_content('')
                else:
                    self.send_main_content(next(iter(content.title.keys)))

            elif self.path == '/query':
                self.send_response(200)
                self.send_header('ContentType', 'text/plain')
                self.end_headers()
                self.wfile.write(str(content.updateN).encode('utf-8'))

            elif (
                (match := re.fullmatch(f'/(?P<variant>[^/]*)/?index.html', self.path)) and
                (variant := match['variant']) in content.title
            ):
                # Having verified that the URL contains the name of a variant, send that variant.
                self.send_main_content(variant)

            elif (
                (match := re.fullmatch(f'/(?P<variant>[^/]*)/(?P<file>.+)', self.path)) and
                ((variant := match['variant']) in content.title) and
                (full_path := os.path.join(content.path[variant], match['file'].replace('/', os.sep))) and
                os.path.isfile(full_path)
            ):
                self.send_file(full_path)

            elif (
                (match := re.fullmatch(f'/(?P<file>.+)', self.path)) and
                ('' in content.title) and
                (full_path := os.path.join(content.path[''], match['file'].replace('/', os.sep))) and
                os.path.isfile(full_path)
            ):
                self.send_file(full_path)

            else:
                self.send_response(404)
                self.send_header('ContentType', 'text/plain')
                self.end_headers()
                self.wfile.write('404 - Yeah nah mate.'.encode('utf-8'))


        def log_message(self, format, *args):
            pass

    return _handler



def watchLive(buildParams: build_params.BuildParams):

    content = Content()
    content.update(buildParams)

    class SourceFileEventHandler(watchdog.events.FileSystemEventHandler):
        def on_closed(self, event): # When something else finishes writing to a file
            if event.src_path == buildParams.src_file or event.src_path in buildParams.build_files:
                try:
                    md_compiler.compile(buildParams)
                    content.update(buildParams)
                except Exception as e:
                    print('---')
                    traceback.print_exc(e)
                    print('---')

    paths = {os.path.dirname(p) for p in [buildParams.src_file] + buildParams.build_files if p}

    handler = SourceFileEventHandler()
    observer = watchdog.observers.Observer()
    for path in paths:
        observer.schedule(handler, path)
    observer.start()

    try:
        mainThread = threading.current_thread()

        # Iterate over a port range, and pick the first free port.
        for port in PORT_RANGE:
            try:
                # Create the server. This attempts to bind to the given port.
                server = http.server.HTTPServer(('', port), getHandler(content))

            except OSError:
                continue # Port in use; try next one.

            else:
                print(f'Monitoring changes to source and build files.\nBrowse to http://localhost:{port}\nPress Ctrl-C to quit.')

                # We want to open a web browser at the address we're serving, but not before the
                # server is running. Hence, we start a new thread, which waits 0.5 secs while the
                # main thread calls serve_forever(), then runs the browser.
                def openBrowser():
                    time.sleep(0.5)
                    webbrowser.open(f'http://localhost:{port}')
                    mainThread.join()

                threading.Thread(target=openBrowser).start()
                break

        server.serve_forever()


    except KeyboardInterrupt: # Ctrl-C
        pass

    finally:
        observer.stop()
        observer.join()