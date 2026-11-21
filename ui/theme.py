import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional


class MacTheme:
    """Paleta de cores e tipografia inspirada no macOS Dark Mode."""

    BG_WINDOW = "#1C1C1E"       # System Gray 6 Dark
    BG_TOOLBAR = "#242426"      # Barra superior translúcida
    BG_CARD = "#2C2C2E"         # System Gray 5 Dark
    BG_CONTROL = "#3A3A3C"      # System Gray 4 Dark
    BG_CONTROL_HOVER = "#48484A"
    BG_SEGMENT_ACTIVE = "#636366"
    BG_VIEWPORT = "#0D0D0F"

    BORDER = "#3A3A3C"
    BORDER_SUBTLE = "#2E2E30"

    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#98989D"
    TEXT_MUTED = "#636366"

    ACCENT = "#0A84FF"          # macOS System Blue
    ACCENT_HOVER = "#409CFF"
    ACCENT_DISABLED = "#2C3E50"

    GREEN = "#30D158"           # macOS System Green
    RED = "#FF453A"             # macOS System Red

    FONT_FAMILY = "Sans"


def configure_ttk_styles():
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Mac.TCombobox",
        fieldbackground=MacTheme.BG_CONTROL,
        background=MacTheme.BG_CONTROL,
        foreground=MacTheme.TEXT_PRIMARY,
        bordercolor=MacTheme.BORDER,
        lightcolor=MacTheme.BG_CONTROL,
        darkcolor=MacTheme.BG_CONTROL,
        arrowcolor=MacTheme.TEXT_PRIMARY,
        padding=6,
    )
    style.map(
        "Mac.TCombobox",
        fieldbackground=[("readonly", MacTheme.BG_CONTROL)],
        selectbackground=[("readonly", MacTheme.BG_CONTROL)],
        selectforeground=[("readonly", MacTheme.TEXT_PRIMARY)],
    )

    style.configure(
        "Mac.TSpinbox",
        fieldbackground=MacTheme.BG_CONTROL,
        background=MacTheme.BG_CONTROL,
        foreground=MacTheme.TEXT_PRIMARY,
        bordercolor=MacTheme.BORDER,
        lightcolor=MacTheme.BG_CONTROL,
        darkcolor=MacTheme.BG_CONTROL,
        arrowcolor=MacTheme.TEXT_PRIMARY,
        padding=6,
    )

    style.configure(
        "Mac.Horizontal.TProgressbar",
        troughcolor=MacTheme.BG_CONTROL,
        background=MacTheme.ACCENT,
        bordercolor=MacTheme.BG_CONTROL,
        lightcolor=MacTheme.ACCENT,
        darkcolor=MacTheme.ACCENT,
        thickness=6,
    )


def draw_rounded_rect(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
    **kwargs,
):
    r = min(radius, (x2 - x1) / 2.0, (y2 - y1) / 2.0)
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class MacButton(tk.Canvas):
    """Botão arredondado estilo macOS com estados hover e disabled."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Optional[Callable] = None,
        primary: bool = False,
        width: int = 120,
        height: int = 34,
        radius: int = 9,
        bg_parent: str = MacTheme.BG_CARD,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=bg_parent,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.text = text
        self.command = command
        self.primary = primary
        self.radius = radius
        self.enabled = True
        self.hovered = False

        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)
        self._redraw()

    def set_text(self, text: str):
        self.text = text
        self._redraw()

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._redraw()

    def _on_enter(self, _event):
        if self.enabled:
            self.hovered = True
            self._redraw()

    def _on_leave(self, _event):
        self.hovered = False
        self._redraw()

    def _on_click(self, _event):
        if self.enabled and self.command:
            self.command()

    def _redraw(self):
        self.delete("all")
        w = max(10, self.winfo_width())
        h = max(10, self.winfo_height())

        if not self.enabled:
            fill = MacTheme.ACCENT_DISABLED if self.primary else MacTheme.BG_CONTROL
            fg = MacTheme.TEXT_MUTED
        elif self.primary:
            fill = MacTheme.ACCENT_HOVER if self.hovered else MacTheme.ACCENT
            fg = MacTheme.TEXT_PRIMARY
        else:
            fill = MacTheme.BG_CONTROL_HOVER if self.hovered else MacTheme.BG_CONTROL
            fg = MacTheme.TEXT_PRIMARY

        draw_rounded_rect(self, 1, 1, w - 1, h - 1, self.radius, fill=fill, outline="")
        weight = "bold" if self.primary else "normal"
        self.create_text(
            w / 2,
            h / 2,
            text=self.text,
            fill=fg,
            font=(MacTheme.FONT_FAMILY, 9, weight),
        )


class MacToggle(tk.Canvas):
    """Switch deslizante estilo macOS / iOS."""

    def __init__(
        self,
        parent: tk.Widget,
        variable: tk.BooleanVar,
        command: Optional[Callable] = None,
        bg_parent: str = MacTheme.BG_CARD,
    ):
        super().__init__(
            parent,
            width=42,
            height=24,
            bg=bg_parent,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.variable = variable
        self.command = command
        self.bind("<ButtonRelease-1>", self._toggle)
        self.variable.trace_add("write", lambda *_: self._redraw())
        self._redraw()

    def _toggle(self, _event):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def _redraw(self):
        self.delete("all")
        active = self.variable.get()
        track_color = MacTheme.GREEN if active else MacTheme.BG_CONTROL
        draw_rounded_rect(self, 1, 1, 41, 23, 11, fill=track_color, outline="")

        knob_x = 21 if active else 3
        self.create_oval(knob_x, 3, knob_x + 18, 21, fill="#FFFFFF", outline="")


class MacSegmentedControl(tk.Canvas):
    """Controle segmentado estilo barra superior do macOS."""

    def __init__(
        self,
        parent: tk.Widget,
        options: List[str],
        on_change: Callable[[int], None],
        width: int = 340,
        height: int = 32,
        bg_parent: str = MacTheme.BG_TOOLBAR,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=bg_parent,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.options = options
        self.on_change = on_change
        self.selected_index = 0

        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<ButtonRelease-1>", self._on_click)
        self._redraw()

    def select(self, index: int):
        if 0 <= index < len(self.options):
            self.selected_index = index
            self._redraw()

    def _on_click(self, event):
        w = max(1, self.winfo_width())
        seg_w = w / len(self.options)
        idx = int(event.x // seg_w)
        if 0 <= idx < len(self.options) and idx != self.selected_index:
            self.selected_index = idx
            self._redraw()
            self.on_change(idx)

    def _redraw(self):
        self.delete("all")
        w = max(20, self.winfo_width())
        h = max(16, self.winfo_height())

        draw_rounded_rect(self, 1, 1, w - 1, h - 1, 9, fill=MacTheme.BG_CARD, outline=MacTheme.BORDER)

        seg_w = (w - 6) / len(self.options)
        ax1 = 3 + self.selected_index * seg_w
        ax2 = ax1 + seg_w
        draw_rounded_rect(
            self,
            ax1,
            3,
            ax2,
            h - 3,
            7,
            fill=MacTheme.BG_SEGMENT_ACTIVE,
            outline="",
        )

        for idx, label in enumerate(self.options):
            cx = 3 + (idx + 0.5) * seg_w
            is_sel = idx == self.selected_index
            self.create_text(
                cx,
                h / 2,
                text=label,
                fill=MacTheme.TEXT_PRIMARY if is_sel else MacTheme.TEXT_SECONDARY,
                font=(MacTheme.FONT_FAMILY, 9, "bold" if is_sel else "normal"),
            )


class MacTimeline(tk.Canvas):
    """Linha do tempo interativa com marcadores verticais nos pontos de zoom."""

    def __init__(
        self,
        parent: tk.Widget,
        on_seek: Callable[[float], None],
        bg_parent: str = MacTheme.BG_CARD,
    ):
        super().__init__(
            parent,
            height=28,
            bg=bg_parent,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.on_seek = on_seek
        self.duration: float = 0.0
        self.current_time: float = 0.0
        self.markers: List[float] = []

        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Button-1>", self._handle_drag)
        self.bind("<B1-Motion>", self._handle_drag)
        self._redraw()

    def set_data(self, duration: float, markers: List[float]):
        self.duration = max(0.0, duration)
        self.markers = markers
        self._redraw()

    def set_time(self, current_time: float):
        self.current_time = max(0.0, min(self.duration, current_time))
        self._redraw()

    def _handle_drag(self, event):
        if self.duration <= 0:
            return
        w = max(20, self.winfo_width())
        pad = 10
        usable = max(1, w - 2 * pad)
        ratio = max(0.0, min(1.0, (event.x - pad) / usable))
        new_time = ratio * self.duration
        self.current_time = new_time
        self._redraw()
        self.on_seek(new_time)

    def _redraw(self):
        self.delete("all")
        w = max(30, self.winfo_width())
        h = max(20, self.winfo_height())
        pad = 10
        usable = max(1, w - 2 * pad)
        cy = h / 2

        # Trilho de fundo
        draw_rounded_rect(self, pad, cy - 3, w - pad, cy + 3, 3, fill=MacTheme.BG_CONTROL, outline="")

        # Marcadores dos cortes de zoom
        if self.duration > 0:
            for t in self.markers:
                if t <= 0:
                    continue
                mx = pad + (min(t, self.duration) / self.duration) * usable
                self.create_line(mx, cy - 8, mx, cy + 8, fill=MacTheme.ACCENT, width=2)

            # Preenchimento do progresso
            progress_x = pad + (self.current_time / self.duration) * usable
            if progress_x > pad + 2:
                draw_rounded_rect(
                    self, pad, cy - 3, progress_x, cy + 3, 3, fill=MacTheme.ACCENT, outline=""
                )

            # Cabeça de reprodução (Playhead)
            self.create_oval(
                progress_x - 6,
                cy - 6,
                progress_x + 6,
                cy + 6,
                fill="#FFFFFF",
                outline=MacTheme.ACCENT,
                width=2,
            )