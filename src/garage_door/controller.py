import time
from enum import Enum
from gpiozero import LED, Button


class State(Enum):
    OPEN = "Open"
    CLOSING = "Closing"
    OPENING = "Opening"
    CLOSED = "Closed"
    STOPPED = "Stopped"


class DoorController:
    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state: State) -> None:
        print(f"Set state: {state}")
        if state != self.state:
            self._state = state

    # Physical configuration
    DOOR_PIN = 23  # pin where door relay is connected
    TOP_SENSOR_PIN = 25
    BOTTOM_SENSOR_PIN = 24

    def __init__(self) -> None:
        self.door_pin = LED(DoorController.DOOR_PIN)
        self.top_sensor = Button(DoorController.TOP_SENSOR_PIN, hold_time=2)
        self.bottom_sensor = Button(DoorController.BOTTOM_SENSOR_PIN, hold_time=2)

        # Set the initial sensor state
        self.set_state_from_sensors()

        # Add handlers to update the state when the sensors change
        self.top_sensor.when_held = self.handle_open
        self.top_sensor.when_deactivated = self.handle_closing
        self.bottom_sensor.when_held = self.handle_closed
        self.bottom_sensor.when_deactivated = self.handle_opening

    def set_state_from_sensors(self):
        # Set the current state
        if self.top_sensor.is_held:
            self.state = State.OPEN
        elif self.bottom_sensor.is_held:
            self.state = State.CLOSED

    # Handle sensor transitions
    def handle_open(self):
        self.state = State.OPEN

    def handle_closing(self):
        self.state = State.CLOSING

    def handle_closed(self):
        self.state = State.CLOSED

    def handle_opening(self):
        self.state = State.OPENING

    # Handle open/close requests
    def press_button(self):
        self.door_pin.on()
        time.sleep(0.5)
        self.door_pin.off()
        time.sleep(0.5)

    def open(self):
        if self.state == State.OPEN:
            print(f"Not doing anything, door already open")

        if self.state == State.OPENING:
            print(f"Not doing anything, door already opening")

        if self.state == State.CLOSING:
            self.press_button()
            self.state = State.STOPPED
            self.press_button()
            self.state = State.OPENING

        if self.state == State.CLOSED:
            self.press_button()  # opening
            # Let sensor changes take care of changing the state to opening
            # self.state = State.OPENING

    def close(self):
        if self.state == State.CLOSED or self.state == State.CLOSING:
            print(f"Not doing anything, door is {self.state}")

        if self.state == State.OPENING:
            self.press_button()
            self.state = State.STOPPED
            self.press_button()
            self.state = State.CLOSING

        if self.state == State.OPEN:
            self.press_button()  # closing
            # Let sensor changes take care of changing the state to opening
            # self.state = State.CLOSING


