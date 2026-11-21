from typing import Dict, List, Tuple
import cv2
from core.analyzer import detect_face_anchor


def build_zoom_keyframes(
    video_path: str,
    transitions: List[float],
    clip_duration: float,
    zoom_scale: float = 1.22,
    mode: str = "punch",
    face_tracking: bool = True,
    ramp_duration: float = 0.35,
) -> List[Dict]:
    """Gera a lista cronológica de keyframes reutilizando uma única leitura de vídeo."""
    keyframes: List[Dict] = []
    zoomed_in = False

    cap = cv2.VideoCapture(video_path) if face_tracking else None
    try:
        for idx, t in enumerate(transitions):
            if t >= clip_duration:
                break

            if idx > 0:
                zoomed_in = not zoomed_in

            target_scale = zoom_scale if zoomed_in else 1.0
            if zoomed_in and face_tracking:
                anchor_x, anchor_y = detect_face_anchor(video_path, t + 0.1, cap=cap)
            else:
                anchor_x, anchor_y = 0.5, 0.5

            if mode == "punch" or idx == 0:
                if idx > 0 and t - 0.001 > keyframes[-1]["time"]:
                    prev = keyframes[-1]
                    keyframes.append({
                        "time": round(t - 0.001, 3),
                        "scale": prev["scale"],
                        "anchor_x": prev["anchor_x"],
                        "anchor_y": prev["anchor_y"],
                        "easing": "hold",
                    })

                keyframes.append({
                    "time": t,
                    "scale": target_scale,
                    "anchor_x": anchor_x,
                    "anchor_y": anchor_y,
                    "easing": "hold",
                })
            else:
                ramp_start = max(0.0, round(t - ramp_duration, 3))
                if ramp_start > keyframes[-1]["time"]:
                    prev = keyframes[-1]
                    keyframes.append({
                        "time": ramp_start,
                        "scale": prev["scale"],
                        "anchor_x": prev["anchor_x"],
                        "anchor_y": prev["anchor_y"],
                        "easing": "ease_in_out",
                    })

                keyframes.append({
                    "time": t,
                    "scale": target_scale,
                    "anchor_x": anchor_x,
                    "anchor_y": anchor_y,
                    "easing": "ease_in_out",
                })
    finally:
        if cap is not None:
            cap.release()

    return keyframes


def interpolate_state(keyframes: List[Dict], current_time: float) -> Tuple[float, float, float]:
    """Calcula escala e ponto de ancoragem (x, y) exatos para o instante atual."""
    if not keyframes:
        return 1.0, 0.5, 0.5

    if current_time <= keyframes[0]["time"]:
        kf = keyframes[0]
        return kf["scale"], kf["anchor_x"], kf["anchor_y"]

    if current_time >= keyframes[-1]["time"]:
        kf = keyframes[-1]
        return kf["scale"], kf["anchor_x"], kf["anchor_y"]

    for i in range(len(keyframes) - 1):
        kf_curr = keyframes[i]
        kf_next = keyframes[i + 1]

        if kf_curr["time"] <= current_time < kf_next["time"]:
            if kf_next["easing"] == "hold":
                return kf_curr["scale"], kf_curr["anchor_x"], kf_curr["anchor_y"]

            span = kf_next["time"] - kf_curr["time"]
            t = (current_time - kf_curr["time"]) / span if span > 0 else 1.0
            smooth_t = t * t * (3.0 - 2.0 * t)

            scale = kf_curr["scale"] + (kf_next["scale"] - kf_curr["scale"]) * smooth_t
            ax = kf_curr["anchor_x"] + (kf_next["anchor_x"] - kf_curr["anchor_x"]) * smooth_t
            ay = kf_curr["anchor_y"] + (kf_next["anchor_y"] - kf_curr["anchor_y"]) * smooth_t
            return scale, ax, ay

    last = keyframes[-1]
    return last["scale"], last["anchor_x"], last["anchor_y"]


def compute_crop_rect(
    width: int,
    height: int,
    scale: float,
    anchor_x: float,
    anchor_y: float,
) -> Tuple[int, int, int, int]:
    """Retorna (x1, y1, crop_w, crop_h) garantindo limites válidos dentro do frame."""
    if scale <= 1.001:
        return 0, 0, width, height

    crop_w = max(2, int(round(width / scale)))
    crop_h = max(2, int(round(height / scale)))

    cx = anchor_x * width
    cy = anchor_y * height

    x1 = max(0, min(width - crop_w, int(round(cx - crop_w / 2.0))))
    y1 = max(0, min(height - crop_h, int(round(cy - crop_h / 2.0))))
    return x1, y1, crop_w, crop_h