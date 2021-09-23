from lib import md_compiler

import watchdog.observers
import watchdog.events

import datetime
import http.server
import os.path
import re
import threading
import time
import webbrowser


PORT_RANGE = range(8000, 8020)

class Content:
    def __init__(self):
        self.filename = {}
        self.title = {}
        self.fullHtml = {}
        self.updateN = 0
        
    def update(self, buildParams: md_compiler.BuildParams):
        self.title = {}
        self.fullHtml = {}
        for variant, targetFile in buildParams.targetFiles.items():        
            with open(targetFile) as f:
                fullHtml = f.read()
                
            match = re.search('<title[^>]*>(.*?)</\s*title\s*>', fullHtml, flags = re.IGNORECASE | re.DOTALL)
            self.title[variant] = match[1] if match else '[No Title]'
            self.fullHtml[variant] = fullHtml
            self.filename[variant] = os.path.basename(targetFile)
            
        self.updateN += 1
        
        

def getHandler(content: Content):
    
    class _handler(http.server.BaseHTTPRequestHandler):
        
        def sendFile(self, variant: str):
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
                    '<body>',
                    '<body><div style="position: fixed; background: white; color: black; padding: 1em; right: 1em; top: 1em;">' + 
                        '<strong>Variants</strong><br>' +
                        '<br>'.join(f'<a href="/{v}.html">{f}</a>' for v, f in content.filename.items()) + 
                        '</div>',
                )
                
            self.wfile.write(message.encode('utf-8'))
            
        
        def do_GET(self):
            if self.path == '/':
                # Try to show the default variant (named '') if there is one, or else just pick
                # whichever variant comes out first.
                
                if '' in content.title:
                    message = self.sendFile('')
                else:
                    message = self.sendFile(next(iter(content.title.keys)))
                                
            elif (
                (match := re.fullmatch(r'/(.*)\.html', self.path)) and 
                (variant := match[1]) in content.title
            ):
                # Having verified that the URL contains the name of a variant, send that variant.
                message = self.sendFile(variant)

            elif self.path == '/query':
                self.send_response(200)
                self.send_header('ContentType', 'text/plain')
                self.end_headers()
                self.wfile.write(str(content.updateN).encode('utf-8'))

            else:
                self.send_response(404)
                self.send_header('ContentType', 'text/plain')
                self.end_headers()
                self.wfile.write('404 - Yeah nah mate.'.encode('utf-8'))
            
        def log_message(self, format, *args):
            pass
            
    return _handler



def watchLive(buildParams: md_compiler.BuildParams):
    
    content = Content()
    content.update(buildParams)

    class SourceFileEventHandler(watchdog.events.FileSystemEventHandler):
        def on_closed(self, event): # When something else finishes writing to a file
            if event.src_path == buildParams.src_file or event.src_path in buildParams.build_files:
                try:
                    md_compiler.compile(buildParams)
                    content.update(buildParams)
                except Exception as e:
                    print(e)
                
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
