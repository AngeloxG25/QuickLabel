# =========================================================
# EJECUTAR APP
# =========================================================

# En Windows ayuda a que la ventana y el centrado funcionen mejor
# cuando la pantalla está al 125%, 150%, etc.
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from gui.main_window import App


if __name__ == "__main__":
    app = App()
    app.mainloop()
