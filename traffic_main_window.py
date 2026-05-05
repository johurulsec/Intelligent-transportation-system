import os
import urllib.request

import cv2
from PyQt5.QtCore import QDateTime, QTimer
from PyQt5.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from traffic_capture import VehicleCaptureSaver
from traffic_database import CaptureDatabase
from traffic_detector import VehicleDetector
from traffic_ocr import PlateOcrReader
from traffic_ui import DashboardCard, VideoTile


class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.total = 0
        self.total_plates = 0
        self.cap = cv2.VideoCapture(self.config.video_path)
        self.capture_database = CaptureDatabase(self.config.database_path)
        self.plate_ocr_reader = PlateOcrReader(self.config.tesseract_cmd)
        self.capture_saver = VehicleCaptureSaver(
            capture_root=self.config.capture_root,
            save_cooldown_seconds=self.config.save_cooldown_seconds,
            capture_database=self.capture_database,
        )
        self.detector = VehicleDetector(
            vehicle_model_path=self.config.model_path,
            plate_model_path=self.config.plate_model_path,
            capture_saver=self.capture_saver,
            plate_ocr_reader=self.plate_ocr_reader,
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
        self.card3 = DashboardCard("Plates Detected")
        self.card4 = DashboardCard("OCR Engine")
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

    def _ensure_model_file(self, model_path, model_url, model_label):
        if os.path.exists(model_path):
            return True

        message = (
            f"Could not find the {model_label} model file:\n{os.path.abspath(model_path)}\n\n"
        )
        if model_url:
            message += "Do you want to download it automatically now?"
            answer = QMessageBox.question(
                self,
                "Model File Missing",
                message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if answer != QMessageBox.Yes:
                return False

            try:
                self._download_model(model_url, model_path)
            except Exception as exc:
                self._show_startup_error(
                    "Download Failed",
                    f"Could not download the {model_label} model.\n\nDetails:\n{exc}",
                )
                return False

            QMessageBox.information(
                self,
                "Download Complete",
                f"The {model_label} model was downloaded successfully:\n{os.path.abspath(model_path)}",
            )
            return True

        self._show_startup_error(
            "Model File Missing",
            message + "Automatic download is not configured for this model yet.",
        )
        return False

    @staticmethod
    def _download_model(model_url, model_path):
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        urllib.request.urlretrieve(model_url, model_path)

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

        if not self._ensure_model_file(self.config.model_path, self.config.model_url, "vehicle"):
            return False

        if self.config.plate_model_path and not self._ensure_model_file(
            self.config.plate_model_path,
            self.config.plate_model_url,
            "license plate",
        ):
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

        self.total += result.vehicle_count
        self.total_plates += result.plate_count
        self.card1.v.setText(str(self.total))
        self.card2.v.setText("1")
        self.card3.v.setText(str(self.total_plates))
        self.card4.v.setText(self.plate_ocr_reader.engine_name)
