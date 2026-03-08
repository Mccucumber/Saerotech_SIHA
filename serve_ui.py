#!/usr/bin/env python3
import http.server
import socketserver
import os
import json
from datetime import datetime

PORT = 8080

print("Temizlik yapiliyor. Eski simulasyon verileri siliniyor...")
for file in ['boundary.json', 'hss.json', 'telemetri.json']:
    if os.path.exists(file):
        os.remove(file)
print("Temizlik tamamlandi.")

# This server will serve the index4.html file at the root url
class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        # TEKNOFEST 2026 API Rule 4: GET /api/sunucusaati
        if self.path == '/api/sunucusaati':
            now = datetime.now()
            s_time = {
                "gun": now.day,
                "saat": now.hour,
                "dakika": now.minute,
                "saniye": now.second,
                "milisaniye": int(now.microsecond / 1000)
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(s_time).encode('utf-8'))
            return

        # TEKNOFEST 2026 API Rule 11: GET /api/hss_koordinatlari
        elif self.path == '/api/hss_koordinatlari':
            now = datetime.now()
            s_time = {
                "gun": now.day,
                "saat": now.hour,
                "dakika": now.minute,
                "saniye": now.second,
                "milisaniye": int(now.microsecond / 1000)
            }
            
            hss_list = []
            if os.path.exists('hss.json'):
                try:
                    with open('hss.json', 'r') as f:
                        hss_list = json.load(f)
                except:
                    pass
            
            resp_data = {
                "sunucusaati": s_time,
                "hss_koordinat_bilgileri": hss_list
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(resp_data).encode('utf-8'))
            return

        # Allow default route to go to index.html, but keep other requests intact
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/index4':
            self.path = '/index4.html'
            
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b""

        if self.path == '/api/boundary':
            try:
                data = json.loads(post_data.decode('utf-8'))
                # Sınırları boundary.json dosyasına yaz
                with open('boundary.json', 'w') as f:
                    json.dump(data, f)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        
        elif self.path == '/api/hss':
            try:
                data = json.loads(post_data.decode('utf-8'))
                # HSS verilerini (liste halindeki circle objelerini) dosyasına yaz
                with open('hss.json', 'w') as f:
                    json.dump(data, f)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

        # TEKNOFEST 2026 API Rule 4: POST /api/telemetri_gonder
        elif self.path == '/api/telemetri_gonder':
            try:
                # Gerçekte sunucu burada takımdan gelen veriyi alır ve veritabanına yazar.
                # Sonrasında diğer takımların güncel konumlarını (telemetri.json) döndürür.
                if os.path.exists('telemetri.json'):
                    with open('telemetri.json', 'r') as f:
                        resp_data = json.load(f)
                else:
                    resp_data = {"sunucusaati": {}, "konumBilgileri": []}

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(resp_data).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                
        # TEKNOFEST 2026 API Rule 4 & 5: POST /api/giris
        elif self.path == '/api/giris':
            try:
                # Login mock (Herhangi bir şifreyi takım 1 olarak kabul et)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                # Kural 5: "Girişin başarılı olması durumda 200 OK durum kodu ile birlikte içerik olarak takım numarası alınır."
                self.wfile.write(b"1")
            except Exception as e:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
