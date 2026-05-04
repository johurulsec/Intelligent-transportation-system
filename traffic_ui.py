import cv2
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


class VideoTile(QFrame):
    def __init__(self, title):
        super().__init__()
        self.current_pixmap = None
        self.setStyleSheet("background:#1e1e1e;border:1px solid #333;border-radius:10px;")
        self.label = QLabel("No Signal")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color:#aaa;font-size:18px;")
        self.label.setMinimumSize(320, 180)
        self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.title = QLabel(title)
        self.title.setStyleSheet("color:white;font-weight:bold;padding:6px;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.label, 1)

    def set_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb.shape
        image = QImage(rgb.data, width, height, channels * width, QImage.Format_RGB888)
        self.current_pixmap = QPixmap.fromImage(image)
        self._update_pixmap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()

    def _update_pixmap(self):
        if self.current_pixmap is None or self.label.size().isEmpty():
            return
        scaled = self.current_pixmap.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled)


class DashboardCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setStyleSheet("background:#232323;border-radius:12px;")
        self.v = QLabel("0")
        self.v.setStyleSheet("color:#00d084;font-size:28px;font-weight:bold;")
        label = QLabel(title)
        label.setStyleSheet("color:#bbb;")

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.v)
