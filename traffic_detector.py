from dataclasses import dataclass
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


YOLO = None
YOLO_IMPORT_ERROR = None
try:
    from ultralytics import YOLO
except Exception as exc:
    YOLO_IMPORT_ERROR = exc


@dataclass
class DetectionResult:
    frame: object
    vehicle_count: int
    plate_count: int


class VehicleDetector:
    vehicle_classes = {"car", "bus", "truck", "motorcycle", "bicycle"}

    def __init__(self, vehicle_model_path, plate_model_path=None, capture_saver=None, plate_ocr_reader=None):
        self.vehicle_model_path = vehicle_model_path
        self.plate_model_path = plate_model_path
        self.capture_saver = capture_saver
        self.plate_ocr_reader = plate_ocr_reader
        self.vehicle_model = None
        self.plate_model = None

    @property
    def import_error(self):
        return YOLO_IMPORT_ERROR

    @property
    def plate_detection_enabled(self):
        return self.plate_model is not None

    def load(self):
        if YOLO_IMPORT_ERROR is not None:
            raise YOLO_IMPORT_ERROR

        self.vehicle_model = YOLO(self.vehicle_model_path)
        if self.plate_model_path and os.path.exists(self.plate_model_path):
            self.plate_model = YOLO(self.plate_model_path)

    def detect(self, frame):
        if self.vehicle_model is None:
            return DetectionResult(frame=frame, vehicle_count=0, plate_count=0)

        vehicle_count = 0
        plate_count = 0
        original_frame = frame.copy()
        results = self.vehicle_model(frame, verbose=False)
        names = self.vehicle_model.names

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                name = names[cls]
                if name not in self.vehicle_classes:
                    continue

                vehicle_count += 1
                vehicle_box = tuple(map(int, box.xyxy[0]))
                conf = float(box.conf[0])

                best_plate = self._detect_plate_for_vehicle(original_frame, vehicle_box)
                plate_text = None
                if best_plate is not None:
                    plate_count += 1
                    plate_text = self._read_plate_text(original_frame, best_plate)
                    self._draw_plate_overlay(frame, best_plate, plate_text)

                if self.capture_saver is not None:
                    self.capture_saver.save_detection(
                        frame=original_frame,
                        vehicle_type=name,
                        vehicle_box=vehicle_box,
                        plate_box=best_plate,
                        plate_text=plate_text,
                    )

                cv2.rectangle(frame, (vehicle_box[0], vehicle_box[1]), (vehicle_box[2], vehicle_box[3]), (0, 255, 255), 2)
                cv2.putText(frame, f"{name} {conf:.2f}", (vehicle_box[0], vehicle_box[1] - 5), 0, 1, (255, 255, 0), 2)

        return DetectionResult(frame=frame, vehicle_count=vehicle_count, plate_count=plate_count)

    def _detect_plate_for_vehicle(self, frame, vehicle_box):
        if self.plate_model is None:
            return None

        x1, y1, x2, y2 = vehicle_box
        vehicle_crop = frame[y1:y2, x1:x2]
        if vehicle_crop.size == 0:
            return None

        results = self.plate_model(vehicle_crop, verbose=False)
        best_box = None
        best_confidence = -1.0

        for result in results:
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf <= best_confidence:
                    continue

                px1, py1, px2, py2 = map(int, box.xyxy[0])
                best_box = (x1 + px1, y1 + py1, x1 + px2, y1 + py2)
                best_confidence = conf

        return best_box

    def _read_plate_text(self, frame, plate_box):
        if self.plate_ocr_reader is None:
            return None

        x1, y1, x2, y2 = plate_box
        plate_crop = frame[y1:y2, x1:x2]
        if plate_crop.size == 0:
            return None

        return self.plate_ocr_reader.read_text(plate_crop)

    @staticmethod
    def _draw_plate_overlay(frame, plate_box, plate_text):
        x1, y1, x2, y2 = plate_box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
        label = plate_text if plate_text else "plate"
        VehicleDetector._draw_unicode_text(frame, label, (x1, max(28, y1 - 10)))

    @staticmethod
    def _draw_unicode_text(frame, text, position):
        font = VehicleDetector._load_text_font()
        if font is None:
            cv2.putText(frame, text, position, 0, 0.8, (0, 165, 255), 2)
            return

        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(image)
        x, y = position
        bbox = draw.textbbox((x, y), text, font=font)
        draw.rectangle(
            (bbox[0] - 4, bbox[1] - 2, bbox[2] + 4, bbox[3] + 2),
            fill=(24, 24, 24),
        )
        draw.text((x, y), text, font=font, fill=(255, 165, 0))
        frame[:] = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    @staticmethod
    def _load_text_font():
        candidates = [
            r"C:\Windows\Fonts\Nirmala.ttf",
            r"C:\Windows\Fonts\NirmalaB.ttf",
            r"C:\Windows\Fonts\arial.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, 24)
                except Exception:
                    continue
        return None
