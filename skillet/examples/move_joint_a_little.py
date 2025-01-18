"""Example script to interact with actuators.

Make sure you have configured and zeroed the joints before running this script.
"""

# Standard library imports
import logging
import time

# Third-party imports
import colorlogging
import pykos  # type: ignore[import-untyped]

# Local imports
from skillet.setup.maps import ACTUATOR_NAME_TO_ID

# Constants
JOINT_NAME = "right_hip_roll"
MOVE_DEGREES = -10.0  # Could be 10 or -20 or whatever you want


def configure_joint(kos: pykos.KOS, joint_name: str) -> None:
    """Configure a specific actuator with preset PID gains.

    Args:
        kos (pykos.KOS): Instance of the KOS object to communicate with actuators.
        joint_name (str): Name of the joint to configure.
    """
    actuator_id = ACTUATOR_NAME_TO_ID[joint_name]
    logging.info("Configuring %s (ID: %d)", joint_name, actuator_id)

    result = kos.actuator.configure_actuator(
        actuator_id=actuator_id,
        kp=32.0,  # Proportional gain
        kd=32.0,  # Derivative gain
        torque_enabled=True,
        zero_position=True
    )
    logging.info("Configuration result: %s", result)


def get_joint_state(kos: pykos.KOS, joint_name: str) -> None:
    """Get and log the state of a specific actuator.

    Args:
        kos (pykos.KOS): Instance of the KOS object to communicate with actuators.
        joint_name (str): Name of the joint whose state should be retrieved.
    """
    actuator_id = ACTUATOR_NAME_TO_ID[joint_name]
    state = kos.actuator.get_actuators_state([actuator_id])
    logging.info("%s state: %s", joint_name, state)


def move_joint(kos: pykos.KOS, joint_name: str, position: float) -> None:
    """Move a joint to a given position.

    Args:
        kos (pykos.KOS): Instance of the KOS object to communicate with actuators.
        joint_name (str): Name of the joint to move.
        position (float): Target position to move the joint to.
    """
    logging.info("Moving %s to position %f", joint_name, position)
    command = {"actuator_id": ACTUATOR_NAME_TO_ID[joint_name], "position": position}

    result = kos.actuator.command_actuators([command])
    logging.info("Movement result: %s", result)

def move_joint_a_little(joint_name: str, move_degrees: float) -> None:
    """Move a joint by a specified number of degrees from its current position.

    Args:
        joint_name (str): Name of the joint to move.
        move_degrees (float): Number of degrees to move (positive or negative).
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    colorlogging.configure()

    # Instantiate the KOS client
    kos = pykos.KOS(ip="192.168.42.1")

    # Configure and log initial state
    configure_joint(kos, joint_name)
    get_joint_state(kos, joint_name)

    # Read current position
    actuator_id = ACTUATOR_NAME_TO_ID[joint_name]
    state = kos.actuator.get_actuators_state([actuator_id])
    current_position = state[0].position

    # Determine target position
    target_position = current_position - move_degrees
    # Move joint and log new state
    move_joint(kos, joint_name, target_position)
    time.sleep(0.1)  # Wait a moment to ensure movement completes
    get_joint_state(kos, joint_name)


def main() -> None:
    """Main function to move a joint by a small amount."""
    move_joint_a_little(JOINT_NAME, MOVE_DEGREES)


if __name__ == "__main__":
    main()
