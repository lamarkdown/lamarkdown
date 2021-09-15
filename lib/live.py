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
        self.title = None
        self.fullHtml = None
        self.updateN = 0
    
    def update(self, targetFile: str):
        with open(targetFile) as f:
            self.fullHtml = f.read()
            
        match = re.search('<title>(.*?)</title>', self.fullHtml, flags = re.IGNORECASE | re.DOTALL)
        self.title = match[1] if match else '[No Title]'
        
        self.updateN += 1
        

def getHandler(content: Content):
    
    class _handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('ContentType', 'text/html')
                self.end_headers()
                message = f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>{content.title}</title>
                        <meta charset="utf-8" />
                        <script>
                            let lastUpdateN = 0;
                        
                            setInterval(
                                () => {{
                                    fetch("/query")
                                        .then(response => response.text())
                                        .then(text =>
                                        {{
                                            let newUpdateN = parseInt(text);
                                            if(lastUpdateN != newUpdateN)
                                            {{
                                                lastUpdateN = newUpdateN;
                                                document.getElementById("frame").contentDocument.location.reload();
                                            }}
                                        }})
                                }},
                                500
                            );
                        </script>
                    </head>
                    <body style="padding: 0; margin: 0;">
                        <iframe id="frame" src="content.html" style="padding: 0; margin: 0; border: 0; position: fixed; width: 100%; height: 100%;"></iframe>
                    </body>
                    </html>
                '''

            elif self.path == '/content.html':
                self.send_response(200)
                self.send_header('ContentType', 'text/html')
                self.end_headers()
                message = content.fullHtml

            elif self.path == '/query':
                self.send_response(200)
                self.send_header('ContentType', 'text/plain')
                self.end_headers()
                message = str(content.updateN)

            else:
                self.send_response(404)
                self.send_header('ContentType', 'text/plain')
                self.end_headers()
                message = 'Yeah nah mate.'

            self.wfile.write(message.encode('utf-8'))
            
        def log_message(self, format, *args):
            pass
            
    return _handler



def watchLive(srcFile: str, targetFile: str, buildFiles: list[str], buildDir: str):
    
    content = Content()
    content.update(targetFile)    

    class SourceFileEventHandler(watchdog.events.FileSystemEventHandler):
        def on_closed(self, event): # When something else finishes writing to a file
            if event.src_path == srcFile or event.src_path in buildFiles:
                try:
                    md_compiler.compile(srcFile=srcFile, targetFile=targetFile, buildFiles=buildFiles, buildDir=buildDir)
                    content.update(targetFile)
                except Exception as e:
                    print(e)
                
    paths = {os.path.dirname(p) for p in [srcFile] + buildFiles if p}
                    
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
                print(f'Monitoring changes to {srcFile}.\nBrowse to http://localhost:{port}\nPress Ctrl-C to quit.')
            
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
