import os
import re
import subprocess
import cv2


def detect_speech_transitions(
    media_path: str,
    min_interval: float = 3.5,
    noise_db: str = "-32dB",
    min_silence: float = 0.25
) -> list[float]:
    """Detecta pausas na fala via FFmpeg para marcar os cortes de zoom."""
    cmd = [
        "ffmpeg", "-i", media_path,
        "-af", f"silencedetect=noise={noise_db}:d={min_silence}",
        "-f", "null", "-"
    ]
    try:
        result = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True
        )
    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg não encontrado no sistema. Instale com: sudo apt install ffmpeg"
        )

    silence_ends = [
        float(m) for m in re.findall(r"silence_end:\s*([0-9.]+)", result.stderr)
    ]

    transitions = [0.0]
    for t in silence_ends:
        if t - transitions[-1] >= min_interval:
            transitions.append(round(t, 3))

    return transitions


def detect_face_anchor(video_path: str, timestamp: float) -> tuple[float, float]:
    """Retorna o centro normalizado (x, y) do maior rosto detectado no timestamp."""
    if not hasattr(cv2, "CascadeClassifier"):
        return 0.5, 0.42

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000.0)
    ok, frame = cap.read()
    cap.release()

    if not ok or frame is None:
        return 0.5, 0.42

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cascade_dir = getattr(getattr(cv2, "data", None), "haarcascades", "")
    cascade_path = os.path.join(cascade_dir, "haarcascade_frontalface_default.xml")

    if not os.path.exists(cascade_path):
        return 0.5, 0.42

    face_cascade = cv2.CascadeClassifier(cascade_path)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.15,
        minNeighbors=5,
        minSize=(60, 60)
    )
    if len(faces) == 0:
        return 0.5, 0.42

    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    frame_h, frame_w = frame.shape[:2]

    center_x = round((x + w / 2.0) / frame_w, 4)
    center_y = round((y + h / 2.0) / frame_h, 4)
    return center_x, center_y
