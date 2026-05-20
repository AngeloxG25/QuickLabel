# =========================================================
# UTILIDADES DEL PROYECTO
# =========================================================

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import Optional

from PIL import ImageFont

from config import (
    CONFIG_FONT_PATH,
    CONFIG_LAYOUT_PATH,
    DEFAULT_FONT_NAME,
    DEFAULT_LAYOUT,
    get_fonts_dir,
    get_output_dir,
)


def cargar_fuente() -> str:
    """Devuelve el nombre de la fuente guardada en config_font.json."""
    if os.path.exists(CONFIG_FONT_PATH):
        try:
            with open(CONFIG_FONT_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)
                font_name = data.get("font_name", DEFAULT_FONT_NAME)
                if font_name in obtener_fuentes_disponibles():
                    return font_name
        except Exception:
            pass
    return obtener_fuente_fallback()


def obtener_fuente_fallback() -> str:
    fuentes = obtener_fuentes_disponibles()
    if DEFAULT_FONT_NAME in fuentes:
        return DEFAULT_FONT_NAME
    return fuentes[0] if fuentes else DEFAULT_FONT_NAME


def obtener_font_path(font_name: Optional[str] = None) -> str:
    fuente_actual = font_name or cargar_fuente()
    return os.path.join(get_fonts_dir(), fuente_actual)


def obtener_fuentes_disponibles() -> list[str]:
    """Detecta automáticamente fuentes .ttf, .otf y .ttc.

    También revisa subcarpetas dentro de la carpeta de fonts, por si el usuario
    copia familias completas de fuentes en carpetas separadas.
    """
    fonts_dir = get_fonts_dir()
    if not os.path.isdir(fonts_dir):
        return []

    extensiones = (".ttf", ".otf", ".ttc")
    fuentes = []

    for raiz, _dirs, archivos in os.walk(fonts_dir):
        for archivo in archivos:
            if not archivo.lower().endswith(extensiones):
                continue
            ruta_abs = os.path.join(raiz, archivo)
            ruta_rel = os.path.relpath(ruta_abs, fonts_dir)
            fuentes.append(os.path.normpath(ruta_rel))

    return sorted(fuentes, key=str.lower)


def guardar_fuente(nombre_fuente: str) -> None:
    if nombre_fuente not in obtener_fuentes_disponibles():
        raise ValueError(f"La fuente no existe en la carpeta fonts seleccionada: {nombre_fuente}")

    with open(CONFIG_FONT_PATH, "w", encoding="utf-8") as file:
        json.dump({"font_name": nombre_fuente}, file, indent=4, ensure_ascii=False)


# =========================================================
# CONFIGURACIÓN DE POSICIONES / LAYOUT
# =========================================================

def cargar_layout() -> dict:
    layout = json.loads(json.dumps(DEFAULT_LAYOUT))

    if os.path.exists(CONFIG_LAYOUT_PATH):
        try:
            with open(CONFIG_LAYOUT_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)

            for clave, valor in data.items():
                if clave in layout and isinstance(valor, dict):
                    layout[clave].update(valor)
        except Exception:
            pass

    return layout


def guardar_layout(layout: dict) -> None:
    data = json.loads(json.dumps(DEFAULT_LAYOUT))

    for clave, valor in layout.items():
        if clave in data and isinstance(valor, dict):
            data[clave].update(valor)

    with open(CONFIG_LAYOUT_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def restaurar_layout_default() -> dict:
    layout = json.loads(json.dumps(DEFAULT_LAYOUT))
    guardar_layout(layout)
    return layout


def formato_precio(valor) -> Optional[str]:
    try:
        if valor is None:
            return None
        valor = int(float(valor))
        if valor <= 0:
            return None
        return f"${valor:,}".replace(",", ".")
    except Exception:
        return None


def cargar_font_fijo(size: int, font_name: Optional[str] = None):
    font_path = obtener_font_path(font_name)
    if not os.path.exists(font_path):
        return ImageFont.load_default()
    return ImageFont.truetype(font_path, size)


def ajustar_fuente(draw, texto: str, max_width: int, max_size: int, font_name: Optional[str] = None):
    font_path = obtener_font_path(font_name)

    if not os.path.exists(font_path):
        return ImageFont.load_default()

    size = max_size
    while size > 20:
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), texto, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            return font
        size -= 2

    return ImageFont.truetype(font_path, 20)


def dividir_texto_por_ancho(texto: str, draw, font, max_width: int = 820) -> list[str]:
    texto = str(texto).upper().strip()
    palabras = texto.split()

    if not texto:
        return [""]

    if len(palabras) <= 1:
        return [texto]

    bbox_total = draw.textbbox((0, 0), texto, font=font)
    ancho_total = bbox_total[2] - bbox_total[0]
    if ancho_total <= max_width:
        return [texto]

    mejor = None
    mejor_puntaje = float("inf")

    for corte in range(1, len(palabras)):
        linea1 = " ".join(palabras[:corte])
        linea2 = " ".join(palabras[corte:])
        bbox1 = draw.textbbox((0, 0), linea1, font=font)
        bbox2 = draw.textbbox((0, 0), linea2, font=font)
        ancho1 = bbox1[2] - bbox1[0]
        ancho2 = bbox2[2] - bbox2[0]

        exceso = max(0, ancho1 - max_width) + max(0, ancho2 - max_width)
        diferencia = abs(ancho1 - ancho2)
        puntaje = (exceso * 10_000) + diferencia

        if puntaje < mejor_puntaje:
            mejor_puntaje = puntaje
            mejor = [linea1, linea2]

    return mejor or [texto]


def dividir_texto(texto: str, max_chars: int = 28) -> list[str]:
    texto = str(texto).upper().strip()
    palabras = texto.split()

    if len(texto) <= max_chars or len(palabras) <= 1:
        return [texto]

    mejor_corte = 1
    mejor_diferencia = float("inf")

    for i in range(1, len(palabras)):
        linea1 = " ".join(palabras[:i])
        linea2 = " ".join(palabras[i:])
        diferencia = abs(len(linea1) - len(linea2))
        if diferencia < mejor_diferencia:
            mejor_diferencia = diferencia
            mejor_corte = i

    return [" ".join(palabras[:mejor_corte]), " ".join(palabras[mejor_corte:])]


def limpiar_nombre_archivo(texto: str) -> str:
    texto = str(texto).strip().upper()
    texto = re.sub(r'[\\/:*?"<>|]+', "-", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto[:50] or "ETIQUETA"


def abrir_ruta(ruta: str) -> None:
    if sys.platform.startswith("win"):
        os.startfile(ruta)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", ruta])
    else:
        subprocess.Popen(["xdg-open", ruta])


def abrir_carpeta_salida() -> None:
    output_dir = get_output_dir()
    os.makedirs(output_dir, exist_ok=True)
    abrir_ruta(output_dir)
