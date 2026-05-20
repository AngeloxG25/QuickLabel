# =========================================================
# CONFIGURACIÓN GENERAL DEL PROYECTO
# - Soporta rutas configurables para fonts, plantillas y salida
# - Pensado para ejecutarse también compilado con Nuitka en Windows
# =========================================================

from __future__ import annotations

import json
import os
import re
from copy import deepcopy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

APP_SETTINGS_PATH = os.path.join(BASE_DIR, "app_settings.json")
CONFIG_FONT_PATH = os.path.join(BASE_DIR, "config_font.json")
CONFIG_LAYOUT_PATH = os.path.join(BASE_DIR, "config_layout.json")

DEFAULT_EXCEL_PATH = os.path.join(BASE_DIR, "ListaPrecios.xlsx")
DEFAULT_OUTPUT_DIR = os.path.join(BASE_DIR, "salida")
DEFAULT_FONTS_DIR = os.path.join(BASE_DIR, "fonts")
DEFAULT_PLANTILLAS_DIR = os.path.join(BASE_DIR, "plantillas")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
APP_ICON_PATH = os.path.join(ASSETS_DIR, "label_844652.ico")

APP_NAME = "QuickLabel"
APP_VERSION = "1.6.0"
APP_DEVELOPER = "DevAngelo for Teba"
APP_DESCRIPTION = "Generador de etiquetas de precios con vista previa interactiva."

DEFAULT_APP_SETTINGS = {
    "fonts_dir": DEFAULT_FONTS_DIR,
    "plantillas_dir": DEFAULT_PLANTILLAS_DIR,
    "output_dir": DEFAULT_OUTPUT_DIR,
}


def _normalizar_settings(data: dict | None) -> dict:
    final = deepcopy(DEFAULT_APP_SETTINGS)
    if isinstance(data, dict):
        for key in final:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                final[key] = value
    return final


def load_app_settings() -> dict:
    if os.path.exists(APP_SETTINGS_PATH):
        try:
            with open(APP_SETTINGS_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return _normalizar_settings(data)
        except Exception:
            pass
    return _normalizar_settings(None)


def save_app_settings(data: dict) -> dict:
    settings = _normalizar_settings(data)
    with open(APP_SETTINGS_PATH, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=4, ensure_ascii=False)
    ensure_runtime_directories(settings)
    return settings


def ensure_runtime_directories(settings: dict | None = None) -> dict:
    settings = _normalizar_settings(settings or load_app_settings())
    os.makedirs(settings["output_dir"], exist_ok=True)
    os.makedirs(settings["fonts_dir"], exist_ok=True)
    os.makedirs(settings["plantillas_dir"], exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    return settings


def get_fonts_dir() -> str:
    return ensure_runtime_directories()["fonts_dir"]


def get_plantillas_dir() -> str:
    return ensure_runtime_directories()["plantillas_dir"]


def get_output_dir() -> str:
    return ensure_runtime_directories()["output_dir"]


def get_default_excel_path() -> str:
    return DEFAULT_EXCEL_PATH


PLANTILLA_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

# Nombres históricos para no romper Excel antiguos que ya usaban estas marcas.
LEGACY_PLANTILLA_NAMES = {
    "minutoverde": "MINUTO VERDE",
    "gag": "GAG",
    "sadia": "SADIA",
}


def _nombre_plantilla_desde_archivo(nombre_archivo: str) -> str:
    """Convierte el nombre del archivo en el nombre visible de la plantilla.

    Ejemplos:
    - minutoverde.png -> MINUTOVERDE
    - minuto_verde.png -> MINUTO VERDE
    - mi-plantilla.jpg -> MI PLANTILLA
    """
    nombre_base = os.path.splitext(os.path.basename(nombre_archivo))[0]
    nombre_legacy = LEGACY_PLANTILLA_NAMES.get(nombre_base.lower())
    if nombre_legacy:
        return nombre_legacy

    nombre = nombre_base
    nombre = re.sub(r"[_-]+", " ", nombre)
    nombre = re.sub(r"\s+", " ", nombre).strip().upper()
    return nombre or "PLANTILLA"


def get_plantillas_map() -> dict:
    """Detecta automáticamente las plantillas disponibles.

    Cualquier imagen compatible que el usuario ponga en la carpeta de plantillas
    aparecerá en el selector y se podrá usar en el Excel usando el nombre del
    archivo sin extensión, en mayúsculas.
    """
    plantillas_dir = get_plantillas_dir()
    plantillas = {}

    if os.path.isdir(plantillas_dir):
        for archivo in sorted(os.listdir(plantillas_dir), key=str.lower):
            ruta = os.path.join(plantillas_dir, archivo)
            if not os.path.isfile(ruta):
                continue
            if not archivo.lower().endswith(PLANTILLA_EXTENSIONS):
                continue

            nombre_visible = _nombre_plantilla_desde_archivo(archivo)

            # Si existen archivos que generan el mismo nombre visible, conserva
            # el primero y evita sobrescribir de forma silenciosa.
            if nombre_visible not in plantillas:
                plantillas[nombre_visible] = ruta

    return plantillas


# Compatibilidad con versiones anteriores.
_runtime = ensure_runtime_directories()
EXCEL_PATH = DEFAULT_EXCEL_PATH
OUTPUT_DIR = _runtime["output_dir"]
FONTS_DIR = _runtime["fonts_dir"]
PLANTILLAS_DIR = _runtime["plantillas_dir"]
PLANTILLAS = get_plantillas_map()

COLOR_VERDE = (0, 122, 61)

POS_PRODUCTO_X = 545
POS_PRODUCTO_Y = 192
POS_PRECIO = (1400, 299)
POS_LATERAL = (1686, 417)
POS_SECUNDARIO = (1603, 518)

DEFAULT_LABEL_SCALE = 1.0
MIN_LABEL_SCALE = 0.60
MAX_LABEL_SCALE = 1.40

DEFAULT_LAYOUT = {
    "producto": {"x": POS_PRODUCTO_X, "y": POS_PRODUCTO_Y},
    "precio": {"x": POS_PRECIO[0], "y": POS_PRECIO[1]},
    "lateral": {"x": POS_LATERAL[0], "y": POS_LATERAL[1]},
    "secundario": {"x": POS_SECUNDARIO[0], "y": POS_SECUNDARIO[1]},
    "etiqueta": {"scale": DEFAULT_LABEL_SCALE},
}

SIZE_PRODUCTO = 85
SIZE_PRECIO = 190
SIZE_LATERAL = 60
SIZE_SECUNDARIO = 60

DEFAULT_FONT_NAME = "Anton.ttf"
