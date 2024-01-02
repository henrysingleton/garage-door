from http.server import BaseHTTPRequestHandler, HTTPServer
from controller import DoorController, State

# Server settings
HOST_NAME = "192.168.0.202"
SERVER_PORT = 8080

controller = DoorController()


class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)

        if self.path == "/state":
           self.send_header("Content-type", "text/plain")
           self.end_headers()
           self.wfile.write(bytes(str(controller.current_state.value), "utf-8"))

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
            controller.open()
            # Handle error
        if self.path == "/close":
            controller.close()
            # Handle error
        if self.path == "/button":
            controller.press_button()
        if self.path == "/reset":
            controller.set_state_from_sensors()
        if self.path == "/reset/closed":
            controller.current_state = State.CLOSED
            controller.target_state = State.CLOSED
        if self.path == "/reset/open":
            controller.current_state = State.OPEN
            controller.target_state = State.OPEN

        self.wfile.write(bytes(str(controller.current_state.value), "utf-8"))


if __name__ == "__main__":
    webServer = HTTPServer((HOST_NAME, SERVER_PORT), WebServer)
    print("Server started http://%s:%s" % (HOST_NAME, SERVER_PORT))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
