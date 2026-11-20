import os
import subprocess
import tempfile
from pathlib import Path
import cv2


def _interpolate_state(keyframes: list[dict], current_time: float) -> tuple[float, float, float]:
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


def render_zoomed_video(
    input_path: str,
    output_path: str,
    keyframes: list[dict],
    progress_callback=None
) -> str:
    """Renderiza um novo .mp4 com o AutoZoom aplicado e mantém o áudio original."""
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Não foi possível abrir o vídeo: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    temp_video = str(Path(tempfile.gettempdir()) / "fc_autozoom_silent.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))

    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        current_time = frame_idx / fps
        scale, anchor_x, anchor_y = _interpolate_state(keyframes, current_time)

        if scale > 1.001:
            crop_w = int(round(width / scale))
            crop_h = int(round(height / scale))

            cx = anchor_x * width
            cy = anchor_y * height

            x1 = max(0, min(width - crop_w, int(round(cx - crop_w / 2.0))))
            y1 = max(0, min(height - crop_h, int(round(cy - crop_h / 2.0))))

            cropped = frame[y1:y1 + crop_h, x1:x1 + crop_w]
            frame = cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LANCZOS4)

        writer.write(frame)
        frame_idx += 1

        if progress_callback and total_frames > 0 and frame_idx % 10 == 0:
            pct = min(95, int((frame_idx / total_frames) * 95))
            progress_callback(pct)

    cap.release()
    writer.release()

    if progress_callback:
        progress_callback(97)

    cmd = [
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", input_path,
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0?",
        output_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as err:
        raise RuntimeError(f"Erro ao finalizar vídeo no FFmpeg:\n{err.stderr}")
    finally:
        if os.path.exists(temp_video):
            os.remove(temp_video)

    if progress_callback:
        progress_callback(100)

    return output_path
