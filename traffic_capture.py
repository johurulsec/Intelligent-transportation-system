import os
import time
from dataclasses import dataclass
from datetime import datetime

import cv2


@dataclass
class SavedCapture:
    vehicle_type: str
    captured_at: str
    vehicle_image_path: str | None
    vehicle_image_name: str | None = None
    plate_image_path: str | None = None
    plate_image_name: str | None = None
    plate_text: str | None = None
    plate_text_path: str | None = None


class VehicleCaptureSaver:
    def __init__(
        self,
        capture_root,
        save_cooldown_seconds=1.0,
        capture_database=None,
        save_images_enabled=True,
        save_database_enabled=True,
    ):
        self.capture_root = capture_root
        self.save_cooldown_seconds = save_cooldown_seconds
        self.capture_database = capture_database
        self.save_images_enabled = save_images_enabled
        self.save_database_enabled = save_database_enabled
        self._last_saved_at = {}

    def save_detection(self, frame, vehicle_type, vehicle_box, plate_box=None, plate_text=None):
        if not self.save_images_enabled and not self.save_database_enabled:
            return None

        now = time.time()
        if now - self._last_saved_at.get(vehicle_type, 0.0) < self.save_cooldown_seconds:
            return None

        stamp = datetime.now()
        date_folder = stamp.strftime("%d-%m-%Y")
        timestamp = stamp.strftime("%H-%M-%S-%f")[:-3]
        captured_at = stamp.isoformat(timespec="milliseconds")
        vehicle_image_name = f"{timestamp}.png"

        vehicle_crop = self._crop_frame(frame, vehicle_box)
        if vehicle_crop is None:
            return None

        vehicle_dir = os.path.join(self.capture_root, date_folder, vehicle_type)
        vehicle_image_path = None
        if self.save_images_enabled:
            os.makedirs(vehicle_dir, exist_ok=True)
            vehicle_image_path = os.path.join(vehicle_dir, vehicle_image_name)
            if not cv2.imwrite(vehicle_image_path, vehicle_crop):
                return None
        elif self.save_database_enabled:
            vehicle_image_path = self._virtual_capture_path(date_folder, vehicle_type, vehicle_image_name)

        plate_image_path = None
        plate_image_name = None
        plate_text_path = None
        if plate_box is not None:
            plate_crop = self._crop_frame(frame, plate_box)
            if plate_crop is not None:
                plate_image_name = f"{timestamp}.png"
                if self.save_images_enabled:
                    plate_dir = os.path.join(vehicle_dir, "plates")
                    os.makedirs(plate_dir, exist_ok=True)
                    plate_image_path = os.path.join(plate_dir, plate_image_name)
                    if not cv2.imwrite(plate_image_path, plate_crop):
                        plate_image_path = None
                    elif plate_text:
                        plate_text_path = os.path.join(plate_dir, f"{timestamp}.txt")
                        with open(plate_text_path, "w", encoding="utf-8") as text_file:
                            text_file.write(plate_text)
                elif self.save_database_enabled:
                    plate_image_path = self._virtual_capture_path(date_folder, vehicle_type, plate_image_name, "plates")

        self._last_saved_at[vehicle_type] = now
        saved_capture = SavedCapture(
            vehicle_type=vehicle_type,
            captured_at=captured_at,
            vehicle_image_path=vehicle_image_path,
            vehicle_image_name=vehicle_image_name,
            plate_image_path=plate_image_path,
            plate_image_name=plate_image_name,
            plate_text=plate_text,
            plate_text_path=plate_text_path,
        )

        if self.save_database_enabled and self.capture_database is not None:
            self.capture_database.log_capture(saved_capture)

        return saved_capture

    def _virtual_capture_path(self, date_folder, vehicle_type, image_name, *parts):
        virtual_parts = ["virtual-capture", date_folder, vehicle_type, *parts, image_name]
        return "/".join(virtual_parts)

    @staticmethod
    def _crop_frame(frame, box):
        x1, y1, x2, y2 = box
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
        return crop
