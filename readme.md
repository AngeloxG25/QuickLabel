# QuickLabel

**QuickLabel** es una aplicación de escritorio para Windows que permite generar etiquetas de precios desde un archivo Excel, usando plantillas gráficas personalizables, fuentes configurables, vista previa interactiva y salida en PNG o PDF listo para imprimir.

Desarrollado por **DevAngelo for Teba**.

---

## Descripción

QuickLabel está pensado para crear etiquetas de precios de forma rápida, visual y fácil de usar.  
El usuario puede seleccionar una lista de precios en Excel, elegir una plantilla, cambiar la fuente, ajustar visualmente la ubicación de los textos y generar las etiquetas en formato PNG o PDF.

La aplicación está desarrollada en Python con interfaz Tkinter y está preparada para compilarse en Windows usando Nuitka.

---

## Características principales

- Aplicación de escritorio para Windows.
- Interfaz gráfica con Tkinter.
- Compatible con pantallas escaladas al 125% o 150%.
- Selección manual del archivo Excel desde el programa.
- Lectura de Excel usando **openpyxl**.
- Generación de etiquetas en formato PNG.
- Generación de PDF en tamaño carta.
- Líneas de corte sutiles en el PDF.
- Limpieza automática de PNG temporales al generar PDF.
- Apertura automática de la carpeta de salida al generar PNG.
- Apertura automática del PDF final al generarlo.
- Vista previa interactiva de la etiqueta.
- Cambio de plantilla y fuente desde la interfaz.
- Ajuste de posiciones con el mouse:
  - descripción del producto,
  - precio principal,
  - texto lateral,
  - precio secundario.
- Configuración de rutas para:
  - carpeta de fuentes,
  - carpeta de plantillas,
  - carpeta de salida.
- Menú de información con nombre, versión y créditos.
- Icono personalizado para la aplicación.
- Preparado para distribuirse como ejecutable con Nuitka.

---

## Tecnologías utilizadas

- Python
- Tkinter
- Pillow
- openpyxl
- ReportLab
- Nuitka

---

## Estructura recomendada del proyecto

```text
QuickLabel/
├─ app.py
├─ config.py
├─ utils.py
├─ etiqueta_renderer.py
├─ generar_etiquetas.py
├─ generar_pdf.py
├─ config_font.json
├─ config_layout.json
├─ COMANDO_COMPILAR_NUITKA.txt
├─ gui/
│  ├─ __init__.py
│  └─ main_window.py
├─ assets/
│  └─ label_844652.ico
├─ fonts/
│  └─ Anton.ttf
├─ plantillas/
│  ├─ minutoverde.png
│  └─ gag.png
└─ salida/
```

> La carpeta `salida/` se crea automáticamente si no existe.

---

## Requisitos

Python 3.11 o superior recomendado.

Instalar dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install pillow openpyxl reportlab
```

Para compilar con Nuitka:

```powershell
python -m pip install nuitka ordered-set zstandard
```

> En versiones anteriores se utilizaba pandas, pero fue reemplazado por **openpyxl** para reducir tiempos de compilación y simplificar la distribución del ejecutable.

---

## Archivo Excel esperado

El archivo Excel debe contener como mínimo las siguientes columnas:

| Columna | Descripción |
|---|---|
| `DESCRIPCION` | Nombre o descripción del producto |
| `MARCA` | Nombre de la plantilla a utilizar |
| `PRECIO_UNIDAD` | Precio unitario |
| `PRECIO_CAJA` | Precio por caja |

Las columnas obligatorias son:

```text
DESCRIPCION
MARCA
```

Las columnas de precio son usadas si existen:

```text
PRECIO_UNIDAD
PRECIO_CAJA
```

Ejemplo:

| DESCRIPCION | MARCA | PRECIO_UNIDAD | PRECIO_CAJA |
|---|---|---:|---:|
| HABAS MINUTO VERDE 15X 1KL | MINUTO VERDE | 1290 | 15480 |
| AROS DE CEBOLLA MINUTO VERDE 10X 1KL | MINUTO VERDE | 1990 | 19900 |

---

## Plantillas disponibles

Las plantillas se cargan desde la carpeta configurada como `plantillas`.

Por defecto el proyecto considera:

```text
plantillas/
├─ minutoverde.png
└─ gag.png
```

Las marcas configuradas son:

```text
MINUTO VERDE
GAG
```

El valor de la columna `MARCA` en el Excel debe coincidir con una de las plantillas configuradas.

---

## Fuentes

Las fuentes se cargan desde la carpeta configurada como `fonts`.

Formatos aceptados:

```text
.ttf
.otf
```

Fuente por defecto:

```json
{
  "font_name": "Anton.ttf"
}
```

---

## Posiciones por defecto

Las posiciones base de los textos están configuradas así:

```json
{
  "producto": {
    "x": 545,
    "y": 192
  },
  "precio": {
    "x": 1400,
    "y": 299
  },
  "lateral": {
    "x": 1686,
    "y": 417
  },
  "secundario": {
    "x": 1603,
    "y": 518
  }
}
```

Estas posiciones pueden modificarse desde la vista previa arrastrando los elementos con el mouse.

---

## Uso en modo desarrollo

Ejecutar desde la raíz del proyecto:

```powershell
python app.py
```

Flujo recomendado:

1. Abrir el programa.
2. Seleccionar el archivo Excel.
3. Revisar los datos de ejemplo.
4. Elegir plantilla y fuente.
5. Ajustar posiciones si es necesario.
6. Generar archivos.

---

## Opciones de generación

El programa incluye tres acciones principales:

### Generar solo PNG

Genera una imagen PNG por cada producto válido del Excel.  
Al finalizar, abre automáticamente la carpeta de salida.

### Generar PNG + PDF, limpiar PNG y abrir PDF

Genera primero los PNG, luego crea un PDF carta con líneas de corte sutiles, elimina los PNG temporales y abre automáticamente el PDF final.

### Abrir carpeta de salida

Abre directamente la carpeta configurada para los archivos generados.

---

## Configuración de carpetas

Desde el menú **Ajustes** se pueden cambiar las ubicaciones de:

- carpeta de fonts,
- carpeta de plantillas,
- carpeta de salida.

Esto permite usar el programa en otro computador sin depender de rutas fijas.

---

## Archivos de configuración

| Archivo | Función |
|---|---|
| `config_font.json` | Guarda la fuente seleccionada |
| `config_layout.json` | Guarda las posiciones de los textos |
| `app_settings.json` | Guarda rutas configuradas para fonts, plantillas y salida |

---

## Información del programa

El programa define los siguientes datos:

```text
Nombre: QuickLabel
Versión: 1.5.0
Desarrollador: DevAngelo for Teba
Descripción: Generador de etiquetas de precios con vista previa interactiva.
```

---

## Compilar con Nuitka en Windows

Instalar requisitos dentro del entorno virtual:

```powershell
python -m pip install --upgrade pip
python -m pip install nuitka ordered-set zstandard pillow openpyxl reportlab
```

Ejecutar desde la raíz del proyecto, donde está `app.py`:

```powershell
python -m nuitka .\app.py `
  --standalone `
  --enable-plugin=tk-inter `
  --windows-console-mode=disable `
  --windows-icon-from-ico=assets/label_844652.ico `
  --output-dir=dist `
  --assume-yes-for-downloads `
  --show-progress `
  --nofollow-import-to=pytest `
  --nofollow-import-to=unittest `
  --nofollow-import-to=setuptools `
  --include-module=tkinter `
  --include-package=openpyxl `
  --include-package=PIL `
  --include-package=reportlab `
  --include-data-dir=fonts=fonts `
  --include-data-dir=plantillas=plantillas `
  --include-data-dir=assets=assets `
  --include-data-files=config_font.json=config_font.json `
  --include-data-files=config_layout.json=config_layout.json `
  --lto=no `
  --jobs=8 `
  --windows-file-description="Generador de Etiquetas" `
  --windows-product-name="QuickLabel" `
  --windows-company-name="DevAngelo for Teba" `
  --windows-file-version=1.5.0.0 `
  --windows-product-version=1.5.0.0 `
  --output-filename=QuickLabel.exe `
  --copyright="DevAngelo for Teba"
```

---

## Instalar en otro PC

Después de compilar, copiar la carpeta completa:

```text
dist\app.dist
```

Dentro estará el ejecutable:

```text
QuickLabel.exe
```

Recomendaciones:

- Copiar la carpeta completa, no solo el `.exe`.
- Mantener dentro las carpetas:
  - `assets`
  - `fonts`
  - `plantillas`
- El archivo Excel no necesita compilarse dentro del ejecutable, porque se selecciona desde el programa.
- En el primer uso, configurar las carpetas desde el menú **Ajustes** si corresponde.

---

## Notas de desarrollo

- La aplicación usa `openpyxl` para leer el Excel.
- El render de etiquetas está centralizado en `etiqueta_renderer.py`, de modo que la vista previa y la generación final usen la misma lógica.
- El PDF se genera con `reportlab`.
- Las imágenes se procesan con `Pillow`.
- La ventana principal se inicia desde `app.py`.

---

## Créditos

**QuickLabel**  
Desarrollado por **DevAngelo for Teba**.
