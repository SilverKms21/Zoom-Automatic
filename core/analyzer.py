import os
import re
import subprocess
from typing import List, Optional, Tuple
import cv2


def get_video_metadata(video_path: str) -> Tuple[float, int, int, int, float]:
    """Retorna (fps, largura, altura, total_frames, duracao_segundos) do vídeo."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Não foi possível abrir o vídeo: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    duration = round(total_frames / fps, 3) if fps > 0 else 0.0
    return fps, width, height, total_frames, duration


def detect_speech_transitions(
    media_path: str,
    min_interval: float = 3.5,
    noise_db: str = "-32dB",
    min_silence: float = 0.25,
    max_duration: Optional[float] = None,
) -> List[float]:
    """Detecta pausas na fala via FFmpeg (opcionalmente limitado a max_duration segundos)."""
    cmd = ["ffmpeg"]
    if max_duration is not None and max_duration > 0:
        cmd.extend(["-t", f"{max_duration:.3f}"])

    cmd.extend([
        "-i", media_path,
        "-af", f"silencedetect=noise={noise_db}:d={min_silence}",
        "-f", "null", "-",
    ])

    try:
        result = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True,
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
        if max_duration is not None and t >= max_duration:
            break
        if t - transitions[-1] >= min_interval:
            transitions.append(round(t, 3))

    return transitions


def detect_face_anchor(
    video_path: str,
    timestamp: float,
    cap: Optional[cv2.VideoCapture] = None,
) -> Tuple[float, float]:
    """Retorna o centro normalizado (x, y) do maior rosto detectado no timestamp."""
    if not hasattr(cv2, "CascadeClassifier"):
        return 0.5, 0.42

    own_cap = cap is None
    if own_cap:
        cap = cv2.VideoCapture(video_path)

    try:
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000.0)
        ok, frame = cap.read()
    finally:
        if own_cap and cap is not None:
            cap.release()

    if not ok or frame is None:
        return 0.5, 0.42

    cascade_dir = getattr(getattr(cv2, "data", None), "haarcascades", "")
    cascade_path = os.path.join(cascade_dir, "haarcascade_frontalface_default.xml")
    if not os.path.exists(cascade_path):
        return 0.5, 0.42

    # Reduz a resolução apenas para a detecção facial (muito mais rápido em 1080p/4K)
    orig_h, orig_w = frame.shape[:2]
    detect_w = min(orig_w, 480)
    scale_ratio = detect_w / float(orig_w)
    detect_h = max(2, int(round(orig_h * scale_ratio)))

    small_gray = cv2.cvtColor(
        cv2.resize(frame, (detect_w, detect_h), interpolation=cv2.INTER_AREA),
        cv2.COLOR_BGR2GRAY,
    )

    min_face = max(24, int(round(60 * scale_ratio)))
    face_cascade = cv2.CascadeClassifier(cascade_path)
    faces = face_cascade.detectMultiScale(
        small_gray,
        scaleFactor=1.15,
        minNeighbors=5,
        minSize=(min_face, min_face),
    )
    if len(faces) == 0:
        return 0.5, 0.42

    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    center_x = round((x + w / 2.0) / detect_w, 4)
    center_y = round((y + h / 2.0) / detect_h, 4)
    return center_x, center_y