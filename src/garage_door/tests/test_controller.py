import pytest as pytest

from garage_door.controller import DoorController, State


def test_setting_state():
    # Manually set the door state externally. Probably should be part of the public API but oh well...
    controller = DoorController()

    controller.set_state(State.OPEN)

    assert controller.state == State.OPEN

    controller.set_state(State.CLOSING)

    assert controller.state == State.CLOSING
    assert controller.lastState == State.OPEN


@pytest.mark.parametrize(
    "sensor, current, last, delta, expected",
    [
        ## Static states

        # 0. Closed
        ((0, 1), State.CLOSED, State.CLOSED, 5.0, State.CLOSED),
        # 1. Open
        ((1, 0), State.OPEN, State.OPEN, 5.0, State.OPEN),
        # 2. Closing
        ((0, 0), State.CLOSING, State.CLOSING, 5.0, State.CLOSING),
        # 3. Opening
        ((0, 0), State.OPENING, State.OPENING, 5.0, State.OPENING),

        ## Regular transition states

        # 4. Closed -> Opening
        ((0, 0), State.CLOSED, State.CLOSING, 5.0, State.OPENING),
        # 5. Open -> Closing
        ((0, 0), State.OPEN, State.OPENING, 5.0, State.CLOSING),
        # 6. Closing -> Closed
        ((0, 1), State.CLOSING, State.OPEN, 5.0, State.CLOSED),
        # 7. Opening -> Open
        ((1, 0), State.OPENING, State.CLOSED, 5.0, State.OPEN),

        ## Unusual transition states

        # 8. Open -> Closed
        ((0, 1), State.OPEN, State.OPENING, 5.0, State.CLOSED),
        # 9. Closed -> Open
        ((1, 0), State.CLOSED, State.CLOSING, 5.0, State.OPEN),

        # Error states
        # If the door has been in closing or opening state for too long,
        # we can assume something has gone wrong. Not sure what to do though...
        # ((0, 0), State.OPEN, State.OPENING, 5.0, State.OPEN),
    ]
)