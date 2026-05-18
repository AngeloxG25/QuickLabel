# =========================================================
# MOTOR ÚNICO DE RENDER DE ETIQUETAS
# Lo usa tanto la generación final como la vista previa.
# =========================================================

from __future__ import annotations

import os
from typing import Optional

from PIL import Image, ImageDraw

from config import (
    COLOR_VERDE,
    DEFAULT_LAYOUT,
    SIZE_LATERAL,
    SIZE_PRECIO,
    SIZE_PRODUCTO,
    SIZE_SECUNDARIO,
)
from config import get_plantillas_map
from utils import ajustar_fuente, cargar_font_fijo, cargar_layout, dividir_texto_por_ancho, formato_precio


def _crear_plantilla_temporal(nombre_marca: str) -> Image.Image:
    """Plantilla visual de emergencia si aún no existe el PNG real."""
    img = Image.new("RGB", (1920, 650), "white")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((35, 35, 1885, 615), radius=35, outline=COLOR_VERDE, width=8)
    draw.text((70, 55), f"PLANTILLA: {nombre_marca}", fill=COLOR_VERDE)
    return img


def _normalizar_layout(layout: Optional[dict]) -> dict:
    final = {
        key: value.copy() if isinstance(value, dict) else value
        for key, value in DEFAULT_LAYOUT.items()
    }
    if layout:
        for key, value in layout.items():
            if key in final and isinstance(value, dict):
                final[key].update(value)
    return final


def calcular_textos_precio(precio_unidad=None, precio_caja=None):
    precio_unidad_txt = formato_precio(precio_unidad)
    precio_caja_txt = formato_precio(precio_caja)

    if precio_caja_txt and precio_unidad_txt:
        return precio_caja_txt, "X CAJA", f"{precio_unidad_txt} C/U"
    if precio_caja_txt:
        return precio_caja_txt, "X CAJA", None
    if precio_unidad_txt:
        return precio_unidad_txt, "C/U", None
    return None, None, None


def renderizar_etiqueta(
    producto: str,
    marca: str,
    precio_unidad=None,
    precio_caja=None,
    font_name: Optional[str] = None,
    layout: Optional[dict] = None,
) -> Image.Image:
    marca = str(marca).upper().strip()
    producto = str(producto).upper().strip()
    layout = _normalizar_layout(layout or cargar_layout())

    plantillas = get_plantillas_map()
    if marca not in plantillas:
        raise ValueError(f"Marca no encontrada en PLANTILLAS: {marca}")

    ruta_plantilla = plantillas[marca]
    if os.path.exists(ruta_plantilla):
        plantilla = Image.open(ruta_plantilla).convert("RGB")
    else:
        plantilla = _crear_plantilla_temporal(marca)

    draw = ImageDraw.Draw(plantilla)

    precio_principal, texto_lateral, texto_secundario = calcular_textos_precio(precio_unidad, precio_caja)
    if not precio_principal:
        raise ValueError(f"Producto sin precio válido: {producto}")

    # Producto / descripción
    # Nueva regla: tamaño fijo de letra. El texto se mide con ese tamaño y,
    # si no cabe en una línea, se parte en 2 líneas sin cortar palabras.
    producto_x = int(layout["producto"].get("x") or DEFAULT_LAYOUT["producto"]["x"])
    producto_y = int(layout["producto"].get("y") or DEFAULT_LAYOUT["producto"]["y"])
    font_producto = cargar_font_fijo(SIZE_PRODUCTO, font_name)
    lineas_producto = dividir_texto_por_ancho(producto, draw, font_producto, max_width=820)
    espacio_linea_producto = 95

    # La posición guardada sigue funcionando como referencia del bloque de 2 líneas.
    # Si es una sola línea, se baja medio espacio para quedar centrada visualmente.
    if len(lineas_producto) == 1:
        y_actual = producto_y + (espacio_linea_producto // 2)
    else:
        y_actual = producto_y

    for linea in lineas_producto:
        bbox = draw.textbbox((0, 0), linea, font=font_producto)
        ancho = bbox[2] - bbox[0]
        x = producto_x - (ancho // 2)
        draw.text((x, y_actual), linea, fill=COLOR_VERDE, font=font_producto)
        y_actual += espacio_linea_producto

    # Precio principal
    precio_x = int(layout["precio"].get("x") or DEFAULT_LAYOUT["precio"]["x"])
    precio_y = int(layout["precio"].get("y") or DEFAULT_LAYOUT["precio"]["y"])
    font_precio = ajustar_fuente(draw, precio_principal, 700, SIZE_PRECIO, font_name)
    draw.text((precio_x, precio_y), precio_principal, fill=COLOR_VERDE, font=font_precio, anchor="mm")

    # Lateral
    font_lateral = ajustar_fuente(draw, texto_lateral, 220, SIZE_LATERAL, font_name)
    lateral_cfg = layout.get("lateral", {})
    lateral_x = lateral_cfg.get("x")
    lateral_y = lateral_cfg.get("y")

    if lateral_x is None:
        bbox_precio = draw.textbbox((0, 0), precio_principal, font=font_precio)
        ancho_precio = bbox_precio[2] - bbox_precio[0]
        lateral_x = precio_x + (ancho_precio // 2) + 170
        lateral_x = min(lateral_x, 1750)

    if lateral_y is None:
        lateral_y = DEFAULT_LAYOUT["lateral"]["y"]

    draw.text((int(lateral_x), int(lateral_y)), texto_lateral, fill=COLOR_VERDE, font=font_lateral, anchor="mm")

    # Precio secundario
    if texto_secundario:
        sec_x = int(layout["secundario"].get("x") or DEFAULT_LAYOUT["secundario"]["x"])
        sec_y = int(layout["secundario"].get("y") or DEFAULT_LAYOUT["secundario"]["y"])
        font_secundario = ajustar_fuente(draw, texto_secundario, 500, SIZE_SECUNDARIO, font_name)
        draw.text((sec_x, sec_y), texto_secundario, fill=COLOR_VERDE, font=font_secundario, anchor="mm")

    return plantilla
