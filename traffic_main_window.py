import os
import random

import cv2
from PyQt5.QtCore import QDateTime, QTimer
from PyQt5.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from traffic_capture import VehicleCaptureSaver
from traffic_database import CaptureDatabase
from traffic_detector import VehicleDetector
from traffic_ui import DashboardCard, VideoTile


class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.total = 0
        self.cap = cv2.VideoCapture(self.config.video_path)
        self.capture_database = CaptureDatabase(self.config.database_path)
        self.capture_saver = VehicleCaptureSaver(
            capture_root=self.config.capture_root,
            save_cooldown_seconds=self.config.save_cooldown_seconds,
            capture_database=self.capture_database,
        )
        self.detector = VehicleDetector(
            model_path=self.config.model_path,
            capture_saver=self.capture_saver,
        )

        self.setWindowTitle(self.config.window_title)
        self.resize(self.config.window_width, self.config.window_height)
        self.setStyleSheet(
            "QMainWindow{background:#121212;} QLabel{color:white;} "
            "QPushButton{padding:8px;border-radius:8px;background:#2d2d2d;color:white;} "
            "QPushButton:hover{background:#3d3d3d;}"
        )

        self._build_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        if self._validate_startup():
            self.timer.start(self.config.timer_interval_ms)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)

        side = QFrame()
        side.setFixedWidth(220)
        side.setStyleSheet("background:#181818;")
        side_layout = QVBoxLayout(side)
        brand = QLabel("Traffic Monitor")
        brand.setStyleSheet("font-size:20px;font-weight:bold;padding:15px;")
        side_layout.addWidget(brand)
        for txt in ["Dashboard", "Live Cameras", "Analytics", "Alerts", "Settings"]:
            side_layout.addWidget(QPushButton(txt))
        side_layout.addStretch()
        main_layout.addWidget(side)

        content = QVBoxLayout()
        top = QHBoxLayout()
        self.clock = QLabel()
        top.addWidget(QLabel("Control Center"))
        top.addStretch()
        top.addWidget(self.clock)
        content.addLayout(top)

        cards = QHBoxLayout()
        self.card1 = DashboardCard("Vehicles Detected")
        self.card2 = DashboardCard("Active Stream")
        self.card3 = DashboardCard("Alerts")
        self.card4 = DashboardCard("FPS")
        for card in [self.card1, self.card2, self.card3, self.card4]:
            cards.addWidget(card)
        content.addLayout(cards)

        grid = QGridLayout()
        self.tiles = []
        for index in range(1):
            tile = VideoTile(f"Camera {index + 1}")
            self.tiles.append(tile)
            grid.addWidget(tile, index // 2, index % 2)
        content.addLayout(grid, 1)

        wrap = QWidget()
        wrap.setLayout(content)
        main_layout.addWidget(wrap, 1)

    def _show_startup_error(self, title, message):
        QMessageBox.critical(self, title, message)
        self.close()

    def _validate_startup(self):
        if not self.cap.isOpened():
            self._show_startup_error(
                "Video Error",
                f"Could not open the video file:\n{os.path.abspath(self.config.video_path)}",
            )
            return False

        if self.detector.import_error is not None:
            self._show_startup_error(
                "PyTorch / YOLO Error",
                "The app could not load Ultralytics/PyTorch.\n\n"
                "This is usually caused by a broken PyTorch install or missing Windows VC++ runtime files.\n\n"
                f"Details:\n{self.detector.import_error}",
            )
            return False

        if not os.path.exists(self.config.model_path):
            self._show_startup_error(
                "Model File Missing",
                f"Could not find the YOLO model file:\n{os.path.abspath(self.config.model_path)}\n\n"
                "Place yolov8n.pt in the configured path before starting the app.",
            )
            return False

        try:
            self.detector.load()
        except Exception as exc:
            self._show_startup_error(
                "Model Load Error",
                f"The model file could not be loaded.\n\nDetails:\n{exc}",
            )
            return False

        return True

    def update_ui(self):
        self.clock.setText(QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"))

        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        result = self.detector.detect(frame)
        for tile in self.tiles:
            tile.set_frame(result.frame)

        self.total += result.count
        self.card1.v.setText(str(self.total))
        self.card2.v.setText("1")
        self.card3.v.setText(str(random.randint(0, 2)))
        self.card4.v.setText(str(random.randint(18, 30)))
