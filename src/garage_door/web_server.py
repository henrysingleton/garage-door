from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer

# Server settings
HOST_NAME = "192.168.0.166"
SERVER_PORT = 8080
WEBHOOK_ADDRESS = "http://192.168.0.25:8089/bay1"


@dataclass(frozen=True)
class StatesNamespace:
    UNKNOWN = (
        "Unknown",
        "unknown",
    )
    OPEN = (
        "Open",
        "0",
    )
    CLOSED = (
        "Closed",
        "1",
    )
    OPENING = (
        "Opening",
        "2",
    )
    CLOSING = (
        "Closing",
        "3",
    )
    STOPPED = (
        "Stopped",
        "4",
    )


states = StatesNamespace()

TRANSITION_STATES = (states.OPENING, states.CLOSING)


class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

        if self.path == "/state":
            print(f"Sending state {controller.current_state[0]}")
            self.wfile.write(bytes(controller.current_state[1], "utf-8"))

        if self.path == "/reset/closed":
            # controller.reset()
            controller.update_state(states.CLOSED)
        if self.path == "/reset/open":
            # controller.reset()
            controller.update_state(states.OPEN)

    def do_PUT(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

        print(
            f"Current state: {controller.current_state[0]}, last updated {controller.last_state_update}"
        )

        if self.path == "/open":
            controller.request_activate_door(states.OPEN)
        if self.path == "/close":
            controller.request_activate_door(states.CLOSED)


if __name__ == "__main__":
    webServer = HTTPServer((HOST_NAME, SERVER_PORT), WebServer)
    print("Server started http://%s:%s" % (HOST_NAME, SERVER_PORT))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
