# =========================================================
# INTERFAZ GRÁFICA MEJORADA
# - Panel izquierdo con scroll
# - Opciones colapsables/desplegables
# - Menú Ajustes para cambiar rutas de fonts, plantillas y salida
# - Asistente inicial para elegir carpetas en el primer inicio
# - Vista previa responsiva y ajuste por arrastre
# =========================================================

from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from config import (
    APP_SETTINGS_PATH,
    APP_ICON_PATH,
    APP_NAME,
    APP_VERSION,
    APP_DEVELOPER,
    APP_DESCRIPTION,
    DEFAULT_APP_SETTINGS,
    get_default_excel_path,
    get_output_dir,
    get_plantillas_map,
    load_app_settings,
    save_app_settings,
)
from etiqueta_renderer import renderizar_etiqueta
from generar_etiquetas import generar_etiquetas
from generar_pdf import generar_pdf
from utils import (
    abrir_carpeta_salida,
    abrir_ruta,
    cargar_fuente,
    cargar_layout,
    guardar_fuente,
    guardar_layout,
    obtener_fuentes_disponibles,
    restaurar_layout_default,
)


class ScrollableFrame(ttk.Frame):
    """Frame vertical con scroll para evitar que las opciones queden tapadas."""

    def __init__(self, parent, width=310, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.canvas = tk.Canvas(self, width=width, highlightthickness=0, bg="white")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas, style="Card.TFrame", padding=14)

        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _content_height(self) -> int:
        self.update_idletasks()
        bbox = self.canvas.bbox("all")
        if not bbox:
            return 0
        return max(0, bbox[3] - bbox[1])

    def _has_vertical_overflow(self) -> bool:
        return self._content_height() > max(self.canvas.winfo_height(), 1)

    def refresh_scroll(self, force_top_if_no_overflow: bool = True):
        self.update_idletasks()
        bbox = self.canvas.bbox("all")
        if not bbox:
            self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), self.canvas.winfo_height()))
            return

        content_h = max(0, bbox[3] - bbox[1])
        canvas_h = max(self.canvas.winfo_height(), 1)
        scroll_h = max(content_h, canvas_h)
        self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), scroll_h))

        if force_top_if_no_overflow and content_h <= canvas_h:
            self.canvas.yview_moveto(0)

    def _on_content_configure(self, _event=None):
        self.refresh_scroll()

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)
        self.refresh_scroll()

    def _mouse_inside(self) -> bool:
        try:
            x, y = self.winfo_pointerxy()
            widget = self.winfo_containing(x, y)
        except (tk.TclError, KeyError):
            return False

        while widget is not None:
            if widget == self:
                return True
            widget = getattr(widget, "master", None)
        return False

    def _on_mousewheel(self, event):
        if self._mouse_inside() and self._has_vertical_overflow():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self.refresh_scroll(force_top_if_no_overflow=False)

    def _on_mousewheel_linux(self, event):
        if not self._mouse_inside() or not self._has_vertical_overflow():
            return
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        self.refresh_scroll(force_top_if_no_overflow=False)


class CollapsibleSection(ttk.Frame):
    def __init__(self, parent, title: str, opened: bool = True, on_toggle=None):
        super().__init__(parent, style="Card.TFrame")
        self.opened = tk.BooleanVar(value=opened)
        self.title = title
        self.on_toggle = on_toggle
        self.header = ttk.Button(self, text=self._header_text(title), command=self.toggle, style="Section.TButton")
        self.header.pack(fill="x", pady=(0, 4))
        self.body = ttk.Frame(self, style="Card.TFrame", padding=(2, 6, 2, 10))
        if opened:
            self.body.pack(fill="x")

    def _header_text(self, title: str) -> str:
        return f"{'▼' if self.opened.get() else '▶'} {title}"

    def toggle(self):
        if self.opened.get():
            self.opened.set(False)
            self.body.pack_forget()
        else:
            self.opened.set(True)
            self.body.pack(fill="x")
        self.header.configure(text=self._header_text(self.title))
        if callable(self.on_toggle):
            self.after(10, self.on_toggle)


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.minsize(920, 620)
        self.app_icon_photo = None
        self._aplicar_icono_ventana()

        self.settings = load_app_settings()

        self.preview_photo = None
        self.preview_original_size = (1920, 650)
        self.preview_display_size = (820, 360)
        self.preview_scale = 1.0
        self.preview_offset = (0, 0)
        self.drag_item = None
        self.drag_start = None
        self.layout = cargar_layout()
        self.resize_after_id = None
        self.entry_after_id = None

        self.log_queue: queue.Queue = queue.Queue()
        self.running = False

        plantillas = get_plantillas_map()
        plantilla_inicial = next(iter(plantillas.keys()))

        self.template_var = tk.StringVar(value=plantilla_inicial)
        self.font_var = tk.StringVar(value=cargar_fuente())
        self.product_var = tk.StringVar(value="ACEITE VEGETAL MARAVILLA 900 ML")
        self.precio_unidad_var = tk.StringVar(value="1290")
        self.precio_caja_var = tk.StringVar(value="15480")
        self.status_var = tk.StringVar(value="Listo")
        self.selected_item_var = tk.StringVar(value="Seleccionado: ninguno")
        self.excel_path = get_default_excel_path()
        if os.path.isfile(self.excel_path):
            excel_texto = f"Excel: {os.path.basename(self.excel_path)}"
        else:
            excel_texto = "Excel: no seleccionado"
        self.excel_label_var = tk.StringVar(value=excel_texto)

        self._crear_estilos()
        self._crear_menu()
        self._crear_ui()
        self._cargar_fuentes()
        self._centrar_ventana()

        self.after(100, self.actualizar_preview)
        self.after(150, self._configuracion_inicial_si_corresponde)
        self.after(200, self._procesar_log_queue)

    def _aplicar_icono_ventana(self):
        """Aplica el icono al ejecutable/ventana cuando existe el archivo assets/label_844652.ico."""
        if not os.path.exists(APP_ICON_PATH):
            return
        try:
            self.iconbitmap(APP_ICON_PATH)
        except Exception:
            pass

    def _obtener_icono_titulo(self, size: int = 32):
        """Carga el icono para mostrarlo junto al título dentro de la pantalla principal."""
        if self.app_icon_photo is not None:
            return self.app_icon_photo
        if not os.path.exists(APP_ICON_PATH):
            return None
        try:
            icon = Image.open(APP_ICON_PATH)
            icon = icon.resize((size, size), Image.Resampling.LANCZOS)
            self.app_icon_photo = ImageTk.PhotoImage(icon)
            return self.app_icon_photo
        except Exception:
            return None

    def _centrar_ventana(self):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        target_w = min(1240, int(screen_w * 0.92))
        target_h = min(820, int(screen_h * 0.88))
        target_w = max(target_w, 920)
        target_h = max(target_h, 620)
        x = max((screen_w - target_w) // 2, 0)
        y = max((screen_h - target_h) // 2, 0)
        self.geometry(f"{target_w}x{target_h}+{x}+{y}")

    def _crear_estilos(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f6f8")
        style.configure("Card.TFrame", background="white", relief="flat")
        style.configure("TLabel", background="#f5f6f8", font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="white", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#f5f6f8", font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", background="#f5f6f8", font=("Segoe UI", 10))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.configure("TButton", padding=7)
        style.configure(
            "Section.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=9,
            background="#0f766e",
            foreground="white",
            bordercolor="#0f766e",
            lightcolor="#0f766e",
            darkcolor="#0f766e",
        )
        style.map(
            "Section.TButton",
            background=[("active", "#115e59"), ("pressed", "#134e4a")],
            foreground=[("active", "white"), ("pressed", "white")],
        )

    def _crear_menu(self):
        menubar = tk.Menu(self)
        menu_ajustes = tk.Menu(menubar, tearoff=0)
        menu_ajustes.add_command(label="Cambiar ubicación de fonts...", command=lambda: self.cambiar_directorio("fonts_dir", "Selecciona la carpeta de fonts"))
        menu_ajustes.add_command(label="Cambiar ubicación de plantillas...", command=lambda: self.cambiar_directorio("plantillas_dir", "Selecciona la carpeta de plantillas"))
        menu_ajustes.add_command(label="Cambiar carpeta de salida...", command=lambda: self.cambiar_directorio("output_dir", "Selecciona la carpeta de salida"))
        menu_ajustes.add_separator()
        menu_ajustes.add_command(label="Restaurar ubicaciones por defecto", command=self.restaurar_rutas_predeterminadas)
        menubar.add_cascade(label="Ajustes", menu=menu_ajustes)

        menu_info = tk.Menu(menubar, tearoff=0)
        menu_info.add_command(label="Acerca del programa", command=self.mostrar_acerca_de)
        menubar.add_cascade(label="Información", menu=menu_info)

        self.config(menu=menubar)

    def mostrar_acerca_de(self):
        messagebox.showinfo(
            "Información del programa",
            f"{APP_NAME}\n"
            f"Versión: {APP_VERSION}\n"
            f"Desarrollado por: {APP_DEVELOPER}\n\n"
            f"{APP_DESCRIPTION}",
        )

    def _crear_ui(self):
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(anchor="w", fill="x")
        icono_titulo = self._obtener_icono_titulo(34)
        if icono_titulo is not None:
            ttk.Label(header, image=icono_titulo).pack(side="left", padx=(0, 10))
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(side="left", anchor="w")

        ttk.Label(
            root,
            text="Cambia la fuente, elige una plantilla y arrastra la descripción o los precios en la vista previa para ajustar su posición.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 14))

        body = ttk.Frame(root)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self.scroll_panel = ScrollableFrame(body, width=315)
        self.scroll_panel.grid(row=0, column=0, sticky="nsw", padx=(0, 16))
        panel = self.scroll_panel.content

        preview_card = ttk.Frame(body, style="Card.TFrame", padding=16)
        preview_card.grid(row=0, column=1, sticky="nsew")
        preview_card.columnconfigure(0, weight=1)
        preview_card.rowconfigure(1, weight=1)

        # 1. Seleccionar Excel
        sec_excel = CollapsibleSection(panel, "1. Seleccionar Excel", opened=True, on_toggle=self._refrescar_panel_scroll)
        sec_excel.pack(fill="x", pady=(0, 8))
        excel_frame = sec_excel.body
        ttk.Label(excel_frame, textvariable=self.excel_label_var, style="Card.TLabel", wraplength=260).pack(anchor="w", pady=(0, 8))
        ttk.Button(excel_frame, text="Seleccionar archivo Excel", command=self.seleccionar_excel).pack(fill="x", pady=(0, 4))

        # 2. Datos de ejemplo
        sec_datos = CollapsibleSection(panel, "2. Datos de ejemplo", opened=False, on_toggle=self._refrescar_panel_scroll)
        sec_datos.pack(fill="x", pady=(0, 8))
        datos = sec_datos.body
        self._entry(datos, "Producto", self.product_var)
        self._entry(datos, "Precio unidad", self.precio_unidad_var)
        self._entry(datos, "Precio caja", self.precio_caja_var)
        ttk.Button(datos, text="Actualizar vista previa", command=self.actualizar_preview).pack(fill="x", pady=(8, 4))

        # 3. Plantilla y fuente
        sec_general = CollapsibleSection(panel, "3. Plantilla y fuente", opened=False, on_toggle=self._refrescar_panel_scroll)
        sec_general.pack(fill="x", pady=(0, 8))
        general = sec_general.body
        ttk.Label(general, text="Plantilla", style="Card.TLabel").pack(anchor="w")
        self.template_combo = ttk.Combobox(general, textvariable=self.template_var, values=list(get_plantillas_map().keys()), state="readonly", width=34)
        self.template_combo.pack(anchor="w", pady=(4, 14), fill="x")
        self.template_combo.bind("<<ComboboxSelected>>", lambda _e: self.actualizar_preview())

        ttk.Label(general, text="Fuente", style="Card.TLabel").pack(anchor="w")
        self.font_combo = ttk.Combobox(general, textvariable=self.font_var, state="readonly", width=34)
        self.font_combo.pack(anchor="w", pady=(4, 6), fill="x")
        self.font_combo.bind("<<ComboboxSelected>>", lambda _e: self.actualizar_preview())
        ttk.Button(general, text="Guardar esta fuente", style="Primary.TButton", command=self.guardar_fuente_actual).pack(fill="x", pady=(0, 4))

        # 4. Ajuste de posición
        sec_pos = CollapsibleSection(panel, "4. Ajuste de posición", opened=False, on_toggle=self._refrescar_panel_scroll)
        sec_pos.pack(fill="x", pady=(0, 8))
        pos = sec_pos.body
        ttk.Label(
            pos,
            text="En la vista previa, haz clic sobre una zona y arrástrala con el mouse. Luego guarda las posiciones.",
            style="Card.TLabel",
            wraplength=260,
        ).pack(anchor="w", pady=(0, 8))
        ttk.Label(pos, textvariable=self.selected_item_var, style="Card.TLabel", wraplength=260).pack(anchor="w", pady=(0, 8))
        ttk.Button(pos, text="Guardar posiciones", style="Primary.TButton", command=self.guardar_posiciones_actuales).pack(fill="x", pady=(0, 8))
        ttk.Button(pos, text="Restaurar posiciones originales", command=self.restaurar_posiciones).pack(fill="x", pady=(0, 4))

        # 5. Generar archivos
        sec_generar = CollapsibleSection(panel, "5. Generar archivos", opened=True, on_toggle=self._refrescar_panel_scroll)
        sec_generar.pack(fill="x", pady=(0, 8))
        generar = sec_generar.body
        ttk.Button(generar, text="Generar solo PNG", command=self.generar_etiquetas_async).pack(fill="x", pady=(0, 8))
        ttk.Button(generar, text="Generar PDF", style="Primary.TButton", command=self.generar_todo_async).pack(fill="x", pady=(0, 8))
        ttk.Button(generar, text="Abrir carpeta de salida", command=abrir_carpeta_salida).pack(fill="x")

        ttk.Label(panel, textvariable=self.status_var, style="Card.TLabel", wraplength=260).pack(anchor="w", pady=(12, 0))

        # Vista previa
        top_preview = ttk.Frame(preview_card, style="Card.TFrame")
        top_preview.grid(row=0, column=0, sticky="ew")
        top_preview.columnconfigure(0, weight=1)
        ttk.Label(top_preview, text="Vista previa interactiva", style="Card.TLabel", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(
            top_preview,
            text="Puedes mover: descripción, precio principal, texto lateral y precio secundario. La vista se ajusta al tamaño de la ventana.",
            style="Card.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 8))

        self.preview_canvas = tk.Canvas(preview_card, bg="#f3f4f6", highlightthickness=0, height=390)
        self.preview_canvas.grid(row=1, column=0, sticky="nsew", pady=(8, 12))
        self.preview_canvas.bind("<ButtonPress-1>", self._on_preview_press)
        self.preview_canvas.bind("<B1-Motion>", self._on_preview_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self._on_preview_release)
        self.preview_canvas.bind("<Configure>", self._on_preview_resize)

        ttk.Label(preview_card, text="Registro de proceso", style="Card.TLabel", font=("Segoe UI", 11, "bold")).grid(row=2, column=0, sticky="w")
        self.log_text = tk.Text(preview_card, height=8, wrap="word", font=("Consolas", 9), bg="#111827", fg="#e5e7eb")
        self.log_text.grid(row=3, column=0, sticky="ew", pady=(8, 0))

    def _refrescar_panel_scroll(self):
        if hasattr(self, "scroll_panel"):
            self.scroll_panel.refresh_scroll()

    def _entry(self, parent, label, variable):
        ttk.Label(parent, text=label, style="Card.TLabel").pack(anchor="w")
        entry = ttk.Entry(parent, textvariable=variable, width=36)
        entry.pack(anchor="w", pady=(4, 10), fill="x")
        entry.bind("<KeyRelease>", self._on_entry_change)
        return entry

    def _on_entry_change(self, _event=None):
        if self.entry_after_id:
            self.after_cancel(self.entry_after_id)
        self.entry_after_id = self.after(250, self.actualizar_preview)

    def _on_preview_resize(self, _event=None):
        if self.resize_after_id:
            self.after_cancel(self.resize_after_id)
        self.resize_after_id = self.after(120, self.actualizar_preview)

    def _cargar_fuentes(self):
        fuentes = obtener_fuentes_disponibles()
        self.font_combo["values"] = fuentes
        if not fuentes:
            self.status_var.set("No hay fuentes en la carpeta seleccionada. Agrega archivos .ttf u .otf.")
            self.font_combo.configure(state="disabled")
        else:
            self.font_combo.configure(state="readonly")
            if self.font_var.get() not in fuentes:
                self.font_var.set(fuentes[0])

    def _configuracion_inicial_si_corresponde(self):
        if os.path.exists(APP_SETTINGS_PATH):
            return

        messagebox.showinfo(
            "Configuración inicial",
            "Es la primera vez que abres el programa.\n\n"
            "Ahora podrás seleccionar la carpeta de fonts, la carpeta de plantillas y la carpeta de salida."
            "\n\nSi cancelas alguna selección, se usará la ubicación por defecto.",
        )

        nuevos = dict(DEFAULT_APP_SETTINGS)
        for key, titulo in (
            ("fonts_dir", "Selecciona la carpeta de fonts"),
            ("plantillas_dir", "Selecciona la carpeta de plantillas"),
            ("output_dir", "Selecciona la carpeta de salida"),
        ):
            ruta = filedialog.askdirectory(title=titulo, initialdir=nuevos[key])
            if ruta:
                nuevos[key] = ruta

        self.settings = save_app_settings(nuevos)
        self._aplicar_cambios_rutas(mostrar_mensaje=False)
        self._log("Configuración inicial guardada.")

    def cambiar_directorio(self, key: str, title: str):
        actual = self.settings.get(key, DEFAULT_APP_SETTINGS[key])
        ruta = filedialog.askdirectory(title=title, initialdir=actual)
        if not ruta:
            return
        nuevos = dict(self.settings)
        nuevos[key] = ruta
        self.settings = save_app_settings(nuevos)
        self._aplicar_cambios_rutas(mostrar_mensaje=True)

    def restaurar_rutas_predeterminadas(self):
        if not messagebox.askyesno("Restaurar ubicaciones", "¿Deseas restaurar las ubicaciones por defecto de fonts, plantillas y salida?"):
            return
        self.settings = save_app_settings(DEFAULT_APP_SETTINGS)
        self._aplicar_cambios_rutas(mostrar_mensaje=True)

    def _aplicar_cambios_rutas(self, mostrar_mensaje: bool = False):
        self.settings = load_app_settings()
        self.template_combo["values"] = list(get_plantillas_map().keys())
        if self.template_var.get() not in self.template_combo["values"]:
            self.template_var.set(next(iter(get_plantillas_map().keys())))
        self._cargar_fuentes()
        self.actualizar_preview()
        salida = self.settings.get("output_dir", "")
        self.status_var.set(f"Rutas actualizadas. Salida: {salida}")
        if mostrar_mensaje:
            messagebox.showinfo(
                "Rutas actualizadas",
                "Se actualizaron las ubicaciones del proyecto.\n\n"
                f"Fonts: {self.settings['fonts_dir']}\n"
                f"Plantillas: {self.settings['plantillas_dir']}\n"
                f"Salida: {self.settings['output_dir']}",
            )

    def actualizar_preview(self):
        try:
            imagen = renderizar_etiqueta(
                producto=self.product_var.get(),
                marca=self.template_var.get(),
                precio_unidad=self.precio_unidad_var.get(),
                precio_caja=self.precio_caja_var.get(),
                font_name=self.font_var.get(),
                layout=self.layout,
            )
            self.preview_original_size = imagen.size

            canvas_w = max(self.preview_canvas.winfo_width(), 320)
            canvas_h = max(self.preview_canvas.winfo_height(), 220)
            margen = 20
            max_w = max(canvas_w - (margen * 2), 250)
            max_h = max(canvas_h - (margen * 2), 180)
            ratio = min(max_w / imagen.width, max_h / imagen.height)
            ratio = max(ratio, 0.05)
            new_size = (int(imagen.width * ratio), int(imagen.height * ratio))
            self.preview_display_size = new_size
            self.preview_scale = ratio

            display = imagen.resize(new_size, Image.Resampling.LANCZOS)
            self.preview_photo = ImageTk.PhotoImage(display)

            self.preview_canvas.delete("all")
            offset_x = max((canvas_w - new_size[0]) // 2, 0)
            offset_y = max((canvas_h - new_size[1]) // 2, 0)
            self.preview_offset = (offset_x, offset_y)
            self.preview_canvas.create_image(offset_x, offset_y, image=self.preview_photo, anchor="nw", tags=("preview",))
            self._dibujar_puntos_arrastre()

            self.status_var.set(f"Vista previa usando: {self.font_var.get()}")
        except Exception as exc:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(20, 20, anchor="nw", text=f"No se pudo generar la vista previa:\n{exc}", fill="red")
            self.status_var.set(str(exc))

    def _layout_to_canvas(self, item: str) -> tuple[int, int]:
        x = self.layout[item].get("x")
        y = self.layout[item].get("y")
        if item == "lateral" and x is None:
            precio_x = self.layout["precio"].get("x") or 1420
            x = precio_x + 300
        x = int(x or 0)
        y = int(y or 0)
        off_x, off_y = self.preview_offset
        return int(off_x + x * self.preview_scale), int(off_y + y * self.preview_scale)

    def _canvas_to_layout(self, canvas_x: int, canvas_y: int) -> tuple[int, int]:
        off_x, off_y = self.preview_offset
        x = int((canvas_x - off_x) / self.preview_scale)
        y = int((canvas_y - off_y) / self.preview_scale)
        w, h = self.preview_original_size
        return max(0, min(x, w)), max(0, min(y, h))

    def _dibujar_puntos_arrastre(self):
        nombres = {
            "producto": "Descripción",
            "precio": "Precio",
            "lateral": "Lateral",
            "secundario": "Precio secundario",
        }
        for item, label in nombres.items():
            x, y = self._layout_to_canvas(item)
            r = 7
            self.preview_canvas.create_oval(x - r, y - r, x + r, y + r, fill="#2563eb", outline="white", width=2, tags=("drag_handle", item))
            self.preview_canvas.create_text(x + 12, y - 12, text=label, anchor="w", fill="#1d4ed8", font=("Segoe UI", 9, "bold"), tags=("drag_handle", item))

    def _detectar_item(self, event) -> str | None:
        tolerancia = 35
        for item in ("producto", "precio", "lateral", "secundario"):
            x, y = self._layout_to_canvas(item)
            if abs(event.x - x) <= tolerancia and abs(event.y - y) <= tolerancia:
                return item
        return None

    def _on_preview_press(self, event):
        item = self._detectar_item(event)
        self.drag_item = item
        self.drag_start = (event.x, event.y)
        if item:
            nombres = {
                "producto": "descripción",
                "precio": "precio principal",
                "lateral": "texto lateral",
                "secundario": "precio secundario",
            }
            self.selected_item_var.set(f"Seleccionado: {nombres[item]}")
            self.preview_canvas.configure(cursor="fleur")
        else:
            self.selected_item_var.set("Seleccionado: ninguno")

    def _on_preview_drag(self, event):
        if not self.drag_item:
            return
        x, y = self._canvas_to_layout(event.x, event.y)
        self.layout[self.drag_item]["x"] = x
        self.layout[self.drag_item]["y"] = y
        self.actualizar_preview()

    def _on_preview_release(self, _event):
        self.drag_item = None
        self.drag_start = None
        self.preview_canvas.configure(cursor="")

    def guardar_posiciones_actuales(self):
        try:
            guardar_layout(self.layout)
            self.status_var.set("Posiciones guardadas correctamente")
            messagebox.showinfo("Posiciones guardadas", "Las posiciones quedaron guardadas para la generación de etiquetas.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def restaurar_posiciones(self):
        self.layout = restaurar_layout_default()
        self.actualizar_preview()
        self.status_var.set("Posiciones originales restauradas")

    def guardar_fuente_actual(self):
        try:
            guardar_fuente(self.font_var.get())
            self.status_var.set(f"Fuente guardada: {self.font_var.get()}")
            messagebox.showinfo("Fuente guardada", "La fuente quedó guardada para las próximas etiquetas.")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def seleccionar_excel(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar lista de precios Excel",
            initialdir=os.path.dirname(self.excel_path) if self.excel_path else os.getcwd(),
            filetypes=[("Archivos Excel", "*.xlsx *.xls"), ("Todos los archivos", "*.*")],
        )
        if not ruta:
            return
        self.excel_path = ruta
        self.excel_label_var.set(f"Excel: {os.path.basename(ruta)}")
        self.status_var.set(f"Excel seleccionado: {ruta}")
        self._log(f"Excel seleccionado: {ruta}")

    def _validar_excel_cargado(self) -> bool:
        """Evita iniciar la generación si el usuario aún no cargó un Excel válido."""
        ruta = (self.excel_path or "").strip()
        extension_valida = ruta.lower().endswith((".xlsx", ".xls"))

        if ruta and os.path.isfile(ruta) and extension_valida:
            return True

        self.status_var.set("Falta cargar el archivo Excel")
        self._log("Falta cargar el archivo Excel antes de generar.")

        seleccionar = messagebox.askyesno(
            "Falta cargar Excel",
            "Antes de generar las etiquetas debes seleccionar un archivo Excel válido con la lista de precios.\n\n"
            "¿Deseas seleccionarlo ahora?",
        )
        if not seleccionar:
            return False

        self.seleccionar_excel()
        ruta = (self.excel_path or "").strip()
        return bool(ruta and os.path.isfile(ruta) and ruta.lower().endswith((".xlsx", ".xls")))

    def generar_todo_async(self):
        if self.running:
            return
        if not self._validar_excel_cargado():
            return
        self.running = True
        self.status_var.set("Generando etiquetas y PDF...")
        self._log("Generando todo desde el Excel seleccionado...")
        threading.Thread(target=self._worker_generar_todo, daemon=True).start()

    def _worker_generar_todo(self):
        try:
            guardar_layout(self.layout)
            total = generar_etiquetas(font_name=self.font_var.get(), progreso_callback=self._log_threadsafe, excel_path=self.excel_path)
            self._log_threadsafe(f"Listo. Total generado: {total}")
            pdf_path = generar_pdf(limpiar_imagenes=True)
            self._log_threadsafe(f"PDF generado: {pdf_path}")
            self._log_threadsafe("Imágenes PNG limpiadas después de generar el PDF.")
            self.log_queue.put(("__ABRIR_PDF__", pdf_path))
            self.log_queue.put("__FIN_TODO_OK__")
        except Exception as exc:
            self._log_threadsafe(f"ERROR: {exc}")
            self.log_queue.put("__FIN_ERROR__")

    def generar_etiquetas_async(self):
        if self.running:
            return
        if not self._validar_excel_cargado():
            return
        self.running = True
        self.status_var.set("Generando etiquetas PNG...")
        self._log("Generando etiquetas PNG...")
        threading.Thread(target=self._worker_generar_etiquetas, daemon=True).start()

    def _worker_generar_etiquetas(self):
        try:
            guardar_layout(self.layout)
            total = generar_etiquetas(font_name=self.font_var.get(), progreso_callback=self._log_threadsafe, excel_path=self.excel_path)
            self._log_threadsafe(f"Listo. Total generado: {total}")
            self.log_queue.put(("__ABRIR_CARPETA__", get_output_dir()))
            self.log_queue.put("__FIN_OK__")
        except Exception as exc:
            self._log_threadsafe(f"ERROR: {exc}")
            self.log_queue.put("__FIN_ERROR__")

    def _log(self, mensaje: str):
        self.log_text.insert("end", mensaje + "\n")
        self.log_text.see("end")

    def _log_threadsafe(self, mensaje: str):
        self.log_queue.put(mensaje)

    def _procesar_log_queue(self):
        try:
            while True:
                mensaje = self.log_queue.get_nowait()
                if isinstance(mensaje, tuple) and mensaje[0] == "__ABRIR_PDF__":
                    abrir_ruta(mensaje[1])
                    continue
                if isinstance(mensaje, tuple) and mensaje[0] == "__ABRIR_CARPETA__":
                    abrir_ruta(mensaje[1])
                    continue
                if mensaje == "__FIN_TODO_OK__":
                    self.running = False
                    self.status_var.set("Etiquetas y PDF generados correctamente")
                    messagebox.showinfo("Proceso terminado", "Se generaron los PNG, se creó el PDF, se eliminaron los PNG temporales y se abrió el PDF.")
                    continue
                if mensaje == "__FIN_OK__":
                    self.running = False
                    self.status_var.set("Etiquetas PNG generadas correctamente")
                    messagebox.showinfo("Proceso terminado", "Se generaron las etiquetas PNG y se abrió la carpeta de salida.")
                    continue
                if mensaje == "__FIN_ERROR__":
                    self.running = False
                    self.status_var.set("Ocurrió un error al generar archivos")
                    continue
                self._log(mensaje)
        except queue.Empty:
            pass
        self.after(200, self._procesar_log_queue)
