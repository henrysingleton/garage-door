import time
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class State(Enum):
    OPEN = "Open"
    CLOSING = "Closing"
    OPENING = "Opening"
    CLOSED = "Closed"


SensorData = tuple[int, int]


class StateDefinition(BaseModel):
    """Pydantic method describing a door state"""
    sensor: SensorData  # top, bottom
    last: Optional[State]


# Define some door states, not sure if these would actually get used
states: dict[State, StateDefinition] = {
    State.OPEN: StateDefinition(
        sensor=(1, 0),
        last=None
    ),
    State.CLOSED: StateDefinition(
        sensor=(0, 1),
        last=None
    ),
    State.OPENING: StateDefinition(
        sensor=(0, 0),
        last=State.CLOSED
    ),
    State.CLOSING: StateDefinition(
        sensor=(0, 0),
        last=State.OPEN
    ),
}


class DoorController:
    state: State = State.CLOSED
    lastState: State = State.CLOSED
    lastUpdateTime: float = time.time()

    @staticmethod
    def resolve_state(
        sensor: SensorData,
        current: State,
        last: State,
        delta: float
    ) -> State:
        """Resolves the current state from the passed information"""
        state_by_sensor_data = [state for state, definition in states.items() if definition.sensor == sensor]

        # If we got a direct match on OPEN or CLOSED, just return it, we are very confident about the state.
        if len(state_by_sensor_data) == 1:
            return state_by_sensor_data[0]

        # If the state was opening or closing and current is the same as last, just assume its still in the same state. Could put a little timeout here.
        if last == current:
            return current

        # If its a new state, decide if its opening or closing based on the last known state.
        possible_states_from_last_known_state = [state for state, definition in states.items() if state in state_by_sensor_data and definition.last == current]

        if len(possible_states_from_last_known_state) == 1:
            return possible_states_from_last_known_state[0]

        raise RuntimeError("Could not resolve state :(")

    def set_the_state(self, state: State) -> None:
        self.lastState = self.state
        self.state = state
        self.lastUpdateTime = time.time()

    def get_the_state(self) -> State:
        return self.state

    def open(self) -> State:
        # check existing state
        #   check last update time if something happened recently

        # check sensor states - can we ask
        pass

    def update_state(self) -> State:
        """Given the following:
        - Sensor 1
        - Sensor 2
        - Current state
        - Last state
        - Last state update time

        Resolve the new state, set it, and return it"""

        new_state = self.resolve_state(
            self.get_sensor_data(),
            self.state,
            self.lastState,
            time.time() - self.lastUpdateTime
        )

        self.set_the_state(new_state)

        return new_state

    def get_sensor_data(self):
        # TODO: implementation for getting sensor states
        return 1, 1

# class GarageDoorController:
#     last_state_update: float = time.time()
#     last_activation: float = time.time()

#     # Fine-tuning
#     STATE_UPDATE_DEBOUNCE = 3  # in seconds
#     TEMPORARY_STATE_TIMEOUT = (
#         20  # in seconds. If a temporary state is older than this, handle it.
#     )
#     ACTIVATE_DOOR_WHEN_UNKNOWN_STATE = False

#     def close_state_update(self):
#         print("update state")
#         self.update_state(states.CLOSED)

#     def open_state_update(self):
#         print("update state")
#         self.update_state(states.OPEN)

#     def __init__(self):
#         print("initing")
#         self.reset()
#         self.current_state = states.UNKNOWN

#         # Set up inputs and outputs
#         self.door_pin = LED(23)

#         open_stop_switch = Button(11)
#         closed_stop_switch = Button(8)

#         open_stop_switch.when_activated = self.open_state_update
#         closed_stop_switch.when_activated = self.close_state_update

#     def update_state(self, new_state):
#         self.current_state = new_state
#         self.last_state_update = time.time()
#         requests.post(
#             WEBHOOK_ADDRESS,
#             data=json.dumps(
#                 {
#                     "characteristic": "CurrentDoorState",
#                     "value": self.current_state[1],
#                 }
#             ),
#         )

#     def request_activate_door(self, desired_state):
#         """Receive a request to activate the door. May or may not actually activate the door depending on the
#         current state"""
#         if time.time() < self.last_state_update + self.STATE_UPDATE_DEBOUNCE:
#             print(
#                 f"State {self.current_state} is {time.time() - self.last_state_update} seconds old, ignoring request"
#             )
#             return

#         if (
#             self.current_state is states.UNKNOWN
#             and self.ACTIVATE_DOOR_WHEN_UNKNOWN_STATE
#         ):
#             # if we don't know what the current state is, just activate and hope that we'll figure it out soon?
#             print("Unknown state, activating anyway!")
#             self.activate_door()
#             return

#         if desired_state == self.current_state:
#             print(f"Door is already {self.current_state}, refusing to activate door")
#             return

#         if self.current_state in TRANSITION_STATES:
#             if time.time() > self.last_state_update + self.TEMPORARY_STATE_TIMEOUT:
#                 print(
#                     f"Transition state {self.current_state} is {time.time() - self.last_state_update} seconds old, handling request since something probalby went wrong!"
#                 )
#                 self.activate_door()
#                 return
#             else:
#                 print(f"State is {self.current_state}, refusing to activate door")
#                 return

#         self.activate_door()

#     def activate_door(self):
#         print("Activating door!")
#         self.last_activation = time.time()
#         self.door_pin.on()
#         time.sleep(1)
#         self.door_pin.off()

#         if self.current_state is states.CLOSED:
#             self.update_state(states.OPENING)
#             time.sleep(3)
#             self.open_state_update()  # manually set for now
#         if self.current_state is states.OPEN:
#             self.update_state(states.CLOSING)
#             time.sleep(3)
#             self.close_state_update()  # manually set for now

#     def reset(self):
#         self.last_state_update = 0
#         self.last_activation = 0


