import time
import json
import sys
from enum import Enum

import requests
from gpiozero import LED, Button


class State(Enum):
    OPEN = "0"
    CLOSED = "1"
    OPENING = "2"
    CLOSING = "3"
    STOPPED = "4"


class DoorController:
    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state: State) -> None:
        print(f"Set state: {state}", file=sys.stdout)
        # Make call to webhook
        response = requests.post("http://192.168.0.6:8089/bay1", data=json.dumps({
            "characteristic": "CurrentDoorState",
            "value": str(state.value)
        }))
        if not response.status_code == 200:
            print(f"Warning: failed to update webhook with door state {state.name}.")
            print(f"  Status code: {response.status_code}")
            print(f"  Message: {response.text}")

        if state != self.state:
            self._state = state

        # Also update the TargetDoorState. Not really sure why but maybe it will solve the weirdness we have with the stupid homekit state.
        response = requests.post("http://192.168.0.6:8089/bay1", data=json.dumps({
            "characteristic": "TargetDoorState",
            "value": str(state.value)
        }))

    # Physical configuration
    DOOR_PIN = 23  # pin where door relay is connected
    TOP_SENSOR_PIN = 25
    BOTTOM_SENSOR_PIN = 24
    PIN_HOLD_TIME = 1

    def __init__(self) -> None:
        # Pin configuration
        self.door_pin = LED(DoorController.DOOR_PIN)
        self.top_sensor = Button(DoorController.TOP_SENSOR_PIN, hold_time=DoorController.PIN_HOLD_TIME)
        self.bottom_sensor = Button(DoorController.BOTTOM_SENSOR_PIN, hold_time=DoorController.PIN_HOLD_TIME)

        # Set the initial sensor state
        self._state = State.STOPPED

        # Update state from sensor data
        self.set_state_from_sensors()

        # Add handlers to update the state when the sensors change
        self.top_sensor.when_held = self.handle_open
        self.top_sensor.when_deactivated = self.handle_closing
        self.bottom_sensor.when_held = self.handle_closed
        self.bottom_sensor.when_deactivated = self.handle_opening

    def set_state_from_sensors(self):
        # use is_active instead of is_held in case the program just started
        # and we don't have any hold time history
        if self.top_sensor.is_active:
            self.state = State.OPEN
        elif self.bottom_sensor.is_active:
            self.state = State.CLOSED
        else:
            self.state = State.STOPPED
            print(f"Couldn't determine state from sensors, set to {self.state.name}")

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
        print("Pressing button...")
        self.door_pin.on()
        time.sleep(0.5)
        self.door_pin.off()
        time.sleep(0.5)

    def open(self):
        if self.state == State.CLOSING:
            self.press_button()
            self.state = State.OPENING

        if self.state == State.CLOSED:
            self.press_button()  # opening
            # Let sensor changes take care of changing the state to opening
            # self.state = State.OPENING

        print(f"Requested `/open` but door is {self.state.name}")

    def close(self):
        if self.state == State.OPENING:
            self.press_button()
            self.state = State.STOPPED
            time.sleep(1.1)
            self.press_button()
            self.state = State.CLOSING

        if self.state == State.OPEN:
            self.press_button()  # closing
            # Let sensor changes take care of changing the state to opening
            # self.state = State.CLOSING

        print(f"Requested `/close` but door is {self.state.name}")


