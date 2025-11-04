import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from gui import Ui_mainWindow   # this is your designer code file

class MyApp(QMainWindow, Ui_mainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)   # this loads all the widgets

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())

