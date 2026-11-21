import glob
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

venv_sites = glob.glob(str(BASE_DIR / ".venv/lib/python*/site-packages"))
if venv_sites and venv_sites[0] not in sys.path:
    sys.path.insert(0, venv_sites[0])

import tkinter as tk
from ui.app_window import ZoomAutomaticApp


def main():
    root = tk.Tk()
    ZoomAutomaticApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()