import time
import json
import sys
from enum import Enum

import requests
from gpiozero import LED, Button

# These match the possible Homekit garage door states.
# See https://developer.apple.com/documentation/homekit/hmcharacteristicvaluedoorstate
class State(Enum):
    OPEN = "0"
    CLOSED = "1"
    OPENING = "2"
    CLOSING = "3"
    STOPPED = "4"

WEBHOOK_URL = "http://192.168.0.6:8089/bay1"

# Physical configuration
DOOR_PIN = 23  # pin where door relay is connected
TOP_SENSOR_PIN = 25
BOTTOM_SENSOR_PIN = 24

PIN_HOLD_TIME = 2

class DoorController:

    DEBUG = False

    @property
    def current_state(self):
        return self._current_state

    @property
    def target_state(self):
        return self._target_state

    @current_state.setter
    def current_state(self, state: State) -> None:
        # Update internal state
        self._current_state = state

        # Update state in Homebridge plugin by calling webhook
        print(f"Setting CurrentDoorState to {state}", file=sys.stdout)
        response = requests.post(
            WEBHOOK_URL,
            data=json.dumps({
                "characteristic": "CurrentDoorState",
                "value": str(state.value)
            })
        )

        if not response.status_code == 200:
            print(f"Warning: failed to send CurrentDoorState={state.name} to webhook {WEBHOOK_URL}.")
            print(f"  Status code: {response.status_code}")
            print(f"  Message: {response.text}")

    @target_state.setter
    def target_state(self, state: State) -> None:
        # Update internal state
        self._target_state = state

        # Update state in Homebridge plugin by calling webhook
        print(f"Setting TargetDoorState to {state}", file=sys.stdout)
        response = requests.post(
            WEBHOOK_URL,
            data=json.dumps({
                "characteristic": "TargetDoorState",
                "value": str(state.value)
            })
        )

        if not response.status_code == 200:
            print(
                f"Warning: failed to send TargetDoorState={state.name} to webhook {WEBHOOK_URL}.")
            print(f"  Status code: {response.status_code}")
            print(f"  Message: {response.text}")


    def __init__(self) -> None:
        # Set the initial sensor state. This is just a guess and to set up
        # our object with some sane defaults. It bypasses the homebridge
        # webhooks so it may be out of sync for a second, but we immediately
        # update the state based on the sensor next.
        self._current_state = State.STOPPED
        self._target_state = State.CLOSED

        if self.DEBUG:
            return

        # Pin configuration
        self.door_pin = LED(DOOR_PIN)
        self.top_sensor = Button(
            TOP_SENSOR_PIN,
            hold_time=PIN_HOLD_TIME
        )
        self.bottom_sensor = Button(
            BOTTOM_SENSOR_PIN,
            hold_time=PIN_HOLD_TIME
        )

        # Update state from the real sensor data
        self.set_state_from_sensors()

        # Add handlers to update the state when the sensors change
        self.top_sensor.when_held = self.handle_open
        self.top_sensor.when_deactivated = self.handle_closing
        self.bottom_sensor.when_held = self.handle_closed
        self.bottom_sensor.when_deactivated = self.handle_opening

    def set_state_from_sensors(self):
        # use is_active instead of is_held in case the program just started,
        # and we don't have any hold time history
        if self.top_sensor.is_active:
            self._current_state = State.OPEN
            self._target_state = State.OPEN
        elif self.bottom_sensor.is_active:
            self._current_state = State.CLOSED
            self._target_state = State.CLOSED
        else:
            self._current_state = State.STOPPED
            print(f"Couldn't determine state from sensors, set to {State.STOPPED}")

    # Handle sensor transitions
    def handle_open(self):
        self.target_state = State.OPEN
        self.current_state = State.OPEN

    def handle_closing(self):
        self.current_state = State.CLOSING

    def handle_closed(self):
        self.target_state = State.CLOSED
        self.current_state = State.CLOSED

    def handle_opening(self):
        self.target_state = State.OPEN # Remove?
        self.current_state = State.OPENING

    # Handle open/close requests
    def press_button(self):
        print("Pressing button...")
        self.door_pin.on()
        time.sleep(0.5)
        self.door_pin.off()
        time.sleep(0.5)

    def open(self):
        print(f"Requested `/open`. Door is {self.current_state.name}")

        if self.current_state == State.CLOSING:
            self.press_button()
            # We have to set the state to opening since a sensor-change won't
            # be detected, as the door was never at an extent.
            self.current_state = State.OPENING

        if self.current_state == State.CLOSED:
            self.press_button()



    def close(self):
        print(f"Requested `/close`. Door is {self.current_state.name}")

        if self.current_state == State.OPENING:
            self.press_button()
            self.current_state = State.STOPPED
            time.sleep(1.1)
            self.press_button()
            self.current_state = State.CLOSING

        if self.current_state == State.OPEN:
            self.press_button()



