import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    video_path: str = r"d:\its-info\sample-vehicle2.mp4"
    # video_path: str = r"d:\its-info\lpr-vehicle.mp4"
    model_path: str = r"d:\its-info\yolov8n.pt"
    model_url: str | None = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
    plate_model_path: str = r"d:\its-info\license_plate_detector.pt"
    plate_model_url: str | None = None
    tesseract_cmd: str | None = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    capture_root: str = r"d:\its-info\capture_vehicles"
    database_path: str = r"d:\its-info\transport.db"
    window_title: str = "Intelligent Transportation System"
    window_width: int = 1400
    window_height: int = 900
    timer_interval_ms: int = 30
    save_cooldown_seconds: float = 1.0


APP_CONFIG = AppConfig()
ULTRALYTICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".ultralytics")

os.makedirs(ULTRALYTICS_DIR, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", ULTRALYTICS_DIR)
