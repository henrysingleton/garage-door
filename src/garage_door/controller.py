import time
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel
from gpiozero import LED, Button

class State(Enum):
    OPEN = "Open"
    CLOSING = "Closing"
    OPENING = "Opening"
    CLOSED = "Closed"
    STOPPED = "Stopped"


SensorData = tuple[int, int]


class StateResolutionError(RuntimeError):
    pass


class StateUpdateDebounceException(StateResolutionError):
    pass


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
    STATE_DEBOUNCE: float = 0.3  # seconds
    DOOR_PIN = 23  # pin where door is connected
    TOP_SENSOR_PIN = 24
    BOTTOM_SENSOR_PIN = 25

    def __init__(self) -> None:
        self.state: State = State.CLOSED
        self.lastState: State = State.CLOSED
        self.lastUpdateTime: float = time.time()

        self.door_pin = LED(DoorController.DOOR_PIN)
        self.top_sensor = Button(DoorController.TOP_SENSOR_PIN, hold_time=2)
        self.bottom_sensor = Button(DoorController.BOTTOM_SENSOR_PIN, hold_time=2)

        self.top_sensor.when_held = self.update_state
        self.top_sensor.when_deactivated = self.update_state
        self.bottom_sensor.when_held = self.update_state
        self.bottom_sensor.when_deactivated = self.update_state

    @staticmethod
    def resolve_state(
        sensor: SensorData,
        current: State,
        last: State,
        delta: float
    ) -> State:
        """Resolves the current state from the passed information"""
        print(
            f"\n Resolving state with: \n"
            f" sensor: {sensor}\n"
            f" current: {current.value}\n"
            f" last: {last.value}\n"
            f" delta: {delta}"
        )

        if delta < DoorController.STATE_DEBOUNCE:
            print(f"Refusing to update, last state change was "
                  f"{delta} seconds ago")
            raise StateUpdateDebounceException(delta)

        state_by_sensor_data = [state for state, definition in states.items() if definition.sensor == sensor]

        # If we got a direct match on OPEN or CLOSED, just return it, we are very confident about the state.
        if len(state_by_sensor_data) == 1:
            print(
                f"resolved to {state_by_sensor_data[0].value} via "
                f"direct sensor state match"
            )
            return state_by_sensor_data[0]


        # If its a new state, decide if its opening or closing based on the last known state.
        possible_states_from_last_known_state = [state for state, definition in states.items() if state in state_by_sensor_data and definition.last == current]

        if len(possible_states_from_last_known_state) == 1:
            print(
                f"resolved to {possible_states_from_last_known_state[0].value}"
                f" as we have transitioned from {current}"
            )
            return possible_states_from_last_known_state[0]

        # If the state was opening or closing and current is the same as last, just assume its still in the same state. Could put a little timeout here.
        if last == current and states[current].last is not None:
            print(
                f"resolved to {current} as it's the same as the last opening "
                f"or closing state ",
            )
            return current

        raise StateResolutionError(
            "Could not resolve state, no matches from state definition"
        )

    def set_state(self, state: State) -> None:
        self.lastState = self.state
        self.state = state
        self.lastUpdateTime = time.time()

    def get_state(self) -> State:
        return self.state

    def open(self) -> State:
        self.update_state()
        print(f"Doing opening...")
        if self.state == State.OPEN:
            print(f"Not doing anything, door already open...")
            return self.state

        if self.state == State.OPENING:
            print(f"Not doing anything, door already opening")
            return self.state

        if self.state == State.STOPPED:
            # Not sure if we'll ever know its stopped
            if self.lastState == State.OPENING:
                self.press_button()  # closing
                self.press_button()  # stopped
                self.press_button()  # opening
                return State.OPENING

            if self.lastState == State.CLOSING:
                self.press_button()  # stopped
                self.press_button()  # opening
                return State.OPENING

            raise RuntimeError(
                "Not sure what to do from unknown state when opening")

        if self.state == State.CLOSING:
            self.press_button()  # stopped
            self.press_button()  # opening
            return State.OPENING

        if self.state == State.CLOSED:
            self.press_button()  # opening
            return State.OPENING

    def close(self) -> State:
        self.update_state()
        if self.state == State.CLOSED:
            print(f"Not doing anything, door already closed...")
            return self.state

        if self.state == State.CLOSING:
            print(f"Not doing anything, door already closing")
            return self.state

        if self.state == State.STOPPED:
            # Not sure if we'll ever know its stopped
            if self.lastState == State.CLOSING:
                self.press_button()  # opening
                self.press_button()  # stopped
                self.press_button()  # closing
                return State.CLOSING

            if self.lastState == State.OPENING:
                self.press_button()  # stopped
                self.press_button()  # closing
                return State.CLOSING

            raise RuntimeError("Not sure what to do from unknown state when closing")

        if self.state == State.OPENING:
            self.press_button()  # stopped
            self.press_button()  # closing
            return State.CLOSING

        if self.state == State.OPEN:
            self.press_button()  # closing
            return State.CLOSING

    def press_button(self):
        self.door_pin.on()
        time.sleep(0.5)
        self.door_pin.off()
        time.sleep(0.5)

    def update_state(self, sensor: Optional[Any] = None) -> State:
        """Given the following:
        - Sensor 1 & 2
        - Current state
        - Last state
        - Last state update time

        Resolve the new state, set it, and return it"""

        if sensor:
            print(f"Updating state from sensor {sensor} change")

        print(f"Updating state. Resolving first...")

        new_state = self.resolve_state(
            self.get_sensor_data(),
            self.state,
            self.lastState,
            time.time() - self.lastUpdateTime
        )

        print(f"Checking time diff")

        if new_state != self.lastState:
            print(f"Saving state")
            self.set_state(new_state)
            # TODO: make request to homebridge to let them know the state
            #  changed.
        print(f"Returning")

        return new_state

    def get_sensor_data(self):
        return self.top_sensor.value, self.bottom_sensor.value