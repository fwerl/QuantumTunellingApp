from src.gui import QuantumTunnellingApp
from PyQt6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication([])
    window = QuantumTunnellingApp()
    app.exec()