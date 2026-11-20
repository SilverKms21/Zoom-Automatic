import glob
import sys
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
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Zoom Automatic")
        self.root.geometry("360x390")
        self.root.resizable(False, False)

        self.mode_var = tk.StringVar(value="punch")
        self.scale_var = tk.DoubleVar(value=1.22)
        self.interval_var = tk.DoubleVar(value=3.5)
        self.face_lock_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Estilo de Zoom:").pack(anchor="w")
        ttk.Combobox(
            frame,
            textvariable=self.mode_var,
            values=["punch", "smooth"],
            state="readonly"
        ).pack(fill="x", pady=(2, 10))

        ttk.Label(frame, text="Intensidade do Zoom (1.10 a 1.60):").pack(anchor="w")
        ttk.Spinbox(
            frame,
            from_=1.10,
            to=1.60,
            increment=0.02,
            textvariable=self.scale_var
        ).pack(fill="x", pady=(2, 10))

        ttk.Label(frame, text="Intervalo Mínimo entre Cortes (segundos):").pack(anchor="w")
        ttk.Spinbox(
            frame,
            from_=1.5,
            to=10.0,
            increment=0.5,
            textvariable=self.interval_var
        ).pack(fill="x", pady=(2, 10))

        ttk.Checkbutton(
            frame,
            text="Centralizar no rosto (Face Lock)",
            variable=self.face_lock_var
        ).pack(anchor="w", pady=(2, 14))

        self.progress = ttk.Progressbar(frame, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(0, 6))

        self.status_label = ttk.Label(
            frame,
            text="Escolha um vídeo para aplicar o Zoom Automatic.",
            foreground="#555"
        )
        self.status_label.pack(anchor="w", pady=(0, 12))

        self.run_btn = ttk.Button(
            frame,
            text="Selecionar Vídeo e Gerar Zoom Automatic",
            command=self.run_autozoom
        )
        self.run_btn.pack(fill="x")

    def _update_progress(self, pct: int):
        self.progress["value"] = pct
        if 97 <= pct < 100:
            self.status_label.config(text="Finalizando áudio e compressão H.264...")
        else:
            self.status_label.config(text=f"Renderizando vídeo: {pct}%...")
        self.root.update()

    def run_autozoom(self):
        input_path = filedialog.askopenfilename(
            title="Selecione o vídeo original",
            filetypes=[("Arquivos de Vídeo", "*.mp4 *.mov *.mkv *.avi *.webm")]
        )
        if not input_path:
            return

        src = Path(input_path)
        output_path = str(src.with_name(f"{src.stem}_zoom.mp4"))

        try:
            self.run_btn.config(state="disabled")
            self.progress["value"] = 0
            self.status_label.config(text="Analisando pausas na fala...")
            self.root.update()

            cap = cv2.VideoCapture(input_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()
            duration = round(frames / fps, 3)

            transitions = detect_speech_transitions(
                input_path,
                min_interval=self.interval_var.get()
            )

            self.status_label.config(text="Rastreando rosto e calculando keyframes...")
            self.root.update()

            keyframes = build_zoom_keyframes(
                video_path=input_path,
                transitions=transitions,
                clip_duration=duration,
                zoom_scale=self.scale_var.get(),
                mode=self.mode_var.get(),
                face_tracking=self.face_lock_var.get()
            )

            render_zoomed_video(
                input_path=input_path,
                output_path=output_path,
                keyframes=keyframes,
                progress_callback=self._update_progress
            )

            self.status_label.config(text="Concluído! Concluído! Vídeo pronto para edição.")
            messagebox.showinfo(
                "Zoom Automatic Concluído",
                f"Vídeo salvo com sucesso em:\n{output_path}\n\n"
                "Agora é só arrastar esse arquivo para o seu editor de vídeo."
            )
        except Exception as exc:
            messagebox.showerror("Erro no Zoom Automatic", str(exc))
            self.status_label.config(text="Falha ao processar o vídeo.")
        finally:
            self.run_btn.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    ZoomAutomaticApp(root)
    root.mainloop()
