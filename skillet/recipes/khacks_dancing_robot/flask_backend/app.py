# Copyright 2025 Homero Roman
# MIT License
# Flask app that takes in a trajectory and calls pykos to make a robot dance
import os
from os.path import join
from dataclasses import dataclass
from flask import Flask, request, jsonify


app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@dataclass
class Poses:
    A_POSE: str
    T_POSE: str
    Y_POSE: str

@dataclass
class AllowedTrajectories:
    A_POSE_TO_T_POSE: str = 'A_POSE_TO_T_POSE'
    T_POSE_TO_A_POSE: str = 'T_POSE_TO_A_POSE'
    T_POSE_TO_Y_POSE: str = 'T_POSE_TO_Y_POSE'
    Y_POSE_TO_T_POSE: str = 'Y_POSE_TO_T_POSE'


@app.route("/send_trajectory/<trajectory>")
def send_trajectory(trajectory):
    print(trajectory)
    if trajectory in AllowedTrajectories.__dataclass_fields__.keys():
        call_pykos(trajectory)
        response = jsonify({"error": "", "data": f"Trajectory '{trajectory}' received"})
    else:
        response = jsonify({"error": "1", "data": f"Trajectory '{trajectory}' not found"})
    response.headers.add("Access-Control-Allow-Origin", "*")        
    return response


def call_pykos(trajectory):
    if trajectory in AllowedTrajectories.__dataclass_fields__.keys():
        script_path = join(
            os.getcwd(), "..", "..", "skillit", "examples"
        )
        command = f"cd {script_path}"
        command += " && python play_record_example.py play --ip 192.168.42.1"
        if trajectory == AllowedTrajectories.A_POSE_TO_T_POSE:
            command += " --file A_to_T.json"
        elif trajectory == AllowedTrajectories.T_POSE_TO_A_POSE:
            command += " --file T_to_A.json"
        elif trajectory == AllowedTrajectories.T_POSE_TO_Y_POSE:
            command += " --file T_to_Y.json"
        elif trajectory == AllowedTrajectories.Y_POSE_TO_T_POSE:
            command += " --file Y_to_T.json"
        else:
            return
        
        print(f"Sending command {command}")
        os.system(command)