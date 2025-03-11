from PyQt6.QtCore import QThread, pyqtSignal
import os
import cv2

from visualization import Visualization


class SimulationWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    interrupted = pyqtSignal()
    new_data = pyqtSignal(object, int)  # Signal to send data to the GUI thread

    def __init__(self, calc, export_ith_image):
        super().__init__()
        self.calc = calc
        self.vis = Visualization(calc)
        self.running = True
        self.export_ith_image = export_ith_image
        self._initialize_image_folder()

    def _initialize_image_folder(self) -> None:
        """
        Deletes all files from previous runs. Ensures the image folder exists.
        """
        image_folder = self.vis.image_folder
        if os.path.exists(image_folder):
            for file in os.listdir(image_folder[:-1]):
                file_object_path = os.path.join(image_folder, file)
                os.remove(file_object_path)
        os.makedirs(image_folder, exist_ok=True)

    def _emit_progress(self, i, t_steps) -> None:
        """ Emits progress as a percentage. """
        self.progress.emit(int(i / t_steps * 100))

    # noinspection PyUnresolvedReferences
    def run(self):
        self.vis.plot_wave_packet(self.calc.get_packet(), 0)
        t_steps = self.calc.division_time

        for i in range(1, t_steps + 1):
            if not self.running:
                break  # Stop simulation if needed

            self.calc.calculate_timestep()

            # plot only every i-th image
            if i % self.export_ith_image == 0:
                self.vis.plot_wave_packet(self.calc.get_packet(), i)

            self._emit_progress(i, t_steps)

        if self.running:
            self.finished.emit()
            self.progress.emit(100)
        else:
            self.interrupted.emit()

    def stop(self):
        """Stops the simulation thread."""
        self.running = False
        self.wait()  # Ensures thread finishes before exiting


class ExportVideoWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    video_name = "tunnelling_video.mp4"

    def __init__(self, image_folder, fps):
        super().__init__()
        self.image_folder = image_folder
        self.image_names = sorted(
            [f for f in os.listdir(self.image_folder) if
             f.startswith("frame_") and f.split('_')[1].split('.')[0].isdigit()],
            key=lambda x: int(x.split('_')[1].split('.')[0])
        )
        self.image_number = len(self.image_names)
        self._initialize_video_writer(fps)

    def _initialize_video_writer(self, fps):
        """
        Initializes cv2 VideoWriter with proper settings.
        """
        # loads first found image in the image folder and extracts its dimensions
        frame = cv2.imread(os.path.join(self.image_folder, self.image_names[0]))
        height, width, _ = frame.shape
        # define fourcc
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        # initialize VideoWriter
        self.video = cv2.VideoWriter(self.video_name, fourcc, fps, (width, height))

    def _create_video(self):
        """Creates a video from stored frames."""
        for i, image in enumerate(self.image_names):
            self.video.write(cv2.imread(os.path.join(self.image_folder, image)))
            self.progress.emit(int(i / self.image_number * 100))
        self.video.release()
        self.progress.emit(100)  # Ensure progress reaches 100

    # noinspection PyUnresolvedReferences
    def run(self):
        self._create_video()
        self.finished.emit()
