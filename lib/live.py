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


PORT = 8000

class Content:
    def __init__(self):
        self.title = None
        self.fullHtml = None
        self.updated = False
    
    def update(self, targetFile: str):
        with open(targetFile) as f:
            self.fullHtml = f.read()
            
        match = re.search('<title>(.*?)</title>', self.fullHtml, flags = re.IGNORECASE | re.DOTALL)
        self.title = match[1] if match else '[No Title]'
        
        self.updated = True
        

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
                        <script>
                            setInterval(
                                () => {{
                                    fetch("/query")
                                        .then(response => response.text())
                                        .then(text =>
                                        {{
                                            console.log(text);
                                            if(text == '1')
                                            {{
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
                content.updated = False

            elif self.path == '/query':
                self.send_response(200)
                self.send_header('ContentType', 'text/plain')
                self.end_headers()
                message = '1' if content.updated else '0'

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
    print(f'Monitoring changes to {srcFile}.\nBrowse to http://localhost:{PORT}\nPress Ctrl-C to quit.')
    
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
        def openBrowser():
            time.sleep(0.5)
            webbrowser.open(f'http://localhost:{PORT}')
            mainThread.join()
        
        server = http.server.HTTPServer(('', PORT), getHandler(content))
        threading.Thread(target=openBrowser).start()
        server.serve_forever()
        
            
    except KeyboardInterrupt: # Ctrl-C
        pass
    
    finally:
        observer.stop()
        observer.join()
