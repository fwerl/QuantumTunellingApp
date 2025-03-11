from __future__ import annotations
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
                             QProgressBar, QGroupBox, QFormLayout)

from numerics import NumericalCalculation
from workers import SimulationWorker, ExportVideoWorker
from visualization import Visualization

# author: Filip Werl

# todo
# refactoring... done numerics.py, visualization.py, workers.py
# test on windows

class SimulationConfig:
    PARAMETERS = [
        ("Packet size [nm]:", "size_packet"),
        ("Barrier size [nm]:", "size_barrier"),
        ("Time duration [fs]:", "duration_time"),
        ("Packet energy [eV]:", "energy_packet"),
        ("Barrier height [eV]:", "potential_barrier_height"),
        ("dx [pm]:", "dx"),
        ("dt [as]:", "dt"),
        ("Export every i-th image:", "export_ith_image"),
        ("Video duration [s]:", "video_duration"),
    ]

    DEFAULT_VALUES = {
        "size_packet": 1,
        "size_barrier": 1,
        "duration_time": 30,
        "energy_packet": 1,
        "potential_barrier_height": 1,
        "dx": 10,
        "dt": 10,
        "export_ith_image": 20,
        "video_duration": 10,
    }

    CATEGORY_GROUPS = {
        "packet": ["size_packet", "energy_packet"],
        "barrier": ["size_barrier", "potential_barrier_height"],
        "simulation": ["duration_time", "dx", "dt"],
        "export": ["export_ith_image", "video_duration"],
    }
    COLOR_CODES = {
        "red": "#D32F2F",
        "green": "#66BB6A",
        "blue": "#007aff"
    }

    def __init__(self):
        pass

    def get_default_value(self, key) -> int | float:
        return self.DEFAULT_VALUES[key]

    def get_category_group_params(self, key) -> list:
        return self.CATEGORY_GROUPS[key]

    def get_color_code(self, color) -> str:
        return self.COLOR_CODES[color]


class QuantumTunnellingAppUI(QWidget):
    def __init__(self):
        super().__init__()
        self.config = SimulationConfig()
        self.setWindowTitle("Quantum Tunneling Simulation")
        self.layout = QVBoxLayout()
        self.entries = {}

        self._initialize_entries()
        self._initialize_start_button()
        self._initialize_progress_bar()
        self._initialize_export_button()

        self.setLayout(self.layout)

    def _initialize_entries(self) -> None:
        """
        Creates groups for entries, fills groups with approprieate entries, adds all groups to layout.
        :return: None
        """

        group_keys = self.config.CATEGORY_GROUPS.keys()

        # Initialize groups and group layouts
        self.groups = {}
        self.group_layouts = {}
        for group_key in group_keys:
            group_name_GUI = group_key.capitalize() + " Parameters"
            self.groups[group_key] = QGroupBox(group_name_GUI)
            self.group_layouts[group_key] = QFormLayout()

        # Add entries to group layouts from config.PARAMETERS
        for item in self.config.PARAMETERS:
            for group_key in group_keys:
                self._add_entry_row_in_group_layout(item, group_key)

        # Add groups to the main layout
        for group_key in group_keys:
            self.groups[group_key].setLayout(self.group_layouts[group_key])
            self.layout.addWidget(self.groups[group_key])

    def _initialize_start_button(self) -> None:
        """
        Initializes start button and adds it to the layout.
        :return:
        """
        self.start_button = QPushButton("Start Simulation")
        self.layout.addWidget(self.start_button)

    def _initialize_progress_bar(self) -> None:
        """
        Initializes progress bar, adds it to the layout, sets initial progress bar color and disables text visibility.
        :return: None
        """
        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)
        self.set_progress_bar_color("blue")
        self.progress_bar.setTextVisible(False)

    def _initialize_export_button(self) -> None:
        """
        Initializes export button and adds it to the layout.
        :return: None
        """
        self.export_button = QPushButton("Export Video")
        self.layout.addWidget(self.export_button)

    def _add_entry_row_in_group_layout(self, item, group_key):
        """
        Adds entry row in entry group.
        :param item: Item from GUI parameters from SimulationConfig class.
        :param group_key:
        :return:
        """
        label, key = item
        default_value = str(self.config.get_default_value(key))
        entry = self._create_entry(key, default_value)
        if key in self.config.get_category_group_params(group_key):
            self.group_layouts[group_key].addRow(QLabel(label), entry)

    def _create_entry(self, key, default_value):
        entry = QLineEdit()
        entry.setText(default_value)
        self.entries[key] = entry
        return entry

    def get_parameter_values(self):
        params = {key: float(entry_object.text()) for key, entry_object in self.entries.items()}
        params["export_ith_image"] = int(params["export_ith_image"])
        return params


    def set_progress_bar_color(self, color):
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border-radius: 6px;  /* Rounded corners */
                background-color: #e6e6e6;  /* Light gray background color for the unfilled portion */
                height: 5px;  /* Reduce the height of the progress bar */
            }}
            QProgressBar::chunk {{
                background-color: {self.config.get_color_code(color)};  /* Red color for the filled portion */
                border-radius: 6px;  /* Rounded corners for the chunk to match the overall style */
            }}
        """)

class QuantumTunnellingApp:
    # noinspection PyUnresolvedReferences
    def __init__(self):
        self.simulation_worker = None  # Track simulation thread
        self.video_worker = None  # Track simulation thread
        self.UI = QuantumTunnellingAppUI()
        self.UI.start_button.clicked.connect(self.toggle_simulation)
        self.UI.export_button.clicked.connect(self.export_video)
        self.UI.show()

    def start_simulation(self) -> None:
        self.UI.set_progress_bar_color("blue")

        params = self.UI.get_parameter_values()
        calc = self._initialize_numerical_calculation(params)
        self._initialize_and_start_simulation_worker(calc, params)

    def _initialize_numerical_calculation(self, params) -> NumericalCalculation:
        """
        Initializes NumericalCalculation class with actual parameters in the GUI.
        :return: NumericalCalculation instance
        """
        return NumericalCalculation(
            size_packet=params["size_packet"],
            size_barrier=params["size_barrier"],
            duration_time=params["duration_time"],
            energy_packet=params["energy_packet"],
            potential_barrier_height=params["potential_barrier_height"],
            dx=params["dx"],
            dt=params["dt"]
        )

    def _initialize_and_start_simulation_worker(self, calc: NumericalCalculation, params: dict) -> None:
        """
        Initializes SimulationWorker class, connects the simulation worker progress information to GUI elements
        visualisation. Then starts the simulation worker.
        :param calc: Instance of NumericalCalculation class
        :param params: Dictionary of parameters from the GUI.
        :return: None
        """
        # SimulationWorker class initialization
        self.simulation_worker = SimulationWorker(calc, params["export_ith_image"])

        # Connect simulation worker progress information to GUI visualisation
        self.simulation_worker.progress.connect(self.UI.progress_bar.setValue)
        self.simulation_worker.finished.connect(lambda: self.UI.start_button.setText("Start Simulation"))
        self.simulation_worker.finished.connect(lambda: self.UI.set_progress_bar_color("green"))
        self.simulation_worker.interrupted.connect(lambda: self.UI.set_progress_bar_color("red"))

        # Start simulation worker
        self.simulation_worker.start()


    def toggle_simulation(self) -> None:
        if self.simulation_worker and self.simulation_worker.isRunning():  # If simulation is running, stop it
            self.simulation_worker.stop()  # Stop the simulation
            self.simulation_worker.wait()  # Ensure thread cleanup
            self.UI.start_button.setText("Start Simulation")
            self.UI.set_progress_bar_color("red")
        else:  # Start a new simulation
            self.start_simulation()
            self.UI.start_button.setText("Stop Simulation")

    def _get_fps(self) -> int:
        params = self.UI.get_parameter_values()
        no_images = int(params["duration_time"]/params["dt"]*1000/params["export_ith_image"]) + 1
        fps=int(no_images/params["video_duration"])
        return fps

    def export_video(self) -> None:
        self.UI.set_progress_bar_color("blue")
        fps = self._get_fps()
        image_path = Visualization.get_image_path()
        self.video_worker = ExportVideoWorker(
            image_folder=image_path,
            fps=fps
        )
        self.video_worker.progress.connect(self.UI.progress_bar.setValue)
        self.video_worker.finished.connect(lambda: self.UI.set_progress_bar_color("green"))
        self.video_worker.start()

if __name__ == "__main__":
    app = QApplication([])
    window = QuantumTunnellingApp()
    app.exec()
