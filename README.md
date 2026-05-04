# Intelligent Transportation System

A desktop traffic-monitoring application built with Python, PyQt5, OpenCV, and Ultralytics YOLO. The app plays a video stream, detects vehicles, shows a live dashboard, saves cropped vehicle images into date-wise and vehicle-wise folders, and logs saved captures into SQLite.

## Features

- Live video monitoring with a PyQt5 desktop interface
- Vehicle detection using YOLO
- Vehicle counting for common road vehicles:
  - `car`
  - `bus`
  - `truck`
  - `motorcycle`
  - `bicycle`
- Vehicle image crop saving without bounding boxes in the saved file
- Automatic folder creation by date and vehicle type
- Automatic SQLite logging for each saved image

## Project Structure

```text
ITS/
|-- main.py
|-- traffic_config.py
|-- traffic_main_window.py
|-- traffic_ui.py
|-- traffic_detector.py
|-- traffic_capture.py
|-- traffic_database.py
|-- requirements.txt
|-- README.md
|-- .venv/
```

## Requirements

- Windows
- Python 3.10+
- A valid YOLO model file
- A source video file

## Default Paths

These paths are configured in [traffic_config.py](/C:/Users/HP/Documents/ITS/traffic_config.py):

- Video file: `d:\its-info\sample-vehicle2.mp4`
- YOLO model: `d:\its-info\yolov8n.pt`
- Capture folder: `d:\its-info\capture_vehicles`
- Database file: `d:\its-info\transport.db`

Update those paths if your files are stored somewhere else.

## Setup

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### 2. Install dependencies

Install the general packages:

```powershell
python -m pip install -r requirements.txt
```

If PyTorch needs a CPU-only install, use:

```powershell
python -m pip install torch==2.5.1+cpu torchvision==0.20.1+cpu torchaudio==2.5.1+cpu --index-url https://download.pytorch.org/whl/cpu
```

### 3. Make sure the input files exist

Place these files in the configured locations:

- `d:\its-info\sample-vehicle2.mp4`
- `d:\its-info\yolov8n.pt`

## Run

Start the application with:

```powershell
.\.venv\Scripts\python main.py
```

## Capture Output

Saved vehicle images follow this structure:

```text
d:\its-info\capture_vehicles\dd-mm-yyyy\vehicle_type\hh-mm-ss-fff.png
```

Example:

```text
d:\its-info\capture_vehicles\04-05-2026\car\23-01-15-123.png
```

Notes:

- The saved image is the cropped vehicle only
- The saved image does not include the drawn bounding box
- Folders are created automatically if they do not exist

## Database Logging

The app automatically creates the SQLite database file if it does not exist:

```text
d:\its-info\transport.db
```

Database behavior:

- One table per vehicle type
- Example table names:
  - `car`
  - `bus`
  - `truck`
  - `motorcycle`
  - `bicycle`

Each vehicle table stores:

- `id`
- `vehicle_type`
- `image_name`
- `image_path`
- `captured_at`

## Current Architecture

### `main.py`

Application entry point.

### `traffic_config.py`

Application settings and file paths.

### `traffic_main_window.py`

Main PyQt window, layout, timer loop, and startup validation.

### `traffic_ui.py`

Reusable UI widgets like the video tile and dashboard cards.

### `traffic_detector.py`

YOLO model loading and vehicle detection logic.

### `traffic_capture.py`

Vehicle crop saving logic and output folder management.

### `traffic_database.py`

SQLite logging for saved vehicle images.

## Notes About the Current Process

The current process is valid for a small desktop project and is much better structured now than a single-file prototype. A few design choices to keep in mind:

- The app uses per-vehicle-type save cooldown logic to reduce duplicate image saving
- The preview window shows bounding boxes, but saved captures do not
- The database uses one table per vehicle type because that matches the current requirement

For a larger production system, a single unified capture table and proper vehicle tracking would usually be stronger choices.

## Troubleshooting

### PyTorch / YOLO import error

If you see a DLL or `torch` loading error:

- use the local virtual environment
- reinstall PyTorch CPU wheels
- make sure the Microsoft Visual C++ runtime is installed on Windows

### Model file missing

If the app says the model is missing, confirm:

- `d:\its-info\yolov8n.pt` exists

### Video file missing

If the app says the video is missing, confirm:

- `d:\its-info\sample-vehicle2.mp4` exists

## Future Improvements

- Add a proper vehicle tracker to reduce repeated saves for the same vehicle
- Add search and reporting for capture history
- Add configuration through environment variables or a `.json` config file
- Add tests for database logging and capture saving
