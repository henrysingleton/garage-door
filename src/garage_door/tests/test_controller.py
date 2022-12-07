from garage_door.controller import DoorController, State

def test_setting_state():
    controller = DoorController()

    controller.set_the_state(State.OPEN)

    # assert controller.state == State.OPEN

    controller.set_the_state(State.CLOSING)

    #assert controller.state == State.CLOSING
    # assert controller.lastState == State.OPEN
