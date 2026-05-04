import sys

from PyQt5.QtWidgets import QApplication

from traffic_config import APP_CONFIG
from traffic_main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow(APP_CONFIG)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
