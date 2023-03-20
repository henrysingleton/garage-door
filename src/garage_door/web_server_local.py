from http.server import BaseHTTPRequestHandler, HTTPServer

# Server settings
HOST_NAME = "127.0.0.1"
SERVER_PORT = 8080


class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)

        if self.path == "/state":
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes("0", encoding="utf-8"))

        if self.path == "/":
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open(r'static/index.html', 'r') as f:
                self.wfile.write(bytes(f.read(), encoding='utf8'))

    def do_PUT(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

        if self.path == "/open":
            self.wfile.write(bytes("done open", encoding="utf-8"))
        if self.path == "/close":
            self.wfile.write(bytes("done close", encoding="utf-8"))


if __name__ == "__main__":
    webServer = HTTPServer((HOST_NAME, SERVER_PORT), WebServer)
    print("Server started http://%s:%s" % (HOST_NAME, SERVER_PORT))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
