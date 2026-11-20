import glob
import sys
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
venv_sites = glob.glob(str(BASE_DIR / ".venv/lib/python*/site-packages"))
if venv_sites and venv_sites[0] not in sys.path:
    sys.path.insert(0, venv_sites[0])

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2

from analyzer import detect_speech_transitions
from zoom_engine import build_zoom_keyframes
from renderer import render_zoomed_video


class ZoomAutomaticApp:
    # Paleta Dark Studio
    BG_MAIN = "#121418"
    BG_CARD = "#1B1E24"
    BG_INPUT = "#252932"
    BORDER = "#2F3542"
    TEXT_PRIMARY = "#F3F4F6"
    TEXT_SECONDARY = "#9CA3AF"
    ACCENT = "#3B82F6"
    ACCENT_HOVER = "#2563EB"
    ACCENT_DISABLED = "#374151"

    STYLE_MAP = {
        "Corte Seco (Punch)": "punch",
        "Suave (Smooth)": "smooth",
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Zoom Automatic")
        self.root.geometry("540x520")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG_MAIN)

        self.input_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.mode_label_var = tk.StringVar(value="Corte Seco (Punch)")
        self.scale_var = tk.DoubleVar(value=1.22)
        self.interval_var = tk.DoubleVar(value=3.5)
        self.face_lock_var = tk.BooleanVar(value=True)

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Modern.TCombobox",
            fieldbackground=self.BG_INPUT,
            background=self.BG_INPUT,
            foreground=self.TEXT_PRIMARY,
            bordercolor=self.BORDER,
            lightcolor=self.BG_INPUT,
            darkcolor=self.BG_INPUT,
            arrowcolor=self.TEXT_PRIMARY,
            padding=6,
        )
        style.map(
            "Modern.TCombobox",
            fieldbackground=[("readonly", self.BG_INPUT)],
            selectbackground=[("readonly", self.BG_INPUT)],
            selectforeground=[("readonly", self.TEXT_PRIMARY)],
        )

        style.configure(
            "Modern.TSpinbox",
            fieldbackground=self.BG_INPUT,
            background=self.BG_INPUT,
            foreground=self.TEXT_PRIMARY,
            bordercolor=self.BORDER,
            lightcolor=self.BG_INPUT,
            darkcolor=self.BG_INPUT,
            arrowcolor=self.TEXT_PRIMARY,
            padding=6,
        )

        style.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor=self.BG_INPUT,
            background=self.ACCENT,
            bordercolor=self.BG_INPUT,
            lightcolor=self.ACCENT,
            darkcolor=self.ACCENT,
            thickness=8,
        )

    def _create_card(self, parent: tk.Widget, title: str) -> tk.Frame:
        wrapper = tk.Frame(parent, bg=self.BG_MAIN)
        wrapper.pack(fill="x", pady=(0, 14))

        tk.Label(
            wrapper,
            text=title.upper(),
            bg=self.BG_MAIN,
            fg=self.TEXT_SECONDARY,
            font=("Sans", 8, "bold"),
        ).pack(anchor="w", pady=(0, 5))

        card = tk.Frame(
            wrapper,
            bg=self.BG_CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        card.pack(fill="x")
        return card

    def _create_path_row(
        self,
        parent: tk.Frame,
        label_text: str,
        text_var: tk.StringVar,
        button_text: str,
        command,
        top_pad: int = 0,
    ):
        tk.Label(
            parent,
            text=label_text,
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
            font=("Sans", 9, "bold"),
        ).pack(anchor="w", pady=(top_pad, 4))

        row = tk.Frame(parent, bg=self.BG_CARD)
        row.pack(fill="x")

        entry = tk.Entry(
            row,
            textvariable=text_var,
            bg=self.BG_INPUT,
            fg=self.TEXT_PRIMARY,
            insertbackground=self.TEXT_PRIMARY,
            relief="flat",
            highlightbackground=self.BORDER,
            highlightthickness=1,
            font=("Sans", 9),
        )
        entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        btn = tk.Button(
            row,
            text=button_text,
            command=command,
            bg=self.BG_INPUT,
            fg=self.TEXT_PRIMARY,
            activebackground=self.BORDER,
            activeforeground=self.TEXT_PRIMARY,
            relief="flat",
            highlightbackground=self.BORDER,
            highlightthickness=1,
            cursor="hand2",
            font=("Sans", 9),
            padx=12,
            pady=4,
        )
        btn.pack(side="right")

    def _build_ui(self):
        container = tk.Frame(self.root, bg=self.BG_MAIN, padx=22, pady=18)
        container.pack(fill="both", expand=True)

        # Cabeçalho
        header = tk.Frame(container, bg=self.BG_MAIN)
        header.pack(fill="x", pady=(0, 16))

        tk.Label(
            header,
            text="Zoom Automatic",
            bg=self.BG_MAIN,
            fg=self.TEXT_PRIMARY,
            font=("Sans", 16, "bold"),
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Cortes dinâmicos de câmera e enquadramento facial automático",
            bg=self.BG_MAIN,
            fg=self.TEXT_SECONDARY,
            font=("Sans", 9),
        ).pack(anchor="w", pady=(2, 0))

        # Cartão 1: Arquivos
        files_card = self._create_card(container, "Arquivos")
        self._create_path_row(
            files_card,
            label_text="Vídeo Original",
            text_var=self.input_path_var,
            button_text="Selecionar...",
            command=self._browse_input,
        )
        self._create_path_row(
            files_card,
            label_text="Onde Salvar",
            text_var=self.output_path_var,
            button_text="Salvar como...",
            command=self._browse_output,
            top_pad=10,
        )

        # Cartão 2: Parâmetros
        settings_card = self._create_card(container, "Configurações de Zoom")

        grid = tk.Frame(settings_card, bg=self.BG_CARD)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=2)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)

        # Coluna 0: Estilo
        tk.Label(
            grid,
            text="Estilo de Movimento",
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
            font=("Sans", 9),
        ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 4))

        ttk.Combobox(
            grid,
            textvariable=self.mode_label_var,
            values=list(self.STYLE_MAP.keys()),
            state="readonly",
            style="Modern.TCombobox",
        ).grid(row=1, column=0, sticky="ew", padx=(0, 8))

        # Coluna 1: Intensidade
        tk.Label(
            grid,
            text="Zoom (1.1x - 1.6x)",
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
            font=("Sans", 9),
        ).grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(0, 4))

        ttk.Spinbox(
            grid,
            from_=1.10,
            to=1.60,
            increment=0.02,
            textvariable=self.scale_var,
            style="Modern.TSpinbox",
            width=8,
        ).grid(row=1, column=1, sticky="ew", padx=(0, 8))

        # Coluna 2: Intervalo
        tk.Label(
            grid,
            text="Intervalo (seg)",
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
            font=("Sans", 9),
        ).grid(row=0, column=2, sticky="w", pady=(0, 4))

        ttk.Spinbox(
            grid,
            from_=1.5,
            to=10.0,
            increment=0.5,
            textvariable=self.interval_var,
            style="Modern.TSpinbox",
            width=8,
        ).grid(row=1, column=2, sticky="ew")

        # Face Lock Toggle
        face_check = tk.Checkbutton(
            settings_card,
            text="Centralizar no rosto automaticamente (Face Lock)",
            variable=self.face_lock_var,
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
            activebackground=self.BG_CARD,
            activeforeground=self.TEXT_PRIMARY,
            selectcolor=self.BG_INPUT,
            highlightthickness=0,
            cursor="hand2",
            font=("Sans", 9),
        )
        face_check.pack(anchor="w", pady=(12, 0))

        # Área de Progresso e Ação
        status_row = tk.Frame(container, bg=self.BG_MAIN)
        status_row.pack(fill="x", pady=(2, 6))

        self.status_label = tk.Label(
            status_row,
            text="Selecione o vídeo original e o destino para começar.",
            bg=self.BG_MAIN,
            fg=self.TEXT_SECONDARY,
            font=("Sans", 9),
        )
        self.status_label.pack(side="left")

        self.pct_label = tk.Label(
            status_row,
            text="0%",
            bg=self.BG_MAIN,
            fg=self.TEXT_SECONDARY,
            font=("Sans", 9, "bold"),
        )
        self.pct_label.pack(side="right")

        self.progress = ttk.Progressbar(
            container,
            mode="determinate",
            maximum=100,
            style="Accent.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x", pady=(0, 14))

        self.run_btn = tk.Button(
            container,
            text="Gerar Vídeo com Zoom",
            command=self._start_processing,
            bg=self.ACCENT,
            fg="#FFFFFF",
            activebackground=self.ACCENT_HOVER,
            activeforeground="#FFFFFF",
            disabledforeground="#9CA3AF",
            relief="flat",
            cursor="hand2",
            font=("Sans", 10, "bold"),
            pady=10,
        )
        self.run_btn.pack(fill="x")

    def _browse_input(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o vídeo original",
            filetypes=[("Arquivos de Vídeo", "*.mp4 *.mov *.mkv *.avi *.webm")],
        )
        if not file_path:
            return

        self.input_path_var.set(file_path)
        src = Path(file_path)
        default_out = str(src.with_name(f"{src.stem}_zoom.mp4"))
        self.output_path_var.set(default_out)
        self.status_label.config(text="Pronto para processar.", fg=self.TEXT_SECONDARY)

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

    def _set_status(self, text: str, pct: int | None = None, is_error: bool = False):
        color = "#F87171" if is_error else self.TEXT_SECONDARY
        self.status_label.config(text=text, fg=color)
        if pct is not None:
            self.progress["value"] = pct
            self.pct_label.config(text=f"{pct}%")

    def _start_processing(self):
        input_path = self.input_path_var.get().strip()
        output_path = self.output_path_var.get().strip()

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

        self.run_btn.config(state="disabled", bg=self.ACCENT_DISABLED, text="Processando...")
        self._set_status("Analisando pausas na fala...", pct=0)

        mode_key = self.STYLE_MAP.get(self.mode_label_var.get(), "punch")
        zoom_scale = self.scale_var.get()
        min_interval = self.interval_var.get()
        face_tracking = self.face_lock_var.get()

        worker = threading.Thread(
            target=self._process_worker,
            args=(input_path, output_path, zoom_scale, min_interval, mode_key, face_tracking),
            daemon=True,
        )
        worker.start()

    def _process_worker(
        self,
        input_path: str,
        output_path: str,
        zoom_scale: float,
        min_interval: float,
        mode: str,
        face_tracking: bool,
    ):
        try:
            cap = cv2.VideoCapture(input_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()
            duration = round(frames / fps, 3)

            transitions = detect_speech_transitions(
                input_path,
                min_interval=min_interval,
            )

            self.root.after(
                0,
                lambda: self._set_status("Rastreando rosto e calculando cortes...", pct=5),
            )

            keyframes = build_zoom_keyframes(
                video_path=input_path,
                transitions=transitions,
                clip_duration=duration,
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
                self.root.after(0, lambda p=pct, m=msg: self._set_status(m, pct=p))

            render_zoomed_video(
                input_path=input_path,
                output_path=output_path,
                keyframes=keyframes,
                progress_callback=on_progress,
            )

            self.root.after(0, lambda: self._on_success(output_path))
        except Exception as exc:
            err_msg = str(exc)
            self.root.after(0, lambda: self._on_error(err_msg))

    def _on_success(self, output_path: str):
        self._set_status("Concluído! Vídeo salvo com sucesso.", pct=100)
        self.run_btn.config(state="normal", bg=self.ACCENT, text="Gerar Vídeo com Zoom")
        messagebox.showinfo(
            "Processamento Concluído",
            f"Vídeo salvo em:\n{output_path}\n\nPronto para ser importado no seu editor de vídeo.",
        )

    def _on_error(self, err_msg: str):
        self._set_status("Falha ao processar o vídeo.", is_error=True)
        self.run_btn.config(state="normal", bg=self.ACCENT, text="Gerar Vídeo com Zoom")
        messagebox.showerror("Erro no Processamento", err_msg)


if __name__ == "__main__":
    root = tk.Tk()
    ZoomAutomaticApp(root)
    root.mainloop()
