import os

import cv2


class PlateOcrReader:
    def __init__(self, tesseract_cmd=None):
        self.engine_name = "Unavailable"
        self.tesseract_cmd = tesseract_cmd
        self._reader = None
        self._read_fn = None
        self._load_engine()

    @property
    def available(self):
        return self._read_fn is not None

    @property
    def status_text(self):
        return self.engine_name if self.available else "Unavailable"

    def read_text(self, plate_image):
        if self._read_fn is None:
            return None

        processed = self._preprocess(plate_image)
        text = self._read_fn(processed)
        return self._normalize_text(text)

    def _load_engine(self):
        try:
            import pytesseract

            self._configure_tesseract_command(pytesseract)
            self._reader = pytesseract
            self._read_fn = self._read_with_tesseract
            self.engine_name = "Tesseract (ben+eng)"
            return
        except Exception:
            pass

        try:
            import easyocr

            self._reader = easyocr.Reader(["en"], gpu=False)
            self._read_fn = self._read_with_easyocr
            self.engine_name = "EasyOCR (en fallback)"
        except Exception:
            self._reader = None
            self._read_fn = None
            self.engine_name = "Unavailable"

    def _configure_tesseract_command(self, pytesseract):
        candidates = []
        if self.tesseract_cmd:
            candidates.append(self.tesseract_cmd)
        candidates.extend(
            [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract",
            ]
        )

        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                pytesseract.pytesseract.tesseract_cmd = candidate
                return

    def _read_with_easyocr(self, image):
        results = self._reader.readtext(image, detail=0)
        if not results:
            return None
        return " ".join(results)

    def _read_with_tesseract(self, image):
        config = "--psm 7"
        return self._reader.image_to_string(image, lang="ben+eng", config=config)

    @staticmethod
    def _preprocess(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        enlarged = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        _, thresholded = cv2.threshold(enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresholded

    @staticmethod
    def _normalize_text(text):
        if not text:
            return None
        text = text.replace("\n", " ").strip()
        allowed = []
        for char in text:
            if char.isalnum() or char in {"-", " "}:
                allowed.append(char)
            elif "\u0980" <= char <= "\u09FF":
                allowed.append(char)

        cleaned = " ".join("".join(allowed).split())
        return cleaned or None
