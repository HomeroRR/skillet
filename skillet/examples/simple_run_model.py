#!/usr/bin/env python3
"""Generalized example script to run a model on any subset of joints via pykos.

Usage (example controlling 10 lower-body joints):
  python simple_run_model.py

By default, the script:
1. Connects to a KOS-based robot (pykos) (unless --dry-run is set).
2. Configures actuators for the specified joints (KP/KD) unless you pass --skip-config.
3. Reads sensor data: N joint positions, N velocities, plus 6 IMU values.
4. Keeps track of previous model outputs (actions).
5. Runs inference (either a dummy random model or a simple placeholder).
6. Sends the resulting position commands (N joints) back to the robot.
7. Disables torque when done or if interrupted.

Important notes:
- The 6 IMU values are [acc_x, acc_y, acc_z, grav_x, grav_y, grav_z] by default.
- If you integrate a real ML model, replace `MyModel.infer` with your actual code.
- The total input dimension to the model = 3*N (positions, velocities, prev_actions) + 6 (IMU) = 3N + 6.
- The model output dimension is expected to be N (one action per joint).
"""

import argparse
import logging
import time

import numpy as np
import pykos  # type: ignore[import-untyped]

from skillet.setup.maps import ACTUATOR_NAME_TO_ID


# DEFAULT JOINTS & MODEL CLASSES

# Needs to be a list cause order matters
JOINTS_TO_MOVE = [
    "left_hip_yaw",
    "left_hip_roll",
    "left_hip_pitch",
    "left_knee_pitch",
    "left_ankle_pitch",
    "right_hip_yaw",
    "right_hip_roll",
    "right_hip_pitch",
    "right_knee_pitch",
    "right_ankle_pitch",
]


# Put your model code in here!!
class MyModel:
    """Placeholder for a real model. Replace 'infer' with your code.

    Example usage:
      - Load your PyTorch/ONNX model in __init__ if needed.
      - In 'infer', do something like 'return self.model(obs_tensor)'.
    """

    def __init__(self, num_joints: int) -> None:
        self.num_joints = num_joints
        self.model = None

    def infer(self, obs: np.ndarray) -> np.ndarray:
        """Process observation and return joint commands.

        obs: shape (3*num_joints + 6,) = positions, velocities, prev_actions, IMU
        returns: shape (num_joints,) = your desired joint commands
        """
        # TODO: Put your model code here
        # For demonstration, just return zeros.
        return np.zeros(self.num_joints, dtype=np.float32)


class DummyModel:
    """Simple random model for testing. Returns random actions in [-0.5, 0.5].

    Expects an observation array of shape (3*num_joints + 6,).
    Returns an action array of shape (num_joints,).
    """

    def __init__(self, num_joints: int) -> None:
        self.num_joints = num_joints

    def infer(self, obs: np.ndarray) -> np.ndarray:
        return np.random.uniform(low=-0.5, high=0.5, size=(self.num_joints,))


# MAIN LOGIC


def configure_actuators(kos: pykos.KOS, joint_names: list[str], kp: float = 32.0, kd: float = 32.0) -> None:
    """Configure each actuator with preset gains. If you've done this elsewhere, skip by passing --skip-config."""
    for joint_name in joint_names:
        actuator_id = ACTUATOR_NAME_TO_ID[joint_name]
        logging.info(
            "Configuring actuator %d (%s) with kp=%s, kd=%s, torque_enabled=True", actuator_id, joint_name, kp, kd
        )
        kos.actuator.configure_actuator(
            actuator_id=actuator_id,
            kp=kp,
            kd=kd,
            torque_enabled=True,
        )


def disable_torque(kos: pykos.KOS, joint_names: list[str]) -> None:
    """Disable torque on the specified actuators for safety."""
    for jn in joint_names:
        actuator_id = ACTUATOR_NAME_TO_ID[jn]
        kos.actuator.configure_actuator(actuator_id, torque_enabled=False)
    logging.info("All specified actuators torque disabled.")


def get_joint_positions_and_velocities(
    kos: pykos.KOS,
    joint_names: list[str],
) -> tuple[dict[str, float], dict[str, float]]:
    """Get current joint positions and velocities.

    Returns (positions_deg, velocities_dps)
      - positions_deg: Dict[joint_name, float]
      - velocities_dps: Dict[joint_name, float]
    Angles and velocities are in degrees/degrees-per-second from KOS by default.
    """
    actuator_ids = [ACTUATOR_NAME_TO_ID[j] for j in joint_names]
    response = kos.actuator.get_actuators_state(actuator_ids)
    states = response.states
    positions_deg = {}
    velocities_dps = {}
    for s in states:
        jn = next(k for k, v in ACTUATOR_NAME_TO_ID.items() if v == s.actuator_id)
        positions_deg[jn] = s.position
        velocities_dps[jn] = s.velocity
    return positions_deg, velocities_dps


def get_imu_values(kos: pykos.KOS) -> np.ndarray:
    """Get IMU readings.

    Example function returning an IMU reading of shape (6,).
    By default: (acc_x, acc_y, acc_z, grav_x, grav_y, grav_z).
    """
    imu_data = kos.imu.get_imu_advanced_values()
    return np.array(
        [
            imu_data.lin_acc_x,
            imu_data.lin_acc_y,
            imu_data.lin_acc_z,
            imu_data.grav_x,
            imu_data.grav_y,
            imu_data.grav_z,
        ],
        dtype=np.float32,
    )


def command_robot(kos: pykos.KOS, joint_names: list[str], actions_deg: dict[str, float]) -> None:
    """Send position commands to the specified actuators.

    Args:
        actions_deg: Dict[joint_name, position_in_degrees]
    """
    commands = []
    for jn in joint_names:
        actuator_id = ACTUATOR_NAME_TO_ID[jn]
        commands.append({"actuator_id": actuator_id, "position": actions_deg[jn]})
    kos.actuator.command_actuators(commands)


def run_control_loop(kos, model, joint_names, args):
    """Run the main control loop for the robot.

    Args:
        kos: KOS instance or None if dry run
        model: Model instance to use for inference
        joint_names: List of joint names to control
        args: Command line arguments
    """
    n_joints = len(joint_names)

    # We'll store the previous action from the model, start with zeros
    prev_action = np.zeros(n_joints, dtype=np.float32)

    # If you need sign flips or offsets, define them here. We'll just do +1 everywhere
    joint_signs = {jn: 1.0 for jn in joint_names}

    # 50 Hz
    target_dt = 1.0 / 50.0

    try:
        for step_idx in range(args.num_steps):
            loop_start = time.time()

            # 1. Read sensor data
            if kos is not None:
                positions_deg, velocities_dps = get_joint_positions_and_velocities(kos, joint_names)
                imu_vals = get_imu_values(kos)
            else:
                positions_deg = {jn: 0.0 for jn in joint_names}
                velocities_dps = {jn: 0.0 for jn in joint_names}
                imu_vals = np.zeros(6, dtype=np.float32)

            # 2. Build observation: (3*N + 6) -> N pos, N vel, N prev_actions, 6 IMU
            pos_array = np.array([positions_deg[jn] * joint_signs[jn] for jn in joint_names], dtype=np.float32)
            vel_array = np.array([velocities_dps[jn] * joint_signs[jn] for jn in joint_names], dtype=np.float32)
            obs = np.concatenate([pos_array, vel_array, prev_action, imu_vals], axis=0)

            # 3. Run inference
            new_action = model.infer(obs)  # shape (n_joints,)

            # 4. Command actuators
            if kos is not None:
                # If your model outputs degrees, we pass them directly.
                # If radians/normalized, do your conversion here.
                actions_deg = {}
                for i, jn in enumerate(joint_names):
                    actions_deg[jn] = float(new_action[i] * joint_signs[jn])
                command_robot(kos, joint_names, actions_deg)

            # 5. Store new_action for next iteration
            prev_action = new_action

            # 6. Sleep ~50Hz
            elapsed = time.time() - loop_start
            if elapsed < target_dt:
                time.sleep(target_dt - elapsed)

    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    finally:
        # Disable torque for safety
        if kos is not None:
            disable_torque(kos, joint_names)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-type",
        type=str,
        default="my",
        choices=["my", "dummy"],
        help="Which model to use: 'my' (MyModel) or 'dummy' (DummyModel).",
    )
    parser.add_argument("--ip", type=str, default="192.168.42.1", help="KOS IP address.")
    parser.add_argument("--num-steps", type=int, default=50, help="Number of inference steps to run.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logs.")
    parser.add_argument("--dry-run", action="store_true", help="If set, no hardware calls are made (offline test).")
    parser.add_argument("--skip-config", action="store_true", help="If set, skip configuring actuators in this script.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    joint_names = JOINTS_TO_MOVE
    n_joints = len(joint_names)

    # Connect to hardware unless --dry-run
    kos = None if args.dry_run else pykos.KOS(ip=args.ip)

    # Build model
    if args.model_type == "dummy":
        logging.info("Using DummyModel for random actions.")
        model = DummyModel(n_joints)
    else:
        logging.info("Using MyModel (zeros output by default).")
        model = MyModel(n_joints)

    # Configure actuators unless --skip-config
    if kos and not args.skip_config:
        configure_actuators(kos, joint_names)
        time.sleep(1.0)  # small delay for config to settle

    # Run the control loop
    run_control_loop(kos, model, joint_names, args)


if __name__ == "__main__":
    main()
