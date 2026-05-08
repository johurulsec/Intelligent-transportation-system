from dataclasses import dataclass
import math


@dataclass
class Track:
    track_id: int
    label: str
    box: tuple[int, int, int, int]
    center: tuple[int, int]
    missed_frames: int = 0


class VehicleTracker:
    def __init__(self, max_distance=80.0, max_missed_frames=10):
        self.max_distance = max_distance
        self.max_missed_frames = max_missed_frames
        self._next_track_id = 1
        self._tracks = {}
        self._total_tracks_created = 0

    @property
    def active_track_count(self):
        return len(self._tracks)

    @property
    def total_tracks_created(self):
        return self._total_tracks_created

    def update(self, detections):
        assignments = []
        unmatched_detection_indexes = set(range(len(detections)))
        track_ids = list(self._tracks.keys())
        available_track_ids = set(track_ids)
        candidate_pairs = []

        for detection_index, detection in enumerate(detections):
            detection_center = self._get_center(detection["box"])
            for track_id in track_ids:
                track = self._tracks[track_id]
                if track.label != detection["label"]:
                    continue
                distance = self._distance(track.center, detection_center)
                if distance <= self.max_distance:
                    candidate_pairs.append((distance, track_id, detection_index))

        candidate_pairs.sort(key=lambda item: item[0])

        for _, track_id, detection_index in candidate_pairs:
            if track_id not in available_track_ids or detection_index not in unmatched_detection_indexes:
                continue

            detection = detections[detection_index]
            track = self._tracks[track_id]
            track.box = detection["box"]
            track.center = self._get_center(detection["box"])
            track.missed_frames = 0
            assignments.append(self._build_assignment(track, detection))
            available_track_ids.remove(track_id)
            unmatched_detection_indexes.remove(detection_index)

        for detection_index in sorted(unmatched_detection_indexes):
            detection = detections[detection_index]
            track = self._create_track(detection["label"], detection["box"])
            assignments.append(self._build_assignment(track, detection))

        stale_track_ids = []
        for track_id in available_track_ids:
            track = self._tracks[track_id]
            track.missed_frames += 1
            if track.missed_frames > self.max_missed_frames:
                stale_track_ids.append(track_id)

        for track_id in stale_track_ids:
            del self._tracks[track_id]

        assignments.sort(key=lambda item: item["track_id"])
        return assignments

    @staticmethod
    def _distance(point_a, point_b):
        return math.hypot(point_a[0] - point_b[0], point_a[1] - point_b[1])

    @staticmethod
    def _get_center(box):
        x1, y1, x2, y2 = box
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def _create_track(self, label, box):
        track = Track(
            track_id=self._next_track_id,
            label=label,
            box=box,
            center=self._get_center(box),
        )
        self._tracks[track.track_id] = track
        self._next_track_id += 1
        self._total_tracks_created += 1
        return track

    @staticmethod
    def _build_assignment(track, detection):
        return {
            "track_id": track.track_id,
            "label": detection["label"],
            "box": detection["box"],
            "confidence": detection["confidence"],
        }
