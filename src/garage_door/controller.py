import json
import time
from enum import Enum
from typing import Optional
from pydantic import BaseModel

import requests

from gpiozero import LED, Button


class State(Enum):
    OPEN = "Open"
    CLOSING = "Closing"
    OPENING = "Opening"
    CLOSED = "Closed"


class StateDefinition(BaseModel):
    sensor: tuple[int, int]  # top, bottom
    previous: Optional[State]


states: dict[State, StateDefinition] = {
    State.OPEN: StateDefinition(
        sensor=(1, 0),
        previous=None
    ),
    State.CLOSED: StateDefinition(
        sensor=(0, 1),
        previous=None
    ),
    State.OPENING: StateDefinition(
        sensor=(0, 0),
        previous=State.CLOSED
    ),
    State.CLOSING: StateDefinition(
        sensor=(0, 0),
        previous=State.OPEN
    ),
}


class GarageDoorController:
    last_state_update: float = time.time()
    last_activation: float = time.time()

    # Fine-tuning
    STATE_UPDATE_DEBOUNCE = 3  # in seconds
    TEMPORARY_STATE_TIMEOUT = (
        20  # in seconds. If a temporary state is older than this, handle it.
    )
    ACTIVATE_DOOR_WHEN_UNKNOWN_STATE = False

    def close_state_update(self):
        print("update state")
        self.update_state(states.CLOSED)

    def open_state_update(self):
        print("update state")
        self.update_state(states.OPEN)

    def __init__(self):
        print("initing")
        self.reset()
        self.current_state = states.UNKNOWN

        # Set up inputs and outputs
        self.door_pin = LED(23)

        open_stop_switch = Button(11)
        closed_stop_switch = Button(8)

        open_stop_switch.when_activated = self.open_state_update
        closed_stop_switch.when_activated = self.close_state_update

    def update_state(self, new_state):
        self.current_state = new_state
        self.last_state_update = time.time()
        requests.post(
            WEBHOOK_ADDRESS,
            data=json.dumps(
                {
                    "characteristic": "CurrentDoorState",
                    "value": self.current_state[1],
                }
            ),
        )

    def request_activate_door(self, desired_state):
        """Receive a request to activate the door. May or may not actually activate the door depending on the
        current state"""
        if time.time() < self.last_state_update + self.STATE_UPDATE_DEBOUNCE:
            print(
                f"State {self.current_state} is {time.time() - self.last_state_update} seconds old, ignoring request"
            )
            return

        if (
            self.current_state is states.UNKNOWN
            and self.ACTIVATE_DOOR_WHEN_UNKNOWN_STATE
        ):
            # if we don't know what the current state is, just activate and hope that we'll figure it out soon?
            print("Unknown state, activating anyway!")
            self.activate_door()
            return

        if desired_state == self.current_state:
            print(f"Door is already {self.current_state}, refusing to activate door")
            return

        if self.current_state in TRANSITION_STATES:
            if time.time() > self.last_state_update + self.TEMPORARY_STATE_TIMEOUT:
                print(
                    f"Transition state {self.current_state} is {time.time() - self.last_state_update} seconds old, handling request since something probalby went wrong!"
                )
                self.activate_door()
                return
            else:
                print(f"State is {self.current_state}, refusing to activate door")
                return

        self.activate_door()

    def activate_door(self):
        print("Activating door!")
        self.last_activation = time.time()
        self.door_pin.on()
        time.sleep(1)
        self.door_pin.off()

        if self.current_state is states.CLOSED:
            self.update_state(states.OPENING)
            time.sleep(3)
            self.open_state_update()  # manually set for now
        if self.current_state is states.OPEN:
            self.update_state(states.CLOSING)
            time.sleep(3)
            self.close_state_update()  # manually set for now

    def reset(self):
        self.last_state_update = 0
        self.last_activation = 0


