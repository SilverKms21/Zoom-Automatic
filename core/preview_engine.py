import tkinter as tk
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np

from core.analyzer import detect_speech_transitions, get_video_metadata
from core.zoom_engine import build_zoom_keyframes, compute_crop_rect, interpolate_state


class PreviewEngine:
    """Pré-visualização otimizada com cache proxy em memória para os primeiros 30s."""

    PREVIEW_LIMIT = 30.0
    PREVIEW_FPS = 24.0

    def __init__(self, max_width: int = 560, max_height: int = 315):
        self.max_width = max_width
        self.max_height = max_height
        self.video_path: Optional[str] = None

        self.fps: float = 30.0
        self.effective_fps: float = 24.0
        self.width: int = 0
        self.height: int = 0
        self.total_frames: int = 0
        self.full_duration: float = 0.0
        self.preview_duration: float = 0.0

        self.transitions: List[float] = [0.0]
        self.keyframes: List[Dict] = []
        self.proxy_frames: List[np.ndarray] = []

    def close(self):
        self.proxy_frames.clear()

    def load_video(self, video_path: str):
        self.close()
        self.video_path = video_path
        self.fps, self.width, self.height, self.total_frames, self.full_duration = (
            get_video_metadata(video_path)
        )
        self.preview_duration = min(self.full_duration, self.PREVIEW_LIMIT)
        self.effective_fps = min(self.PREVIEW_FPS, max(1.0, self.fps))
        self.transitions = [0.0]
        self.keyframes = []

    def _build_proxy_cache(self):
        """Lê os primeiros 30s em passagem única e guarda frames reduzidos em JPEG na RAM."""
        self.proxy_frames.clear()
        if not self.video_path or self.preview_duration <= 0:
            return

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            return

        try:
            frame_step = max(1.0, self.fps / self.effective_fps)
            max_raw_frames = int(round(self.preview_duration * self.fps))
            next_target = 0.0
            raw_idx = 0

            while raw_idx < max_raw_frames:
                if not cap.grab():
                    break

                if raw_idx >= int(round(next_target)):
                    ok, frame = cap.retrieve()
                    if ok and frame is not None:
                        small = self._fit_to_viewport(frame)
                        ok_enc, buf = cv2.imencode(
                            ".jpg", small, [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                        )
                        if ok_enc:
                            self.proxy_frames.append(buf)
                    next_target += frame_step

                raw_idx += 1
        finally:
            cap.release()

    def analyze_keyframes(
        self,
        zoom_scale: float,
        min_interval: float,
        mode: str,
        face_tracking: bool,
    ) -> Tuple[List[float], List[Dict]]:
        if not self.video_path:
            return [0.0], []

        if not self.proxy_frames:
            self._build_proxy_cache()

        self.transitions = detect_speech_transitions(
            self.video_path,
            min_interval=min_interval,
            max_duration=self.preview_duration,
        )
        self.keyframes = build_zoom_keyframes(
            video_path=self.video_path,
            transitions=self.transitions,
            clip_duration=self.preview_duration,
            zoom_scale=zoom_scale,
            mode=mode,
            face_tracking=face_tracking,
        )
        return self.transitions, self.keyframes

    def _fit_to_viewport(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        ratio = min(self.max_width / w, self.max_height / h)
        new_w = max(2, int(round(w * ratio)))
        new_h = max(2, int(round(h * ratio)))
        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    @staticmethod
    def _bgr_to_photoimage(frame_bgr: np.ndarray) -> tk.PhotoImage:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        header = f"P6 {w} {h} 255\n".encode("ascii")
        return tk.PhotoImage(data=header + rgb.tobytes(), format="PPM")

    def render_preview_frame(
        self,
        timestamp: float,
        show_guide: bool = False,
    ) -> Tuple[Optional[tk.PhotoImage], float, bool]:
        """Decodifica instantaneamente o frame do cache proxy e aplica o zoom/guia."""
        if not self.proxy_frames:
            return None, 1.0, False

        clamped_t = max(0.0, min(self.preview_duration, timestamp))
        idx = int(round(clamped_t * self.effective_fps))
        idx = max(0, min(len(self.proxy_frames) - 1, idx))

        preview = cv2.imdecode(self.proxy_frames[idx], cv2.IMREAD_COLOR)
        if preview is None:
            return None, 1.0, False

        ph, pw = preview.shape[:2]
        scale, anchor_x, anchor_y = interpolate_state(self.keyframes, clamped_t)
        x1, y1, crop_w, crop_h = compute_crop_rect(pw, ph, scale, anchor_x, anchor_y)

        if show_guide:
            if scale > 1.001:
                x2, y2 = x1 + crop_w, y1 + crop_h
                mask = np.zeros_like(preview)
                mask[y1:y2, x1:x2] = preview[y1:y2, x1:x2]
                preview = cv2.addWeighted(preview, 0.42, mask, 0.58, 0)

                cv2.rectangle(preview, (x1, y1), (x2, y2), (255, 132, 10), 2)
                cx = int(round(anchor_x * pw))
                cy = int(round(anchor_y * ph))
                cv2.drawMarker(
                    preview,
                    (cx, cy),
                    (88, 209, 48),
                    markerType=cv2.MARKER_CROSS,
                    markerSize=14,
                    thickness=2,
                )
        elif scale > 1.001:
            cropped = preview[y1 : y1 + crop_h, x1 : x1 + crop_w]
            preview = cv2.resize(cropped, (pw, ph), interpolation=cv2.INTER_LINEAR)

        return self._bgr_to_photoimage(preview), scale, True