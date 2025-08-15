#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys
from http import HTTPStatus

class NoDirListingHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def list_directory(self, path):
        self.send_error(HTTPStatus.FORBIDDEN, "Directory listing not allowed")
        return None

def run_server(port=80, bind=''):
    handler = NoDirListingHTTPRequestHandler
    
    class ReuseAddrTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
        
    with ReuseAddrTCPServer((bind, port), handler) as httpd:
        print(f"Server running on port {port}...")
        print(f"Serving files from: {os.getcwd()}")
        print("Directory listing disabled - files can only be accessed directly")
        httpd.serve_forever()

if __name__ == "__main__":
    port = 80
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
    
    try:
        run_server(port)
    except PermissionError:
        print(f"Permission denied: Cannot bind to port {port}. Try running with sudo.")
        sys.exit(1)
    except OSError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)