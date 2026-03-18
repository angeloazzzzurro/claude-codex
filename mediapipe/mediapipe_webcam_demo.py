#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
from urllib.request import urlretrieve

import cv2
import mediapipe as mp


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_PATH = Path.home() / ".mediapipe" / "hand_landmarker.task"
OUTPUT_DIR = Path.home() / "Videos" / "mediapipe_demos"


def draw_task_landmarks(frame, hand_landmarks_list) -> None:
    from mediapipe.tasks.python import vision

    h, w = frame.shape[:2]
    for hand_landmarks in hand_landmarks_list:
        for connection in vision.HandLandmarksConnections.HAND_CONNECTIONS:
            p1 = hand_landmarks[connection.start]
            p2 = hand_landmarks[connection.end]
            x1, y1 = int(p1.x * w), int(p1.y * h)
            x2, y2 = int(p2.x * w), int(p2.y * h)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        for lm in hand_landmarks:
            x, y = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (x, y), 4, (0, 220, 0), -1)


def ensure_writer(writer, frame, output_path: Path, fps: float):
    if writer is not None:
        return writer
    h, w = frame.shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"Impossibile creare video: {output_path}")
    print(f"Registrazione video: {output_path}")
    return writer


def run_legacy_api(cap, output_path: Path, fps: float) -> None:
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles
    writer = None

    with mp_hands.Hands(
        model_complexity=0,
        max_num_hands=2,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    ) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_styles.get_default_hand_landmarks_style(),
                        mp_styles.get_default_hand_connections_style(),
                    )

            cv2.putText(frame, "Premi Q per uscire", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            writer = ensure_writer(writer, frame, output_path, fps)
            writer.write(frame)
            cv2.imshow("MediaPipe Hands Demo", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    if writer is not None:
        writer.release()


def run_tasks_api(cap, output_path: Path, fps: float) -> None:
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python import vision

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not MODEL_PATH.exists():
        print("Scarico modello hand_landmarker.task ...")
        urlretrieve(MODEL_URL, MODEL_PATH)

    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        num_hands=2,
    )
    writer = None
    with vision.HandLandmarker.create_from_options(options) as landmarker:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect(mp_image)

            if result.hand_landmarks:
                draw_task_landmarks(frame, result.hand_landmarks)

            cv2.putText(frame, "Premi Q per uscire", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            writer = ensure_writer(writer, frame, output_path, fps)
            writer.write(frame)
            cv2.imshow("MediaPipe Hands Demo", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    if writer is not None:
        writer.release()


def main() -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Webcam non disponibile (camera index 0).")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"hands_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps is None or fps <= 0:
        fps = 30.0

    try:
        if hasattr(mp, "solutions"):
            run_legacy_api(cap, output_path, fps)
        else:
            run_tasks_api(cap, output_path, fps)
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
