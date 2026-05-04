from dataclasses import dataclass

import cv2


YOLO = None
YOLO_IMPORT_ERROR = None
try:
    from ultralytics import YOLO
except Exception as exc:
    YOLO_IMPORT_ERROR = exc


@dataclass
class DetectionResult:
    frame: object
    count: int


class VehicleDetector:
    vehicle_classes = {"car", "bus", "truck", "motorcycle", "bicycle"}

    def __init__(self, model_path, capture_saver=None):
        self.model_path = model_path
        self.capture_saver = capture_saver
        self.model = None

    @property
    def import_error(self):
        return YOLO_IMPORT_ERROR

    def load(self):
        if YOLO_IMPORT_ERROR is not None:
            raise YOLO_IMPORT_ERROR
        self.model = YOLO(self.model_path)

    def detect(self, frame):
        if self.model is None:
            return DetectionResult(frame=frame, count=0)

        count = 0
        original_frame = frame.copy()
        results = self.model(frame, verbose=False)
        names = self.model.names

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                name = names[cls]
                if name not in self.vehicle_classes:
                    continue

                count += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                if self.capture_saver is not None:
                    self.capture_saver.save_crop(original_frame, name, x1, y1, x2, y2)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(frame, f"{name} {conf:.2f}", (x1, y1 - 5), 0, 1, (255, 255, 0), 2)

        return DetectionResult(frame=frame, count=count)
