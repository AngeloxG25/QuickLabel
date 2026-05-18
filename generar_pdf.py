# =========================================================
# GENERAR PDF CARTA CON ETIQUETAS
# - Genera el PDF desde los PNG de salida
# - Agrega líneas de corte sutiles alrededor de cada etiqueta
# - Luego limpia/elimina los PNG usados, para dejar la carpeta ordenada
# =========================================================

import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from config import get_output_dir


def _dibujar_lineas_corte(pdf, x: float, y: float, width: float, height: float) -> None:
    """Dibuja líneas de corte suaves y poco invasivas.

    Se usa una línea gris clara, muy delgada y punteada para que sirva como
    guía de corte sin ensuciar visualmente la etiqueta impresa.
    """
    pdf.saveState()
    pdf.setStrokeColorRGB(0.72, 0.72, 0.72)  # gris claro
    pdf.setLineWidth(0.25)
    pdf.setDash(2, 3)  # línea punteada sutil
    pdf.rect(x, y, width, height, stroke=1, fill=0)
    pdf.restoreState()


def generar_pdf(limpiar_imagenes: bool = True, lineas_corte: bool = True) -> str:
    output_dir = get_output_dir()
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "etiquetas_carta.pdf")

    page_width, page_height = letter
    pdf = canvas.Canvas(pdf_path, pagesize=letter)

    etiqueta_width = 580
    etiqueta_height = 190
    margen_x = 10
    margen_y = 10
    espacio_vertical = 1

    x = margen_x
    y = page_height - etiqueta_height - margen_y

    imagenes = sorted(
        f for f in os.listdir(output_dir)
        if f.lower().endswith(".png")
    )

    if not imagenes:
        raise FileNotFoundError("No hay imágenes PNG en la carpeta salida para generar el PDF.")

    rutas_usadas = []

    for imagen in imagenes:
        ruta_imagen = os.path.join(output_dir, imagen)
        rutas_usadas.append(ruta_imagen)

        pdf.drawImage(
            ruta_imagen,
            x,
            y,
            width=etiqueta_width,
            height=etiqueta_height,
            preserveAspectRatio=True,
            mask="auto",
        )

        if lineas_corte:
            _dibujar_lineas_corte(pdf, x, y, etiqueta_width, etiqueta_height)

        y -= etiqueta_height + espacio_vertical
        if y < 0:
            pdf.showPage()
            y = page_height - etiqueta_height - margen_y

    pdf.save()
    print(f"[OK] PDF generado: {pdf_path}")

    if limpiar_imagenes:
        eliminadas = 0
        for ruta in rutas_usadas:
            try:
                os.remove(ruta)
                eliminadas += 1
            except OSError as exc:
                print(f"[WARN] No se pudo eliminar {ruta}: {exc}")
        print(f"[OK] Imágenes PNG limpiadas: {eliminadas}")

    return pdf_path
