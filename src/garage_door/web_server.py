from http.server import BaseHTTPRequestHandler, HTTPServer
from controller import DoorController, State

# Server settings
HOST_NAME = "192.168.0.202"
SERVER_PORT = 8080
WEBHOOK_ADDRESS = "http://192.168.0.6:8089/bay1"

controller = DoorController()


class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

        if self.path == "/state":
            self.wfile.write(bytes(str(controller.state), "utf-8"))

    def do_PUT(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

        if self.path == "/open":
            controller.open()
        if self.path == "/close":
            controller.close()
        if self.path == "/reset":
            controller.set_state_from_sensors()
        if self.path == "/reset/closed":
            controller.state = State.CLOSED
        if self.path == "/reset/open":
            controller.state = State.OPEN


if __name__ == "__main__":
    webServer = HTTPServer((HOST_NAME, SERVER_PORT), WebServer)
    print("Server started http://%s:%s" % (HOST_NAME, SERVER_PORT))
    print(controller.state)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
