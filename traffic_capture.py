import os
import time
from datetime import datetime

import cv2


class VehicleCaptureSaver:
    def __init__(self, capture_root, save_cooldown_seconds=1.0, capture_database=None):
        self.capture_root = capture_root
        self.save_cooldown_seconds = save_cooldown_seconds
        self.capture_database = capture_database
        self._last_saved_at = {}

    def save_crop(self, frame, vehicle_type, x1, y1, x2, y2):
        now = time.time()
        if now - self._last_saved_at.get(vehicle_type, 0.0) < self.save_cooldown_seconds:
            return None

        height, width = frame.shape[:2]
        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(0, min(x2, width))
        y2 = max(0, min(y2, height))
        if x2 <= x1 or y2 <= y1:
            return None

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None

        stamp = datetime.now()
        folder_name = stamp.strftime("%d-%m-%Y")
        timestamp = stamp.strftime("%H-%M-%S-%f")[:-3]
        target_dir = os.path.join(self.capture_root, folder_name, vehicle_type)
        os.makedirs(target_dir, exist_ok=True)

        file_path = os.path.join(target_dir, f"{timestamp}.png")
        if cv2.imwrite(file_path, crop):
            self._last_saved_at[vehicle_type] = now
            if self.capture_database is not None:
                self.capture_database.log_capture(
                    vehicle_type=vehicle_type,
                    image_path=file_path,
                    captured_at=stamp.isoformat(timespec="milliseconds"),
                )
            return file_path
        return None
