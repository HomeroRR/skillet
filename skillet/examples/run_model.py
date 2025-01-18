"""Example script to run a PyTorch MLP model at 50Hz while interacting with actuators.

Make sure you have configured and zeroed the joints before running this script.
"""

import logging
import time

import colorlogging
import pykos  # type: ignore[import-untyped]
import torch
import torch.nn as nn
import numpy as np

from typing import List
from skillet.setup.maps import ACTUATOR_NAME_TO_ID
from skillet.examples.move_joint_a_little import configure_joint, get_joint_state, move_joint


JOINT_NAMES = ["left_hip_roll", "right_hip_roll"]
UPDATE_FREQUENCY = 50  # Hz
LOOP_PERIOD = 1.0 / UPDATE_FREQUENCY


class MLPModel(nn.Module):
    """An example MLP model for demonstration."""
    def __init__(self, input_size: int = 1, hidden_size: int = 64, output_size: int = 2):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size),
            nn.Tanh()  # Limit output to [-1, 1] range
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)



def run_model_loop(joint_names: List[str]) -> None:
    """Run the MLP model in a loop at 50Hz to control joint movements.

    Args:
        joint_names (list[str]): Names of the joints to control.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    colorlogging.configure()

    # Initialize PyTorch model (input size = number of joints)
    model = MLPModel(input_size=len(joint_names), output_size=len(joint_names))
    model.eval()  # Set to evaluation mode

    # Instantiate the KOS client
    kos = pykos.KOS(ip="192.168.42.1")

    # Configure and log initial state for all joints
    actuator_ids = [ACTUATOR_NAME_TO_ID[name] for name in joint_names]
    for joint_name in joint_names:
        configure_joint(kos, joint_name)
        get_joint_state(kos, joint_name)

    try:
        while True:
            loop_start_time = time.time()
            
            # Get current joint states
            states = kos.actuator.get_actuators_state(actuator_ids)
            current_positions = [state.position for state in states.states]

            # Prepare input for model
            model_input = torch.tensor([current_positions], dtype=torch.float32)
            
            # Run model inference
            with torch.inference_mode():
                model_outputs = model(model_input).squeeze()
            
            # Scale model outputs and move joints
            for i, (joint_name, current_pos, model_output) in enumerate(
                zip(joint_names, current_positions, model_outputs)
            ):
                # Scale model output to reasonable joint movement range (-20 to 20 degrees)
                target_position = current_pos + (model_output.item() * 20.0)
                # Move joint
                move_joint(kos, joint_name, target_position)
            
            # Calculate sleep time to maintain 50Hz
            elapsed_time = time.time() - loop_start_time
            sleep_time = max(0, LOOP_PERIOD - elapsed_time)
            time.sleep(sleep_time)
            
            # Log actual loop frequency
            actual_freq = 1.0 / (time.time() - loop_start_time)
            logging.debug(f"Loop frequency: {actual_freq:.2f} Hz")

    except KeyboardInterrupt:
        logging.info("Stopping model loop")



def run_model_loop2(joint_name: str) -> None:
    """Run the MLP model in a loop at 50Hz to control joint movement.

    Args:
        joint_name (str): Name of the joint to control.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    colorlogging.configure()

    # Initialize PyTorch model
    model = MLPModel()
    model.eval()  # Set to evaluation mode

    # Instantiate the KOS client
    kos = pykos.KOS(ip="192.168.42.1")

    # Configure and log initial state
    configure_joint(kos, joint_name)
    get_joint_state(kos, joint_name)

    try:
        while True:
            loop_start_time = time.time()
            
            # Get current joint state
            actuator_id = ACTUATOR_NAME_TO_ID[joint_name]
            state = kos.actuator.get_actuators_state([actuator_id])
            current_position = state.states[0].position

            # Prepare input for model
            model_input = torch.tensor([[current_position]], dtype=torch.float32)
            
            # Run model inference
            with torch.inference_mode():
                model_output = model(model_input).item()
            
            # Scale model output to reasonable joint movement range (-20 to 20 degrees)
            target_position = current_position + (model_output * 20.0)
            
            # Move joint
            move_joint(kos, joint_name, target_position)
            
            # Calculate sleep time to maintain 50Hz
            elapsed_time = time.time() - loop_start_time
            sleep_time = max(0, LOOP_PERIOD - elapsed_time)
            time.sleep(sleep_time)
            
            # Log actual loop frequency
            actual_freq = 1.0 / (time.time() - loop_start_time)
            logging.debug(f"Loop frequency: {actual_freq:.2f} Hz")

    except KeyboardInterrupt:
        logging.info("Stopping model loop")


if __name__ == "__main__":
    run_model_loop(JOINT_NAMES)
