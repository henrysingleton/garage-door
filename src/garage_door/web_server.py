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
            state = controller.get_state()
            print(f"Sending state {state.value}")
            self.wfile.write(bytes(str(state.value), "utf-8"))

        if self.path == "/reset/closed":
            controller.set_state(State.CLOSED)
        if self.path == "/reset/open":
            controller.set_state(State.OPEN)

    def do_PUT(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

        state = controller.get_state()

        print(
            f"Current state: {state.value}, last updated {controller.lastUpdateTime}"
        )

        print(self.path)

        if self.path == "/open":
            controller.open()
        if self.path == "/close":
            controller.close()


if __name__ == "__main__":
    webServer = HTTPServer((HOST_NAME, SERVER_PORT), WebServer)
    print("Server started http://%s:%s" % (HOST_NAME, SERVER_PORT))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
