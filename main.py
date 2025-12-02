from PyQt6.QtWidgets import QApplication, QMainWindow

from Earth_Project import Ui_mainWindow
from logic import EarthSimulation


def main():
    app = QApplication([])
    window = QMainWindow()

    ui = Ui_mainWindow()
    ui.setupUi(window)

    # Hook up the simulation logic to the GUI
    sim = EarthSimulation(ui)

    window.show()
    app.exec()


if __name__ == "__main__":
    main()

