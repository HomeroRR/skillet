# DanceBot: AI-Powered Dancing Robot

A dancing robot platform powered by MilkV Pioneer board, combining motion control with AI-driven choreography generation and simulation.

## Overview

DanceBot is an open-source project that creates fluid, natural dance movements using human pose estimation. The system leverages the MilkV Pioneer board for real-time control, Jetson for AI processing, and Genesis AI for movement simulation and optimization.

## Hardware Requirements

- MilkV Pioneer Board
- NVIDIA Jetson (Nano or Xavier NX recommended)
- Servo motors (minimum 12 DOF recommended)
  - 4x for legs/feet
  - 4x for hip/torso
  - 4x for arms
- IMU sensor for balance feedback
- Optional: RGB camera for visual feedback
- 12V power supply
- Custom 3D printed chassis (STL files provided)

## Software Stack

- Ubuntu 22.04 LTS
- ROS2 Humble
- Python 3.10+
- Genesis AI SDK
- Custom motion control package
- Jetson inference engine

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/HomeroRR/skillet.git
```

2. Start movenet in Tensorflow.js

   Follow the steps at pose-detection/demos/live_video

   Then go to http://localhost:1234/?model=movenet

3. Start the flask server:
```bash
cd flask_backend
flask --app app run
```

## Features

- Real-time motion planning and execution
- AI-generated dance choreography
- Physics-based simulation for movement optimization
- Balance control and feedback system
- Multiple dance style support
- Remote control interface
- Gesture recognition (optional)

## AI Integration

The project uses Genesis AI for:
- Movement simulation and optimization
- Natural motion generation
- Physics-based constraints handling
- Real-time adaptation
- Style transfer between different dance forms

## Safety Features

- Built-in balance monitoring
- Motor torque limits
- Emergency stop system
- Voltage monitoring
- Temperature management
- Collision detection

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

Please read CONTRIBUTING.md for details on our code of conduct and development process.

## Performance Optimization

- Use the Jetson for AI processing
- Offload motion planning to the MilkV board
- Implement parallel processing where possible
- Optimize sensor polling rates
- Use efficient communication protocols

## Troubleshooting

Common issues and solutions:

1. Motor Calibration
   - Follow the calibration guide in docs/calibration.md
   - Check voltage levels
   - Verify servo connections

2. Balance Issues
   - Check IMU calibration
   - Verify weight distribution
   - Update PID parameters

3. Communication Errors
   - Check USB connections
   - Verify baudrate settings
   - Update firmware if needed

## License

This project is licensed under the MIT License - see LICENSE.md for details.

## Citations

- Genesis AI Documentation
- MilkV Pioneer Technical Reference
- Jetson Development Guide
- ROS2 Documentation

## Contact

For support:
- Create an issue in the repository
- Join our Discord community
- Email: support@dancebot-project.org

## Future Development

- Advanced dance style integration
- Multi-robot choreography
- Machine learning for style adaptation
- Visual feedback processing
- Audio rhythm synchronization
