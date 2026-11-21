import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Dict, List, Optional
import cv2

from core.zoom_engine import compute_crop_rect, interpolate_state


def render_zoomed_video(
    input_path: str,
    output_path: str,
    keyframes: List[Dict],
    max_duration: Optional[float] = None,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> str:
    """
    Renderiza o vídeo em H.264 com o zoom aplicado e mantém o áudio original.
    Se max_duration=None, exporta o vídeo completo; caso contrário, limita à duração informada.
    """
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Não foi possível abrir o vídeo: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    raw_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if max_duration is not None and max_duration > 0:
        max_frames = int(round(max_duration * fps))
        target_frames = min(raw_frames, max_frames) if raw_frames > 0 else max_frames
    else:
        target_frames = raw_frames

    temp_video = str(Path(tempfile.gettempdir()) / "zoom_automatic_silent.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))

    frame_idx = 0
    while True:
        if max_duration is not None and frame_idx >= target_frames:
            break

        ok, frame = cap.read()
        if not ok:
            break

        current_time = frame_idx / fps
        scale, anchor_x, anchor_y = interpolate_state(keyframes, current_time)

        if scale > 1.001:
            x1, y1, crop_w, crop_h = compute_crop_rect(width, height, scale, anchor_x, anchor_y)
            cropped = frame[y1 : y1 + crop_h, x1 : x1 + crop_w]
            frame = cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LANCZOS4)

        writer.write(frame)
        frame_idx += 1

        if progress_callback and target_frames > 0 and frame_idx % 10 == 0:
            pct = min(95, int((frame_idx / target_frames) * 95))
            progress_callback(pct)

    cap.release()
    writer.release()

    if progress_callback:
        progress_callback(97)

    cmd = ["ffmpeg", "-y", "-i", temp_video]
    if max_duration is not None and max_duration > 0:
        cmd.extend(["-t", f"{max_duration:.3f}"])
    cmd.extend([
        "-i", input_path,
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0?",
        "-shortest",
        output_path,
    ])

    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as err:
        raise RuntimeError(f"Erro ao finalizar vídeo no FFmpeg:\n{err.stderr}")
    finally:
        if os.path.exists(temp_video):
            os.remove(temp_video)

    if progress_callback:
        progress_callback(100)

    return output_path