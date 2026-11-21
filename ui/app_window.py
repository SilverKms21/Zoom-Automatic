import tkinter as tk

from ui.editor_tab import EditorTab
from ui.preview_tab import PreviewTab
from ui.theme import MacSegmentedControl, MacTheme, configure_ttk_styles


class ZoomAutomaticApp:
    """Janela principal com barra superior estilo macOS e abas alternáveis."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Zoom Automatic")
        self.root.geometry("610x600")
        self.root.resizable(False, False)
        self.root.configure(bg=MacTheme.BG_WINDOW)

        configure_ttk_styles()
        self._build_layout()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self):
        # Barra de ferramentas superior estilo macOS
        toolbar = tk.Frame(self.root, bg=MacTheme.BG_TOOLBAR, height=56, padx=20)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        # Indicadores decorativos estilo semáforo macOS + título
        title_box = tk.Frame(toolbar, bg=MacTheme.BG_TOOLBAR)
        title_box.pack(side="left")

        dots = tk.Canvas(
            title_box, width=48, height=14, bg=MacTheme.BG_TOOLBAR, highlightthickness=0
        )
        dots.pack(side="left", padx=(0, 8))
        dots.create_oval(2, 2, 12, 12, fill="#FF5F56", outline="")
        dots.create_oval(18, 2, 28, 12, fill="#FFBD2E", outline="")
        dots.create_oval(34, 2, 44, 12, fill="#27C93F", outline="")

        tk.Label(
            title_box,
            text="Zoom Automatic",
            bg=MacTheme.BG_TOOLBAR,
            fg=MacTheme.TEXT_PRIMARY,
            font=(MacTheme.FONT_FAMILY, 11, "bold"),
        ).pack(side="left")

        # Controle segmentado (Abas)
        self.segmented = MacSegmentedControl(
            toolbar,
            options=["Configurar", "Pré-visualização"],
            on_change=self._switch_tab,
            width=260,
            height=30,
            bg_parent=MacTheme.BG_TOOLBAR,
        )
        self.segmented.pack(side="right")

        # Linha divisória da barra superior
        tk.Frame(self.root, bg=MacTheme.BORDER, height=1).pack(fill="x")

        # Área de conteúdo das abas
        self.content = tk.Frame(self.root, bg=MacTheme.BG_WINDOW, padx=22, pady=16)
        self.content.pack(fill="both", expand=True)

        self.editor_tab = EditorTab(
            self.content,
            on_video_selected=self._on_video_selected,
            on_params_changed=self._on_params_changed,
            on_open_preview=lambda: self._go_to_tab(1),
        )
        self.preview_tab = PreviewTab(
            self.content,
            get_settings_callback=self.editor_tab.get_settings,
        )

        self.editor_tab.pack(fill="both", expand=True)

    def _on_video_selected(self, _path: str):
        self.preview_tab.mark_dirty()

    def _on_params_changed(self):
        self.preview_tab.mark_dirty()

    def _go_to_tab(self, index: int):
        self.segmented.select(index)
        self._switch_tab(index)

    def _switch_tab(self, index: int):
        if index == 0:
            self.preview_tab.stop_playback()
            self.preview_tab.pack_forget()
            self.editor_tab.pack(fill="both", expand=True)
        else:
            self.editor_tab.pack_forget()
            self.preview_tab.pack(fill="both", expand=True)
            self.preview_tab.refresh_preview(force_reanalysis=False)

    def _on_close(self):
        self.preview_tab.stop_playback()
        self.preview_tab.engine.close()
        self.root.destroy()