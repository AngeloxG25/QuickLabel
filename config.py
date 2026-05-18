# =========================================================
# CONFIGURACIÓN GENERAL DEL PROYECTO
# - Soporta rutas configurables para fonts, plantillas y salida
# - Pensado para ejecutarse también compilado con Nuitka en Windows
# =========================================================

from __future__ import annotations

import json
import os
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
APP_VERSION = "1.5.0"
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


def get_plantillas_map() -> dict:
    plantillas_dir = get_plantillas_dir()
    return {
        "MINUTO VERDE": os.path.join(plantillas_dir, "minutoverde.png"),
        "GAG": os.path.join(plantillas_dir, "gag.png"),
    }


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

DEFAULT_LAYOUT = {
    "producto": {"x": POS_PRODUCTO_X, "y": POS_PRODUCTO_Y},
    "precio": {"x": POS_PRECIO[0], "y": POS_PRECIO[1]},
    "lateral": {"x": POS_LATERAL[0], "y": POS_LATERAL[1]},
    "secundario": {"x": POS_SECUNDARIO[0], "y": POS_SECUNDARIO[1]},
}

SIZE_PRODUCTO = 85
SIZE_PRECIO = 190
SIZE_LATERAL = 60
SIZE_SECUNDARIO = 60

DEFAULT_FONT_NAME = "Anton.ttf"
