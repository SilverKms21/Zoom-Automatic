import threading
import time
import tkinter as tk
from pathlib import Path
from typing import Callable, Optional

from core.preview_engine import PreviewEngine
from ui.theme import MacButton, MacTheme, MacTimeline, MacToggle


class PreviewTab(tk.Frame):
    """Aba de pré-visualização fluida limitada aos primeiros 30 segundos do vídeo."""

    def __init__(self, parent: tk.Widget, get_settings_callback: Callable[[], dict]):
        super().__init__(parent, bg=MacTheme.BG_WINDOW)
        self.get_settings = get_settings_callback
        self.engine = PreviewEngine(max_width=560, max_height=315)

        self.is_playing = False
        self.current_time = 0.0
        self.needs_reanalysis = True
        self._after_id: Optional[str] = None
        self._current_photo: Optional[tk.PhotoImage] = None
        self._canvas_image_id: Optional[int] = None

        self._play_start_wall = 0.0
        self._play_start_media = 0.0

        self.show_guide_var = tk.BooleanVar(value=False)
        self.show_guide_var.trace_add("write", lambda *_: self._render_single_frame())

        self._build_ui()

    def _build_ui(self):
        viewport_frame = tk.Frame(
            self,
            bg=MacTheme.BG_VIEWPORT,
            highlightbackground=MacTheme.BORDER,
            highlightthickness=1,
            height=318,
        )
        viewport_frame.pack(fill="x", pady=(0, 10))
        viewport_frame.pack_propagate(False)

        self.canvas = tk.Canvas(
            viewport_frame,
            bg=MacTheme.BG_VIEWPORT,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self._draw_placeholder("Selecione um vídeo na aba Configurar para pré-visualizar.")

        info_bar = tk.Frame(self, bg=MacTheme.BG_WINDOW)
        info_bar.pack(fill="x", pady=(0, 8), padx=2)

        self.time_label = tk.Label(
            info_bar,
            text="00:00.0 / 00:00.0",
            bg=MacTheme.BG_WINDOW,
            fg=MacTheme.TEXT_PRIMARY,
            font=(MacTheme.FONT_FAMILY, 9, "bold"),
        )
        self.time_label.pack(side="left")

        self.zoom_badge = tk.Label(
            info_bar,
            text="1.00x • Plano Aberto",
            bg=MacTheme.BG_CARD,
            fg=MacTheme.ACCENT,
            padx=8,
            pady=2,
            font=(MacTheme.FONT_FAMILY, 8, "bold"),
        )
        self.zoom_badge.pack(side="left", padx=8)

        self.clip_badge = tk.Label(
            info_bar,
            text="Prévia 30s",
            bg=MacTheme.BG_CARD,
            fg=MacTheme.TEXT_SECONDARY,
            padx=8,
            pady=2,
            font=(MacTheme.FONT_FAMILY, 8),
        )
        self.clip_badge.pack(side="left")

        MacToggle(
            info_bar,
            variable=self.show_guide_var,
            bg_parent=MacTheme.BG_WINDOW,
        ).pack(side="right")

        tk.Label(
            info_bar,
            text="Guia de Corte",
            bg=MacTheme.BG_WINDOW,
            fg=MacTheme.TEXT_SECONDARY,
            font=(MacTheme.FONT_FAMILY, 9),
        ).pack(side="right", padx=(0, 8))

        controls_card = tk.Frame(
            self,
            bg=MacTheme.BG_CARD,
            highlightbackground=MacTheme.BORDER,
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        controls_card.pack(fill="x")

        self.timeline = MacTimeline(
            controls_card,
            on_seek=self._on_timeline_seek,
            bg_parent=MacTheme.BG_CARD,
        )
        self.timeline.pack(fill="x", pady=(0, 8))

        btn_row = tk.Frame(controls_card, bg=MacTheme.BG_CARD)
        btn_row.pack(fill="x")

        self.prev_btn = MacButton(
            btn_row,
            text="⏮ Corte",
            command=self._jump_prev_cut,
            width=88,
            height=32,
            bg_parent=MacTheme.BG_CARD,
        )
        self.prev_btn.pack(side="left", padx=(0, 6))

        self.play_btn = MacButton(
            btn_row,
            text="▶ Reproduzir",
            command=self._toggle_play,
            primary=True,
            width=124,
            height=32,
            bg_parent=MacTheme.BG_CARD,
        )
        self.play_btn.pack(side="left", padx=(0, 6))

        self.next_btn = MacButton(
            btn_row,
            text="Corte ⏭",
            command=self._jump_next_cut,
            width=88,
            height=32,
            bg_parent=MacTheme.BG_CARD,
        )
        self.next_btn.pack(side="left")

        self.recalc_btn = MacButton(
            btn_row,
            text="↻ Recalcular",
            command=lambda: self.refresh_preview(force_reanalysis=True),
            width=106,
            height=32,
            bg_parent=MacTheme.BG_CARD,
        )
        self.recalc_btn.pack(side="right")

        self.status_hint = tk.Label(
            self,
            text="A prévia carrega os primeiros 30s em cache para reprodução instantânea.",
            bg=MacTheme.BG_WINDOW,
            fg=MacTheme.TEXT_SECONDARY,
            font=(MacTheme.FONT_FAMILY, 8),
        )
        self.status_hint.pack(anchor="w", pady=(8, 0), padx=2)

    def _draw_placeholder(self, message: str):
        self._canvas_image_id = None
        self.canvas.delete("all")
        w = max(300, self.canvas.winfo_width())
        h = max(180, self.canvas.winfo_height())
        self.canvas.create_text(
            w / 2,
            h / 2,
            text=message,
            fill=MacTheme.TEXT_SECONDARY,
            font=(MacTheme.FONT_FAMILY, 10),
        )

    def mark_dirty(self):
        self.needs_reanalysis = True

    def stop_playback(self):
        self.is_playing = False
        self.play_btn.set_text("▶ Reproduzir")
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

    def refresh_preview(self, force_reanalysis: bool = False):
        cfg = self.get_settings()
        input_path = cfg["input_path"]

        if not input_path or not Path(input_path).is_file():
            self.stop_playback()
            self._draw_placeholder("Nenhum vídeo selecionado. Escolha um arquivo na aba Configurar.")
            return

        video_changed = self.engine.video_path != input_path
        if video_changed:
            self.stop_playback()
            self.current_time = 0.0
            self.engine.load_video(input_path)
            self.needs_reanalysis = True

        if force_reanalysis or self.needs_reanalysis:
            self.stop_playback()
            self.recalc_btn.set_enabled(False)
            self.play_btn.set_enabled(False)
            msg = (
                "Preparando cache rápido de 30s e analisando cortes..."
                if not self.engine.proxy_frames
                else "Recalculando pontos de zoom..."
            )
            self._draw_placeholder(msg)

            worker = threading.Thread(
                target=self._analyze_worker,
                args=(
                    cfg["zoom_scale"],
                    cfg["min_interval"],
                    cfg["mode"],
                    cfg["face_tracking"],
                ),
                daemon=True,
            )
            worker.start()
        else:
            self._render_single_frame()

    def _analyze_worker(
        self,
        zoom_scale: float,
        min_interval: float,
        mode: str,
        face_tracking: bool,
    ):
        try:
            transitions, _ = self.engine.analyze_keyframes(
                zoom_scale=zoom_scale,
                min_interval=min_interval,
                mode=mode,
                face_tracking=face_tracking,
            )
            self.after(0, lambda: self._on_analysis_ready(transitions))
        except Exception as exc:
            err = str(exc)
            self.after(0, lambda: self._on_analysis_error(err))

    def _on_analysis_ready(self, transitions: list):
        self.needs_reanalysis = False
        self.recalc_btn.set_enabled(True)
        self.play_btn.set_enabled(True)

        p_dur = self.engine.preview_duration
        f_dur = self.engine.full_duration
        self.timeline.set_data(p_dur, transitions)
        self.timeline.set_time(self.current_time)

        if f_dur > p_dur + 0.1:
            self.clip_badge.config(text=f"Prévia 30s de {self._format_time(f_dur)}")
            self.status_hint.config(
                text=f"{len(transitions)} cortes nos primeiros 30s (vídeo total: {f_dur:.1f}s).",
                fg=MacTheme.TEXT_SECONDARY,
            )
        else:
            self.clip_badge.config(text="Vídeo completo")
            self.status_hint.config(
                text=f"{len(transitions)} pontos de transição detectados em {p_dur:.1f}s.",
                fg=MacTheme.TEXT_SECONDARY,
            )

        self._render_single_frame()

    def _on_analysis_error(self, err_msg: str):
        self.recalc_btn.set_enabled(True)
        self.play_btn.set_enabled(True)
        self._draw_placeholder(f"Erro ao gerar prévia:\n{err_msg}")

    @staticmethod
    def _format_time(sec: float) -> str:
        mins = int(sec // 60)
        rem = sec % 60
        return f"{mins:02d}:{rem:04.1f}"

    def _render_single_frame(self) -> bool:
        photo, scale, ok = self.engine.render_preview_frame(
            timestamp=self.current_time,
            show_guide=self.show_guide_var.get(),
        )
        if not ok or photo is None:
            return False

        self._current_photo = photo
        if self._canvas_image_id is None:
            self.canvas.delete("all")
            cw = max(10, self.canvas.winfo_width())
            ch = max(10, self.canvas.winfo_height())
            self._canvas_image_id = self.canvas.create_image(
                cw / 2, ch / 2, image=photo, anchor="center"
            )
        else:
            self.canvas.itemconfig(self._canvas_image_id, image=photo)

        self.time_label.config(
            text=f"{self._format_time(self.current_time)} / {self._format_time(self.engine.preview_duration)}"
        )
        if scale > 1.001:
            self.zoom_badge.config(text=f"{scale:.2f}x • Zoom Ativo", fg=MacTheme.GREEN)
        else:
            self.zoom_badge.config(text="1.00x • Plano Aberto", fg=MacTheme.ACCENT)
        return True

    def _on_timeline_seek(self, new_time: float):
        self.current_time = new_time
        if self.is_playing:
            self._play_start_wall = time.perf_counter()
            self._play_start_media = new_time
        self._render_single_frame()

    def _jump_prev_cut(self):
        if not self.engine.transitions:
            return
        prev_cuts = [t for t in self.engine.transitions if t < self.current_time - 0.15]
        self.current_time = prev_cuts[-1] if prev_cuts else 0.0
        self.timeline.set_time(self.current_time)
        if self.is_playing:
            self._play_start_wall = time.perf_counter()
            self._play_start_media = self.current_time
        self._render_single_frame()

    def _jump_next_cut(self):
        if not self.engine.transitions:
            return
        next_cuts = [t for t in self.engine.transitions if t > self.current_time + 0.15]
        self.current_time = next_cuts[0] if next_cuts else 0.0
        self.timeline.set_time(self.current_time)
        if self.is_playing:
            self._play_start_wall = time.perf_counter()
            self._play_start_media = self.current_time
        self._render_single_frame()

    def _toggle_play(self):
        if not self.engine.proxy_frames:
            return
        if self.is_playing:
            self.stop_playback()
        else:
            if self.current_time >= max(0.0, self.engine.preview_duration - 0.05):
                self.current_time = 0.0
                self._render_single_frame()
            self.is_playing = True
            self._play_start_wall = time.perf_counter()
            self._play_start_media = self.current_time
            self.play_btn.set_text("❚❚ Pausar")
            self._playback_tick()

    def _playback_tick(self):
        if not self.is_playing:
            return

        tick_begin = time.perf_counter()
        self.current_time = self._play_start_media + (tick_begin - self._play_start_wall)

        if self.current_time >= self.engine.preview_duration:
            self.current_time = self.engine.preview_duration
            self.timeline.set_time(self.current_time)
            self._render_single_frame()
            self.stop_playback()
            return

        self.timeline.set_time(self.current_time)
        if not self._render_single_frame():
            self.stop_playback()
            return

        frame_budget_ms = 1000.0 / self.engine.effective_fps
        render_cost_ms = (time.perf_counter() - tick_begin) * 1000.0
        delay_ms = max(8, int(round(frame_budget_ms - render_cost_ms)))
        self._after_id = self.after(delay_ms, self._playback_tick)