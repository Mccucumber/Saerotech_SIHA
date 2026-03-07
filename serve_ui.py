#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8080

# This server will serve the index4.html file at the root url
class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        # Allow default route to go to index.html, but keep other requests intact
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/index4':
            self.path = '/index4.html'
            
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
