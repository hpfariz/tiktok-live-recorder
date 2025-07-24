from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler
from subprocess import Popen
import os, pathlib

def run_recorder():
    # Run src/main.py no matter where server.py is located
    root = pathlib.Path(__file__).parent
    Popen(['python', str(root / 'src' / 'main.py'),
           '-user', 'jcayne_', '-mode', 'automatic'])

if __name__ == '__main__':
    Thread(target=run_recorder, daemon=True).start()
    HTTPServer(('', int(os.getenv('PORT', 10000))),
               SimpleHTTPRequestHandler).serve_forever()
