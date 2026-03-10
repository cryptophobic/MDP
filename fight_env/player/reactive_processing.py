"""
1. End of STUNNED
2. Enter STUNNED
3. Enter HURT
4. Exit HURT
4. Enter DEAD
"""
from fight_env.protocols.state_protocol import StateProtocol


def react_on(currentState: StateProtocol, lastSnapshot: StateProtocol) -> None:
    if currentState.hp <= 0:

    pass