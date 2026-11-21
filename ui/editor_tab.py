import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from core.analyzer import detect_speech_transitions, get_video_metadata
from core.preview_engine import PreviewEngine
from core.renderer import render_zoomed_video
from core.zoom_engine import build_zoom_keyframes
from ui.theme import MacButton, MacTheme, MacToggle


class EditorTab(tk.Frame):
    """Aba principal de configuração de arquivos, parâmetros e exportação."""

    STYLE_MAP = {
        "Corte Seco (Punch)": "punch",
        "Suave (Smooth)": "smooth",
    }

    def __init__(
        self,
        parent: tk.Widget,
        on_video_selected: Callable[[str], None],
        on_params_changed: Callable[[], None],
        on_open_preview: Callable[[], None],
    ):
        super().__init__(parent, bg=MacTheme.BG_WINDOW)
        self.on_video_selected = on_video_selected
        self.on_params_changed = on_params_changed
        self.on_open_preview = on_open_preview

        self.input_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.mode_label_var = tk.StringVar(value="Corte Seco (Punch)")
        self.scale_var = tk.DoubleVar(value=1.22)
        self.interval_var = tk.DoubleVar(value=3.5)
        self.face_lock_var = tk.BooleanVar(value=True)
        self.full_video_var = tk.BooleanVar(value=True)

        self.mode_label_var.trace_add("write", lambda *_: self.on_params_changed())
        self.scale_var.trace_add("write", lambda *_: self.on_params_changed())
        self.interval_var.trace_add("write", lambda *_: self.on_params_changed())

        self._build_ui()

    def get_settings(self) -> dict:
        return {
            "input_path": self.input_path_var.get().strip(),
            "output_path": self.output_path_var.get().strip(),
            "mode": self.STYLE_MAP.get(self.mode_label_var.get(), "punch"),
            "zoom_scale": float(self.scale_var.get()),
            "min_interval": float(self.interval_var.get()),
            "face_tracking": bool(self.face_lock_var.get()),
            "full_video": bool(self.full_video_var.get()),
        }

    def _create_section(self, title: str) -> tk.Frame:
        wrapper = tk.Frame(self, bg=MacTheme.BG_WINDOW)
        wrapper.pack(fill="x", pady=(0, 12))

        tk.Label(
            wrapper,
            text=title.upper(),
            bg=MacTheme.BG_WINDOW,
            fg=MacTheme.TEXT_SECONDARY,
            font=(MacTheme.FONT_FAMILY, 8, "bold"),
        ).pack(anchor="w", pady=(0, 4), padx=4)

        card = tk.Frame(
            wrapper,
            bg=MacTheme.BG_CARD,
            highlightbackground=MacTheme.BORDER,
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        card.pack(fill="x")
        return card

    def _build_ui(self):
        # Seção 1: Arquivos
        files_card = self._create_section("Arquivos")
        self._build_path_field(
            files_card,
            label="Vídeo Original",
            var=self.input_path_var,
            btn_text="Escolher...",
            command=self._browse_input,
        )
        self._build_path_field(
            files_card,
            label="Onde Salvar",
            var=self.output_path_var,
            btn_text="Salvar como...",
            command=self._browse_output,
            top_pad=10,
        )

        # Seção 2: Ajustes de Câmera e Exportação
        cam_card = self._create_section("Ajustes de Câmera e Exportação")

        grid = tk.Frame(cam_card, bg=MacTheme.BG_CARD)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=2)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)

        tk.Label(
            grid,
            text="Estilo de Movimento",
            bg=MacTheme.BG_CARD,
            fg=MacTheme.TEXT_PRIMARY,
            font=(MacTheme.FONT_FAMILY, 9),
        ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 4))

        ttk.Combobox(
            grid,
            textvariable=self.mode_label_var,
            values=list(self.STYLE_MAP.keys()),
            state="readonly",
            style="Mac.TCombobox",
        ).grid(row=1, column=0, sticky="ew", padx=(0, 10))

        tk.Label(
            grid,
            text="Zoom (1.1x - 1.6x)",
            bg=MacTheme.BG_CARD,
            fg=MacTheme.TEXT_PRIMARY,
            font=(MacTheme.FONT_FAMILY, 9),
        ).grid(row=0, column=1, sticky="w", padx=(0, 10), pady=(0, 4))

        ttk.Spinbox(
            grid,
            from_=1.10,
            to=1.60,
            increment=0.02,
            textvariable=self.scale_var,
            style="Mac.TSpinbox",
            width=7,
        ).grid(row=1, column=1, sticky="ew", padx=(0, 10))

        tk.Label(
            grid,
            text="Intervalo (seg)",
            bg=MacTheme.BG_CARD,
            fg=MacTheme.TEXT_PRIMARY,
            font=(MacTheme.FONT_FAMILY, 9),
        ).grid(row=0, column=2, sticky="w", pady=(0, 4))

        ttk.Spinbox(
            grid,
            from_=1.5,
            to=10.0,
            increment=0.5,
            textvariable=self.interval_var,
            style="Mac.TSpinbox",
            width=7,
        ).grid(row=1, column=2, sticky="ew")

        tk.Frame(cam_card, bg=MacTheme.BORDER, height=1).pack(fill="x", pady=10)

        # Toggle 1: Face Lock
        face_row = tk.Frame(cam_card, bg=MacTheme.BG_CARD)
        face_row.pack(fill="x")

        tk.Label(
            face_row,
            text="Centralizar no rosto automaticamente (Face Lock)",
            bg=MacTheme.BG_CARD,
            fg=MacTheme.TEXT_PRIMARY,
            font=(MacTheme.FONT_FAMILY, 9),
        ).pack(side="left")

        MacToggle(
            face_row,
            variable=self.face_lock_var,
            command=self.on_params_changed,
            bg_parent=MacTheme.BG_CARD,
        ).pack(side="right")

        tk.Frame(cam_card, bg=MacTheme.BORDER, height=1).pack(fill="x", pady=10)

        # Toggle 2: Vídeo completo vs Prévia 30s
        export_mode_row = tk.Frame(cam_card, bg=MacTheme.BG_CARD)
        export_mode_row.pack(fill="x")

        label_stack = tk.Frame(export_mode_row, bg=MacTheme.BG_CARD)
        label_stack.pack(side="left")

        tk.Label(
            label_stack,
            text="Exportar vídeo completo",
            bg=MacTheme.BG_CARD,
            fg=MacTheme.TEXT_PRIMARY,
            font=(MacTheme.FONT_FAMILY, 9),
        ).pack(anchor="w")

        self.export_hint_label = tk.Label(
            label_stack,
            text="Ativado: exporta toda a duração • Desativado: apenas 30s",
            bg=MacTheme.BG_CARD,
            fg=MacTheme.TEXT_SECONDARY,
            font=(MacTheme.FONT_FAMILY, 8),
        )
        self.export_hint_label.pack(anchor="w")

        MacToggle(
            export_mode_row,
            variable=self.full_video_var,
            command=self._update_export_mode_hint,
            bg_parent=MacTheme.BG_CARD,
        ).pack(side="right")

        # Seção 3: Progresso e Botões de Ação
        status_row = tk.Frame(self, bg=MacTheme.BG_WINDOW)
        status_row.pack(fill="x", pady=(2, 5), padx=2)

        self.status_label = tk.Label(
            status_row,
            text="Selecione o vídeo original para começar.",
            bg=MacTheme.BG_WINDOW,
            fg=MacTheme.TEXT_SECONDARY,
            font=(MacTheme.FONT_FAMILY, 9),
        )
        self.status_label.pack(side="left")

        self.pct_label = tk.Label(
            status_row,
            text="0%",
            bg=MacTheme.BG_WINDOW,
            fg=MacTheme.TEXT_SECONDARY,
            font=(MacTheme.FONT_FAMILY, 9, "bold"),
        )
        self.pct_label.pack(side="right")

        self.progress = ttk.Progressbar(
            self,
            mode="determinate",
            maximum=100,
            style="Mac.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x", pady=(0, 12))

        actions = tk.Frame(self, bg=MacTheme.BG_WINDOW)
        actions.pack(fill="x")

        self.preview_btn = MacButton(
            actions,
            text="Pré-visualizar (30s)",
            command=self.on_open_preview,
            primary=False,
            width=165,
            height=38,
            bg_parent=MacTheme.BG_WINDOW,
        )
        self.preview_btn.pack(side="left", padx=(0, 10))

        self.run_btn = MacButton(
            actions,
            text="Exportar Vídeo Completo",
            command=self._start_processing,
            primary=True,
            width=340,
            height=38,
            bg_parent=MacTheme.BG_WINDOW,
        )
        self.run_btn.pack(side="right", fill="x", expand=True)

    def _update_export_mode_hint(self):
        if self.full_video_var.get():
            self.run_btn.set_text("Exportar Vídeo Completo")
        else:
            self.run_btn.set_text("Exportar Trecho (30s)")

    def _build_path_field(
        self,
        parent: tk.Frame,
        label: str,
        var: tk.StringVar,
        btn_text: str,
        command: Callable,
        top_pad: int = 0,
    ):
        tk.Label(
            parent,
            text=label,
            bg=MacTheme.BG_CARD,
            fg=MacTheme.TEXT_PRIMARY,
            font=(MacTheme.FONT_FAMILY, 9, "bold"),
        ).pack(anchor="w", pady=(top_pad, 4))

        row = tk.Frame(parent, bg=MacTheme.BG_CARD)
        row.pack(fill="x")

        entry = tk.Entry(
            row,
            textvariable=var,
            bg=MacTheme.BG_CONTROL,
            fg=MacTheme.TEXT_PRIMARY,
            insertbackground=MacTheme.TEXT_PRIMARY,
            relief="flat",
            highlightbackground=MacTheme.BORDER,
            highlightthickness=1,
            font=(MacTheme.FONT_FAMILY, 9),
        )
        entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))

        MacButton(
            row,
            text=btn_text,
            command=command,
            primary=False,
            width=112,
            height=31,
            bg_parent=MacTheme.BG_CARD,
        ).pack(side="right")

    def _browse_input(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o vídeo original",
            filetypes=[("Arquivos de Vídeo", "*.mp4 *.mov *.mkv *.avi *.webm")],
        )
        if not file_path:
            return

        self.input_path_var.set(file_path)
        src = Path(file_path)
        self.output_path_var.set(str(src.with_name(f"{src.stem}_zoom.mp4")))
        self.status_label.config(
            text="Vídeo carregado. Abra a prévia de 30s ou exporte.",
            fg=MacTheme.TEXT_SECONDARY,
        )
        self.on_video_selected(file_path)

    def _browse_output(self):
        current_out = self.output_path_var.get().strip()
        initial_dir = str(Path(current_out).parent) if current_out else str(Path.home())
        initial_file = Path(current_out).name if current_out else "video_zoom.mp4"

        file_path = filedialog.asksaveasfilename(
            title="Escolha onde salvar o vídeo final",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".mp4",
            filetypes=[("Vídeo MP4", "*.mp4")],
        )
        if file_path:
            self.output_path_var.set(file_path)

    def _set_status(self, text: str, pct: int = None, is_error: bool = False):
        color = MacTheme.RED if is_error else MacTheme.TEXT_SECONDARY
        self.status_label.config(text=text, fg=color)
        if pct is not None:
            self.progress["value"] = pct
            self.pct_label.config(text=f"{pct}%")

    def _start_processing(self):
        cfg = self.get_settings()
        input_path = cfg["input_path"]
        output_path = cfg["output_path"]

        if not input_path or not Path(input_path).is_file():
            messagebox.showwarning("Arquivo inválido", "Selecione um arquivo de vídeo original válido.")
            return

        if not output_path:
            messagebox.showwarning("Destino inválido", "Escolha onde deseja salvar o vídeo final.")
            return

        if not output_path.lower().endswith(".mp4"):
            output_path += ".mp4"
            self.output_path_var.set(output_path)

        if Path(input_path).resolve() == Path(output_path).resolve():
            messagebox.showerror(
                "Caminho inválido",
                "O arquivo de destino não pode ter o mesmo nome e pasta do vídeo original.",
            )
            return

        self.run_btn.set_enabled(False)
        self.run_btn.set_text("Processando...")
        self.preview_btn.set_enabled(False)
        self._set_status("Analisando pausas na fala...", pct=0)

        worker = threading.Thread(
            target=self._export_worker,
            args=(
                input_path,
                output_path,
                cfg["zoom_scale"],
                cfg["min_interval"],
                cfg["mode"],
                cfg["face_tracking"],
                cfg["full_video"],
            ),
            daemon=True,
        )
        worker.start()

    def _export_worker(
        self,
        input_path: str,
        output_path: str,
        zoom_scale: float,
        min_interval: float,
        mode: str,
        face_tracking: bool,
        full_video: bool,
    ):
        try:
            _, _, _, _, full_duration = get_video_metadata(input_path)
            target_duration = (
                full_duration if full_video else min(full_duration, PreviewEngine.PREVIEW_LIMIT)
            )
            max_dur_arg = None if full_video else target_duration

            transitions = detect_speech_transitions(
                input_path,
                min_interval=min_interval,
                max_duration=max_dur_arg,
            )

            self.after(
                0,
                lambda: self._set_status("Rastreando rosto e calculando cortes...", pct=5),
            )

            keyframes = build_zoom_keyframes(
                video_path=input_path,
                transitions=transitions,
                clip_duration=target_duration,
                zoom_scale=zoom_scale,
                mode=mode,
                face_tracking=face_tracking,
            )

            def on_progress(pct: int):
                msg = (
                    "Finalizando áudio e compressão H.264..."
                    if 97 <= pct < 100
                    else "Renderizando vídeo com zoom..."
                )
                self.after(0, lambda p=pct, m=msg: self._set_status(m, pct=p))

            render_zoomed_video(
                input_path=input_path,
                output_path=output_path,
                keyframes=keyframes,
                max_duration=max_dur_arg,
                progress_callback=on_progress,
            )
            self.after(0, lambda: self._on_export_success(output_path))
        except Exception as exc:
            err = str(exc)
            self.after(0, lambda: self._on_export_error(err))

    def _on_export_success(self, output_path: str):
        self._set_status("Concluído! Vídeo exportado com sucesso.", pct=100)
        self.run_btn.set_enabled(True)
        self._update_export_mode_hint()
        self.preview_btn.set_enabled(True)
        messagebox.showinfo(
            "Exportação Concluída",
            f"Vídeo salvo em:\n{output_path}\n\nPronto para ser importado no seu editor de vídeo.",
        )

    def _on_export_error(self, err_msg: str):
        self._set_status("Falha ao processar o vídeo.", is_error=True)
        self.run_btn.set_enabled(True)
        self._update_export_mode_hint()
        self.preview_btn.set_enabled(True)
        messagebox.showerror("Erro no Processamento", err_msg)