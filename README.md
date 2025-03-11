# Quantum Tunneling Simulation App

This application simulates quantum tunneling, a phenomenon where a particle can pass through a potential barrier even if it doesn't have enough energy to overcome it classically. The simulation visualizes the behavior of a wave packet as it interacts with a potential barrier.

## Features

*   **Interactive Simulation:** Allows users to set various parameters such as packet size, barrier size, energy, and simulation time.
*   **Visualization:** Displays the wave packet's real and imaginary parts, probability density, and Fourier transform.
*   **Export Video:** Capable of exporting the simulation as a video file.
*   **Configurable Parameters:** Exposes key simulation parameters through a user-friendly interface, enabling experimentation with different scenarios.

## How It Works

The application numerically solves the time-dependent Schrödinger equation to simulate the quantum tunneling process. It uses a finite difference method to discretize space and time, and sparse matrix algebra for efficient computation. The simulation calculates the wave function at each time step and visualizes its evolution.

## Key Components

*   **`gui.py`:** Defines the graphical user interface using PyQt6, providing input fields for parameters and controls for starting the simulation and exporting video.
*   **`numerics.py`:** Contains the `NumericalCalculation` class, which handles the numerical calculations for solving the Schrödinger equation. It sets up the simulation space, defines the potential barrier, and calculates the time evolution of the wave packet.
*   **`visualization.py`:** Implements the `Visualization` class, responsible for plotting the wave packet and potential barrier at each time step using Matplotlib. It generates images that can be combined to create a video.
*   **`workers.py`:** Defines worker threads (`SimulationWorker` and `ExportVideoWorker`) to perform the simulation and video export in the background.

## Note

This application has been tested only on macOS.