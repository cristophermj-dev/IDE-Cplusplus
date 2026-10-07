"""
Editor de diagramas UML para MeriCode C++.

Este módulo proporciona un editor visual de diagramas de clases UML
con las siguientes funcionalidades:
- Crear, editar y eliminar clases UML (nombre, atributos, métodos).
- Crear relaciones entre clases (asociación, herencia, composición,
  agregación, dependencia).
- Mover y redimensionar clases en el lienzo.
- Guardar diagramas en formato XML.
- Exportar diagramas a PDF y PNG.
"""

import os
import sys
import math
import zlib
import struct
import xml.etree.ElementTree as ET
from xml.dom import minidom
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser

# Intentar importar Pillow para exportación PNG
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Intentar importar reportlab para exportación PDF
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors as rl_colors
    from reportlab.pdfgen import canvas as rl_canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ============================================================
# Fuente bitmap 8x8 (dominio público, font8x8_basic) para el exportador
# de PNG sin Pillow. Cada glifo son 8 bytes (filas), bit 0 = columna derecha.
_FONT_8X8_BASIC = [
    (0, 0, 0, 0, 0, 0, 0, 0),
    (24, 60, 60, 24, 24, 0, 24, 0),
    (54, 54, 0, 0, 0, 0, 0, 0),
    (54, 54, 127, 54, 127, 54, 54, 0),
    (12, 62, 3, 30, 48, 31, 12, 0),
    (0, 99, 51, 24, 12, 102, 99, 0),
    (28, 54, 28, 110, 59, 51, 110, 0),
    (6, 6, 3, 0, 0, 0, 0, 0),
    (24, 12, 6, 6, 6, 12, 24, 0),
    (6, 12, 24, 24, 24, 12, 6, 0),
    (0, 102, 60, 255, 60, 102, 0, 0),
    (0, 12, 12, 63, 12, 12, 0, 0),
    (0, 0, 0, 0, 0, 12, 12, 6),
    (0, 0, 0, 63, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 12, 12, 0),
    (96, 48, 24, 12, 6, 3, 1, 0),
    (62, 99, 115, 123, 111, 103, 62, 0),
    (12, 14, 12, 12, 12, 12, 63, 0),
    (30, 51, 48, 28, 6, 51, 63, 0),
    (30, 51, 48, 28, 48, 51, 30, 0),
    (56, 60, 54, 51, 127, 48, 120, 0),
    (63, 3, 31, 48, 48, 51, 30, 0),
    (28, 6, 3, 31, 51, 51, 30, 0),
    (63, 51, 48, 24, 12, 12, 12, 0),
    (30, 51, 51, 30, 51, 51, 30, 0),
    (30, 51, 51, 62, 48, 24, 14, 0),
    (0, 12, 12, 0, 0, 12, 12, 0),
    (0, 12, 12, 0, 0, 12, 12, 6),
    (24, 12, 6, 3, 6, 12, 24, 0),
    (0, 0, 63, 0, 0, 63, 0, 0),
    (6, 12, 24, 48, 24, 12, 6, 0),
    (30, 51, 48, 24, 12, 0, 12, 0),
    (62, 99, 123, 123, 123, 3, 30, 0),
    (12, 30, 51, 51, 63, 51, 51, 0),
    (63, 102, 102, 62, 102, 102, 63, 0),
    (60, 102, 3, 3, 3, 102, 60, 0),
    (31, 54, 102, 102, 102, 54, 31, 0),
    (127, 70, 22, 30, 22, 70, 127, 0),
    (127, 70, 22, 30, 22, 6, 15, 0),
    (60, 102, 3, 3, 115, 102, 124, 0),
    (51, 51, 51, 63, 51, 51, 51, 0),
    (30, 12, 12, 12, 12, 12, 30, 0),
    (120, 48, 48, 48, 51, 51, 30, 0),
    (103, 102, 54, 30, 54, 102, 103, 0),
    (15, 6, 6, 6, 70, 102, 127, 0),
    (99, 119, 127, 127, 107, 99, 99, 0),
    (99, 103, 111, 123, 115, 99, 99, 0),
    (28, 54, 99, 99, 99, 54, 28, 0),
    (63, 102, 102, 62, 6, 6, 15, 0),
    (30, 51, 51, 51, 59, 30, 56, 0),
    (63, 102, 102, 62, 54, 102, 103, 0),
    (30, 51, 7, 14, 56, 51, 30, 0),
    (63, 45, 12, 12, 12, 12, 30, 0),
    (51, 51, 51, 51, 51, 51, 63, 0),
    (51, 51, 51, 51, 51, 30, 12, 0),
    (99, 99, 99, 107, 127, 119, 99, 0),
    (99, 99, 54, 28, 28, 54, 99, 0),
    (51, 51, 51, 30, 12, 12, 30, 0),
    (127, 99, 49, 24, 76, 102, 127, 0),
    (30, 6, 6, 6, 6, 6, 30, 0),
    (3, 6, 12, 24, 48, 96, 64, 0),
    (30, 24, 24, 24, 24, 24, 30, 0),
    (8, 28, 54, 99, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 255),
    (12, 12, 24, 0, 0, 0, 0, 0),
    (0, 0, 30, 48, 62, 51, 110, 0),
    (7, 6, 6, 62, 102, 102, 59, 0),
    (0, 0, 30, 51, 3, 51, 30, 0),
    (56, 48, 48, 62, 51, 51, 110, 0),
    (0, 0, 30, 51, 63, 3, 30, 0),
    (28, 54, 6, 15, 6, 6, 15, 0),
    (0, 0, 110, 51, 51, 62, 48, 31),
    (7, 6, 54, 110, 102, 102, 103, 0),
    (12, 0, 14, 12, 12, 12, 30, 0),
    (48, 0, 48, 48, 48, 51, 51, 30),
    (7, 6, 102, 54, 30, 54, 103, 0),
    (14, 12, 12, 12, 12, 12, 30, 0),
    (0, 0, 51, 127, 127, 107, 99, 0),
    (0, 0, 31, 51, 51, 51, 51, 0),
    (0, 0, 30, 51, 51, 51, 30, 0),
    (0, 0, 59, 102, 102, 62, 6, 15),
    (0, 0, 110, 51, 51, 62, 48, 120),
    (0, 0, 59, 110, 102, 6, 15, 0),
    (0, 0, 62, 3, 30, 48, 31, 0),
    (8, 12, 62, 12, 12, 44, 24, 0),
    (0, 0, 51, 51, 51, 51, 110, 0),
    (0, 0, 51, 51, 51, 30, 12, 0),
    (0, 0, 99, 107, 127, 127, 54, 0),
    (0, 0, 99, 54, 28, 54, 99, 0),
    (0, 0, 51, 51, 51, 62, 48, 31),
    (0, 0, 63, 25, 12, 38, 63, 0),
    (56, 12, 12, 7, 12, 12, 56, 0),
    (24, 24, 24, 0, 24, 24, 24, 0),
    (7, 12, 12, 56, 12, 12, 7, 0),
    (110, 59, 0, 0, 0, 0, 0, 0),
]



class _PngImage:
    """Rasterizador RGB mínimo para generar PNG sin depender de Pillow."""

    def __init__(self, width, height, bg=(255, 255, 255)):
        self.width = int(width)
        self.height = int(height)
        row = bytes(bg) * self.width
        self._rows = [bytearray(row) for _ in range(self.height)]

    def _set(self, x, y, rgb):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = x * 3
            self._rows[y][i] = rgb[0]
            self._rows[y][i + 1] = rgb[1]
            self._rows[y][i + 2] = rgb[2]

    def fill_rect(self, x0, y0, x1, y1, rgb):
        x0, x1 = max(0, int(x0)), min(self.width, int(x1))
        y0, y1 = max(0, int(y0)), min(self.height, int(y1))
        for y in range(y0, y1):
            for x in range(x0, x1):
                self._set(x, y, rgb)

    def stroke_rect(self, x0, y0, x1, y1, rgb, width=2):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        for t in range(width):
            self.fill_rect(x0 + t, y0 + t, x1 - t, y0 + t + 1, rgb)
            self.fill_rect(x0 + t, y1 - t - 1, x1 - t, y1 - t, rgb)
            self.fill_rect(x0 + t, y0 + t, x0 + t + 1, y1 - t, rgb)
            self.fill_rect(x1 - t - 1, y0 + t, x1 - t, y1 - t, rgb)

    def line(self, x0, y0, x1, y1, rgb, width=2):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        r = max(1, width // 2)
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self._fill_disc(x0, y0, r, rgb)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def _fill_disc(self, cx, cy, r, rgb):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r + 1:
                    self._set(cx + dx, cy + dy, rgb)

    def text(self, x, y, s, rgb, scale=1):
        for ch in s:
            self._draw_glyph(x, y, ch, rgb, scale)
            x += 8 * scale

    def _draw_glyph(self, x, y, ch, rgb, scale):
        idx = ord(ch) - 0x20
        if not (0 <= idx < len(_FONT_8X8_BASIC)):
            idx = ord("?") - 0x20
        glyph = _FONT_8X8_BASIC[idx]
        for row in range(8):
            bits = glyph[row]
            for col in range(8):
                if bits & (1 << col):
                    px = x + (7 - col) * scale
                    py = y + row * scale
                    for dy in range(scale):
                        for dx in range(scale):
                            self._set(px + dx, py + dy, rgb)

    def to_png_bytes(self):
        raw = bytearray()
        for row in self._rows:
            raw.append(0)
            raw += row
        compressed = zlib.compress(bytes(raw), 9)

        def chunk(tag, data):
            c = struct.pack(">I", len(data)) + tag + data
            c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            return c

        ihdr = struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", compressed)
                + chunk(b"IEND", b""))



def _hex_to_rgb(hex_color):
    """Convierte un color hexadecimal '#RRGGBB' a una tupla RGB."""
    h = (hex_color or "#FFFFFF").lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) != 6:
        return (255, 255, 255)
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (255, 255, 255)


def _transliterate_ascii(text):
    """Traduce caracteres no ASCII a su equivalente ASCII para el PNG."""
    mapping = {
        "á": "a", "à": "a", "â": "a", "ä": "a", "ã": "a", "å": "a",
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "í": "i", "ì": "i", "î": "i", "ï": "i",
        "ó": "o", "ò": "o", "ô": "o", "ö": "o", "õ": "o",
        "ú": "u", "ù": "u", "û": "u", "ü": "u",
        "ñ": "n", "ç": "c", "ý": "y", "ÿ": "y",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U",
        "Ñ": "N", "Ç": "C",
        "«": "<<", "»": ">>", "“": '"', "”": '"', "‘": "'", "’": "'",
        "—": "-", "–": "-", "•": "*", "·": ".", "…": "...",
    }
    return "".join(
        mapping.get(ch, ch if 32 <= ord(ch) < 127 else "?") for ch in text
    )


def _pdf_escape(text):
    """Escapa texto para usarlo en una cadena literal de PDF."""
    text = text.encode("latin-1", "replace").decode("latin-1")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_pdf_file(file_path, width, height, content_bytes):
    """Escribe un PDF mínimo con la biblioteca estándar de Python."""
    header = b"%PDF-1.4\n"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] "
         "/Resources << /Font << /F1 4 0 R /F2 5 0 R /F3 6 0 R >> >> "
         "/Contents 7 0 R >>" % (width, height)).encode("ascii"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>",
        b"<< /Length %d >>\nstream\n" % len(content_bytes) + content_bytes + b"\nendstream",
    ]

    out = bytearray(header)
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"

    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1, xref_pos)

    with open(file_path, "wb") as f:
        f.write(bytes(out))



# Modelos de datos
# ============================================================

class UMLAttribute:
    """Atributo de una clase UML."""

    def __init__(self, name="", type_name="", visibility="+", is_static=False):
        self.name = name
        self.type_name = type_name
        self.visibility = visibility  # +, -, #, ~
        self.is_static = is_static

    def to_string(self):
        """Convierte el atributo a su representación textual."""
        prefix = self.visibility if self.visibility else "+"
        static = " {static}" if self.is_static else ""
        if self.type_name:
            return f"{prefix} {self.name}: {self.type_name}{static}"
        return f"{prefix} {self.name}{static}"

    def to_xml(self):
        """Convierte el atributo a XML."""
        elem = ET.Element("attribute")
        elem.set("name", self.name)
        elem.set("type", self.type_name)
        elem.set("visibility", self.visibility)
        elem.set("static", str(self.is_static).lower())
        return elem

    @classmethod
    def from_xml(cls, elem):
        """Crea un atributo desde XML."""
        return cls(
            name=elem.get("name", ""),
            type_name=elem.get("type", ""),
            visibility=elem.get("visibility", "+"),
            is_static=elem.get("static", "false").lower() == "true",
        )


class UMLMethod:
    """Método de una clase UML."""

    def __init__(self, name="", return_type="void", params="", visibility="+",
                 is_static=False, is_abstract=False):
        self.name = name
        self.return_type = return_type
        self.params = params
        self.visibility = visibility
        self.is_static = is_static
        self.is_abstract = is_abstract

    def to_string(self):
        """Convierte el método a su representación textual."""
        prefix = self.visibility if self.visibility else "+"
        static = " {static}" if self.is_static else ""
        abstract = " {abstract}" if self.is_abstract else ""
        ret = f": {self.return_type}" if self.return_type else ""
        return f"{prefix} {self.name}({self.params}){ret}{static}{abstract}"

    def to_xml(self):
        """Convierte el método a XML."""
        elem = ET.Element("method")
        elem.set("name", self.name)
        elem.set("return_type", self.return_type)
        elem.set("params", self.params)
        elem.set("visibility", self.visibility)
        elem.set("static", str(self.is_static).lower())
        elem.set("abstract", str(self.is_abstract).lower())
        return elem

    @classmethod
    def from_xml(cls, elem):
        """Crea un método desde XML."""
        return cls(
            name=elem.get("name", ""),
            return_type=elem.get("return_type", "void"),
            params=elem.get("params", ""),
            visibility=elem.get("visibility", "+"),
            is_static=elem.get("static", "false").lower() == "true",
            is_abstract=elem.get("abstract", "false").lower() == "true",
        )


class UMLClass:
    """Clase UML con nombre, atributos y métodos."""

    def __init__(self, name="Clase", x=50, y=50, width=180, height=120,
                 color="#E8F0FE", text_color="#000000"):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.text_color = text_color
        self.attributes = []
        self.methods = []
        self.is_interface = False
        self.is_abstract = False

    def add_attribute(self, attr):
        """Añade un atributo a la clase."""
        self.attributes.append(attr)
        self._recalculate_height()

    def add_method(self, method):
        """Añade un método a la clase."""
        self.methods.append(method)
        self._recalculate_height()

    def _recalculate_height(self):
        """Recalcula la altura de la clase según su contenido."""
        # Altura base: nombre + separadores + atributos + métodos
        attr_count = len(self.attributes)
        method_count = len(self.methods)
        # Cada atributo/método ocupa ~20px
        content_height = 40 + (attr_count * 20) + (method_count * 20)
        self.height = max(120, content_height)

    def contains_point(self, px, py):
        """Verifica si un punto está dentro de la clase."""
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)

    def to_xml(self):
        """Convierte la clase a XML."""
        elem = ET.Element("class")
        elem.set("name", self.name)
        elem.set("x", str(self.x))
        elem.set("y", str(self.y))
        elem.set("width", str(self.width))
        elem.set("height", str(self.height))
        elem.set("color", self.color)
        elem.set("text_color", self.text_color)
        elem.set("interface", str(self.is_interface).lower())
        elem.set("abstract", str(self.is_abstract).lower())

        attrs_elem = ET.SubElement(elem, "attributes")
        for attr in self.attributes:
            attrs_elem.append(attr.to_xml())

        methods_elem = ET.SubElement(elem, "methods")
        for method in self.methods:
            methods_elem.append(method.to_xml())

        return elem

    @classmethod
    def from_xml(cls, elem):
        """Crea una clase desde XML."""
        cls_obj = cls(
            name=elem.get("name", "Clase"),
            x=int(elem.get("x", 50)),
            y=int(elem.get("y", 50)),
            width=int(elem.get("width", 180)),
            height=int(elem.get("height", 120)),
            color=elem.get("color", "#E8F0FE"),
            text_color=elem.get("text_color", "#000000"),
        )
        cls_obj.is_interface = elem.get("interface", "false").lower() == "true"
        cls_obj.is_abstract = elem.get("abstract", "false").lower() == "true"

        attrs_elem = elem.find("attributes")
        if attrs_elem is not None:
            for attr_elem in attrs_elem.findall("attribute"):
                cls_obj.attributes.append(UMLAttribute.from_xml(attr_elem))

        methods_elem = elem.find("methods")
        if methods_elem is not None:
            for method_elem in methods_elem.findall("method"):
                cls_obj.methods.append(UMLMethod.from_xml(method_elem))

        cls_obj._recalculate_height()
        return cls_obj


class UMLRelation:
    """Relación entre dos clases UML."""

    # Tipos de relación
    ASSOCIATION = "association"
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    DEPENDENCY = "dependency"

    TYPE_LABELS = {
        ASSOCIATION: "Asociación",
        INHERITANCE: "Herencia",
        COMPOSITION: "Composición",
        AGGREGATION: "Agregación",
        DEPENDENCY: "Dependencia",
    }

    def __init__(self, source_id, target_id, rel_type=ASSOCIATION,
                 label="", source_multiplicity="", target_multiplicity=""):
        self.source_id = source_id
        self.target_id = target_id
        self.rel_type = rel_type
        self.label = label
        self.source_multiplicity = source_multiplicity
        self.target_multiplicity = target_multiplicity

    def to_xml(self):
        """Convierte la relación a XML."""
        elem = ET.Element("relation")
        elem.set("source", str(self.source_id))
        elem.set("target", str(self.target_id))
        elem.set("type", self.rel_type)
        elem.set("label", self.label)
        elem.set("source_multiplicity", self.source_multiplicity)
        elem.set("target_multiplicity", self.target_multiplicity)
        return elem

    @classmethod
    def from_xml(cls, elem):
        """Crea una relación desde XML."""
        return cls(
            source_id=int(elem.get("source", 0)),
            target_id=int(elem.get("target", 0)),
            rel_type=elem.get("type", cls.ASSOCIATION),
            label=elem.get("label", ""),
            source_multiplicity=elem.get("source_multiplicity", ""),
            target_multiplicity=elem.get("target_multiplicity", ""),
        )


# ============================================================
# Diálogos de edición
# ============================================================

class AttributeDialog(tk.Toplevel):
    """Diálogo para crear/editar un atributo UML."""

    def __init__(self, parent, title="Atributo", attr=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self.result = None

        # Variables
        self.name_var = tk.StringVar(value=attr.name if attr else "")
        self.type_var = tk.StringVar(value=attr.type_name if attr else "")
        self.visibility_var = tk.StringVar(value=attr.visibility if attr else "+")
        self.static_var = tk.BooleanVar(value=attr.is_static if attr else False)

        self._build_ui()
        self._center_on_parent(parent)

    def _build_ui(self):
        """Construye la interfaz del diálogo."""
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Nombre
        ttk.Label(frame, text="Nombre:").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.name_var, width=25).grid(
            row=0, column=1, sticky="ew", pady=3, padx=(5, 0))

        # Tipo
        ttk.Label(frame, text="Tipo:").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.type_var, width=25).grid(
            row=1, column=1, sticky="ew", pady=3, padx=(5, 0))

        # Visibilidad
        ttk.Label(frame, text="Visibilidad:").grid(row=2, column=0, sticky="w", pady=3)
        vis_frame = ttk.Frame(frame)
        vis_frame.grid(row=2, column=1, sticky="w", pady=3, padx=(5, 0))
        for vis, label in [("+", "+ público"), ("-", "- privado"),
                           ("#", "# protegido"), ("~", "~ paquete")]:
            ttk.Radiobutton(vis_frame, text=label, value=vis,
                            variable=self.visibility_var).pack(side="left", padx=3)

        # Estático
        ttk.Checkbutton(frame, text="Estático", variable=self.static_var).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=5)

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btn_frame, text="Aceptar", command=self._on_accept).pack(
            side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(
            side="left", padx=5)

        frame.columnconfigure(1, weight=1)

    def _on_accept(self):
        """Acepta el diálogo."""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Advertencia", "El nombre no puede estar vacío.",
                                   parent=self)
            return
        self.result = UMLAttribute(
            name=name,
            type_name=self.type_var.get().strip(),
            visibility=self.visibility_var.get(),
            is_static=self.static_var.get(),
        )
        self.destroy()

    def _center_on_parent(self, parent):
        """Centra el diálogo sobre el padre."""
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")


class MethodDialog(tk.Toplevel):
    """Diálogo para crear/editar un método UML."""

    def __init__(self, parent, title="Método", method=None, class_name=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self.result = None
        self.class_name = (class_name or "").strip()

        # Variables
        self.name_var = tk.StringVar(value=method.name if method else "")
        self.return_var = tk.StringVar(value=method.return_type if method else "void")
        self.params_var = tk.StringVar(value=method.params if method else "")
        self.visibility_var = tk.StringVar(value=method.visibility if method else "+")
        self.static_var = tk.BooleanVar(value=method.is_static if method else False)
        self.abstract_var = tk.BooleanVar(value=method.is_abstract if method else False)

        self._build_ui()
        self.name_var.trace_add("write", lambda *a: self._update_return_state())
        self._update_return_state()
        self._center_on_parent(parent)

    def _build_ui(self):
        """Construye la interfaz del diálogo."""
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Nombre
        ttk.Label(frame, text="Nombre:").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.name_var, width=25).grid(
            row=0, column=1, sticky="ew", pady=3, padx=(5, 0))

        # Tipo de retorno
        ttk.Label(frame, text="Retorno:").grid(row=1, column=0, sticky="w", pady=3)
        self.return_entry = ttk.Entry(frame, textvariable=self.return_var, width=25)
        self.return_entry.grid(row=1, column=1, sticky="ew", pady=3, padx=(5, 0))
        self.return_hint = ttk.Label(frame, text="", foreground="#888888")
        self.return_hint.grid(row=2, column=0, columnspan=2, sticky="w", padx=(5, 0))

        # Parámetros
        ttk.Label(frame, text="Parámetros:").grid(row=3, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.params_var, width=25).grid(
            row=3, column=1, sticky="ew", pady=3, padx=(5, 0))
        ttk.Label(frame, text="(ej: int a, string b)").grid(
            row=4, column=1, sticky="w", padx=(5, 0))

        # Visibilidad
        ttk.Label(frame, text="Visibilidad:").grid(row=5, column=0, sticky="w", pady=3)
        vis_frame = ttk.Frame(frame)
        vis_frame.grid(row=5, column=1, sticky="w", pady=3, padx=(5, 0))
        for vis, label in [("+", "+ público"), ("-", "- privado"),
                           ("#", "# protegido"), ("~", "~ paquete")]:
            ttk.Radiobutton(vis_frame, text=label, value=vis,
                            variable=self.visibility_var).pack(side="left", padx=3)

        # Opciones
        opts_frame = ttk.Frame(frame)
        opts_frame.grid(row=6, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Checkbutton(opts_frame, text="Estático",
                        variable=self.static_var).pack(side="left", padx=5)
        ttk.Checkbutton(opts_frame, text="Abstracto",
                        variable=self.abstract_var).pack(side="left", padx=5)

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btn_frame, text="Aceptar", command=self._on_accept).pack(
            side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(
            side="left", padx=5)

        frame.columnconfigure(1, weight=1)

    def _is_constructor_or_destructor(self, name):
        """Determina si un nombre corresponde a un constructor o destructor."""
        name = (name or "").strip()
        if not name:
            return False
        if self.class_name and name == self.class_name:
            return True
        if name.startswith("~"):
            return True
        return False

    def _update_return_state(self):
        """Activa/desactiva el campo de retorno según el nombre del método."""
        is_special = self._is_constructor_or_destructor(self.name_var.get())
        if is_special:
            self.return_var.set("")
            self.return_entry.configure(state="disabled")
            self.return_hint.configure(
                text="Constructor/destructor: no llevan tipo de retorno")
        else:
            self.return_entry.configure(state="normal")
            if not self.return_var.get():
                self.return_var.set("void")
            self.return_hint.configure(text="")

    def _on_accept(self):
        """Acepta el diálogo."""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Advertencia", "El nombre no puede estar vacío.",
                                   parent=self)
            return

        if self._is_constructor_or_destructor(name):
            return_type = ""
        else:
            return_type = self.return_var.get().strip() or "void"

        self.result = UMLMethod(
            name=name,
            return_type=return_type,
            params=self.params_var.get().strip(),
            visibility=self.visibility_var.get(),
            is_static=self.static_var.get(),
            is_abstract=self.abstract_var.get(),
        )
        self.destroy()

    def _center_on_parent(self, parent):
        """Centra el diálogo sobre el padre."""
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")


class ClassDialog(tk.Toplevel):
    """Diálogo para crear/editar una clase UML."""

    def __init__(self, parent, title="Clase UML", uml_class=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("560x600")
        self.minsize(520, 540)
        self.resizable(True, True)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self.result = None
        self.uml_class = uml_class

        # Variables
        self.name_var = tk.StringVar(value=uml_class.name if uml_class else "")
        self.interface_var = tk.BooleanVar(
            value=uml_class.is_interface if uml_class else False)
        self.abstract_var = tk.BooleanVar(
            value=uml_class.is_abstract if uml_class else False)
        self.color_var = tk.StringVar(
            value=uml_class.color if uml_class else "#E8F0FE")

        self._build_ui()
        self._center_on_parent(parent)

    def _build_ui(self):
        """Construye la interfaz del diálogo."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Nombre
        ttk.Label(main_frame, text="Nombre de la clase:").pack(anchor="w", pady=2)
        ttk.Entry(main_frame, textvariable=self.name_var).pack(
            fill="x", pady=2)

        # Opciones
        opts_frame = ttk.Frame(main_frame)
        opts_frame.pack(fill="x", pady=5)
        ttk.Checkbutton(opts_frame, text="Interfaz",
                        variable=self.interface_var).pack(side="left", padx=5)
        ttk.Checkbutton(opts_frame, text="Clase abstracta",
                        variable=self.abstract_var).pack(side="left", padx=5)

        # Color
        color_frame = ttk.Frame(main_frame)
        color_frame.pack(fill="x", pady=5)
        ttk.Label(color_frame, text="Color:").pack(side="left", padx=5)
        self.color_btn = tk.Button(color_frame, text="Seleccionar color",
                                   command=self._choose_color, width=18)
        self.color_btn.pack(side="left", padx=5)
        self.color_preview = tk.Label(color_frame, text="  ",
                                      bg=self.color_var.get(), width=5)
        self.color_preview.pack(side="left", padx=5)

        # Separador
        ttk.Separator(main_frame).pack(fill="x", pady=8)

        # Atributos
        ttk.Label(main_frame, text="Atributos:").pack(anchor="w", pady=2)
        attrs_frame = ttk.Frame(main_frame)
        attrs_frame.pack(fill="both", expand=True, pady=2)

        self.attrs_list = tk.Listbox(attrs_frame, height=5)
        self.attrs_list.pack(side="left", fill="both", expand=True)
        attrs_scroll = ttk.Scrollbar(attrs_frame, orient="vertical",
                                     command=self.attrs_list.yview)
        attrs_scroll.pack(side="right", fill="y")
        self.attrs_list.configure(yscrollcommand=attrs_scroll.set)

        attrs_btns = ttk.Frame(main_frame)
        attrs_btns.pack(fill="x", pady=2)
        ttk.Button(attrs_btns, text="Añadir", width=10,
                   command=self._add_attribute).pack(side="left", padx=2)
        ttk.Button(attrs_btns, text="Editar", width=10,
                   command=self._edit_attribute).pack(side="left", padx=2)
        ttk.Button(attrs_btns, text="Eliminar", width=10,
                   command=self._delete_attribute).pack(side="left", padx=2)

        # Separador
        ttk.Separator(main_frame).pack(fill="x", pady=8)

        # Métodos
        ttk.Label(main_frame, text="Métodos:").pack(anchor="w", pady=2)
        methods_frame = ttk.Frame(main_frame)
        methods_frame.pack(fill="both", expand=True, pady=2)

        self.methods_list = tk.Listbox(methods_frame, height=5)
        self.methods_list.pack(side="left", fill="both", expand=True)
        methods_scroll = ttk.Scrollbar(methods_frame, orient="vertical",
                                       command=self.methods_list.yview)
        methods_scroll.pack(side="right", fill="y")
        self.methods_list.configure(yscrollcommand=methods_scroll.set)

        methods_btns = ttk.Frame(main_frame)
        methods_btns.pack(fill="x", pady=2)
        ttk.Button(methods_btns, text="Añadir", width=10,
                   command=self._add_method).pack(side="left", padx=2)
        ttk.Button(methods_btns, text="Editar", width=10,
                   command=self._edit_method).pack(side="left", padx=2)
        ttk.Button(methods_btns, text="Eliminar", width=10,
                   command=self._delete_method).pack(side="left", padx=2)

        # Botones finales
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="Aceptar", command=self._on_accept).pack(
            side="right", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(
            side="right", padx=5)

        # Cargar datos existentes
        self._refresh_lists()

    def _choose_color(self):
        """Abre el selector de color."""
        color = colorchooser.askcolor(color=self.color_var.get(),
                                      parent=self)
        if color[1]:
            self.color_var.set(color[1])
            self.color_preview.configure(bg=color[1])

    def _refresh_lists(self):
        """Actualiza las listas de atributos y métodos."""
        self.attrs_list.delete(0, "end")
        for attr in (self.uml_class.attributes if self.uml_class else []):
            self.attrs_list.insert("end", attr.to_string())

        self.methods_list.delete(0, "end")
        for method in (self.uml_class.methods if self.uml_class else []):
            self.methods_list.insert("end", method.to_string())

    def _add_attribute(self):
        """Añade un atributo."""
        dlg = AttributeDialog(self, "Nuevo atributo")
        self.wait_window(dlg)
        if dlg.result:
            if self.uml_class is None:
                self.uml_class = UMLClass(name=self.name_var.get() or "Clase")
            self.uml_class.attributes.append(dlg.result)
            self._refresh_lists()

    def _edit_attribute(self):
        """Edita un atributo seleccionado."""
        selection = self.attrs_list.curselection()
        if not selection:
            return
        idx = selection[0]
        if self.uml_class is None or idx >= len(self.uml_class.attributes):
            return
        dlg = AttributeDialog(self, "Editar atributo",
                              self.uml_class.attributes[idx])
        self.wait_window(dlg)
        if dlg.result:
            self.uml_class.attributes[idx] = dlg.result
            self._refresh_lists()

    def _delete_attribute(self):
        """Elimina un atributo seleccionado."""
        selection = self.attrs_list.curselection()
        if not selection:
            return
        idx = selection[0]
        if self.uml_class is None or idx >= len(self.uml_class.attributes):
            return
        del self.uml_class.attributes[idx]
        self._refresh_lists()

    def _add_method(self):
        """Añade un método."""
        dlg = MethodDialog(self, "Nuevo método", class_name=self.name_var.get())
        self.wait_window(dlg)
        if dlg.result:
            if self.uml_class is None:
                self.uml_class = UMLClass(name=self.name_var.get() or "Clase")
            self.uml_class.methods.append(dlg.result)
            self._refresh_lists()

    def _edit_method(self):
        """Edita un método seleccionado."""
        selection = self.methods_list.curselection()
        if not selection:
            return
        idx = selection[0]
        if self.uml_class is None or idx >= len(self.uml_class.methods):
            return
        dlg = MethodDialog(self, "Editar método",
                           self.uml_class.methods[idx],
                           class_name=self.name_var.get())
        self.wait_window(dlg)
        if dlg.result:
            self.uml_class.methods[idx] = dlg.result
            self._refresh_lists()

    def _delete_method(self):
        """Elimina un método seleccionado."""
        selection = self.methods_list.curselection()
        if not selection:
            return
        idx = selection[0]
        if self.uml_class is None or idx >= len(self.uml_class.methods):
            return
        del self.uml_class.methods[idx]
        self._refresh_lists()

    def _on_accept(self):
        """Acepta el diálogo."""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Advertencia", "El nombre no puede estar vacío.",
                                   parent=self)
            return

        if self.uml_class is None:
            self.uml_class = UMLClass(name=name)
        else:
            self.uml_class.name = name

        self.uml_class.is_interface = self.interface_var.get()
        self.uml_class.is_abstract = self.abstract_var.get()
        self.uml_class.color = self.color_var.get()
        self.uml_class._recalculate_height()

        self.result = self.uml_class
        self.destroy()

    def _center_on_parent(self, parent):
        """Centra el diálogo sobre el padre."""
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")


class RelationDialog(tk.Toplevel):
    """Diálogo para crear/editar una relación UML."""

    def __init__(self, parent, title="Relación", relation=None,
                 class_names=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("480x300")
        self.minsize(440, 260)
        self.resizable(True, True)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self.result = None
        self.class_names = class_names or []

        # Mostrar la etiqueta legible del tipo de relación
        if relation is not None:
            initial_type = UMLRelation.TYPE_LABELS.get(
                relation.rel_type,
                UMLRelation.TYPE_LABELS[UMLRelation.ASSOCIATION],
            )
        else:
            initial_type = UMLRelation.TYPE_LABELS[UMLRelation.ASSOCIATION]

        # Variables
        self.type_var = tk.StringVar(value=initial_type)
        self.label_var = tk.StringVar(value=relation.label if relation else "")
        self.source_mult_var = tk.StringVar(
            value=relation.source_multiplicity if relation else "")
        self.target_mult_var = tk.StringVar(
            value=relation.target_multiplicity if relation else "")

        self._build_ui()
        self._center_on_parent(parent)

    def _build_ui(self):
        """Construye la interfaz del diálogo."""
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        # Tipo de relación
        ttk.Label(frame, text="Tipo de relación:").grid(
            row=0, column=0, sticky="w", pady=3)
        type_combo = ttk.Combobox(frame, textvariable=self.type_var,
                                  state="readonly", width=20)
        type_combo["values"] = list(UMLRelation.TYPE_LABELS.values())
        type_combo.grid(row=0, column=1, sticky="ew", pady=3, padx=(5, 0))

        # Etiqueta
        ttk.Label(frame, text="Etiqueta:").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.label_var, width=25).grid(
            row=1, column=1, sticky="ew", pady=3, padx=(5, 0))

        # Multiplicidades
        ttk.Label(frame, text="Multiplicidad origen:").grid(
            row=2, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.source_mult_var, width=10).grid(
            row=2, column=1, sticky="w", pady=3, padx=(5, 0))

        ttk.Label(frame, text="Multiplicidad destino:").grid(
            row=3, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.target_mult_var, width=10).grid(
            row=3, column=1, sticky="w", pady=3, padx=(5, 0))

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btn_frame, text="Aceptar", command=self._on_accept).pack(
            side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(
            side="left", padx=5)

        frame.columnconfigure(1, weight=1)

    def _on_accept(self):
        """Acepta el diálogo."""
        # Convertir la etiqueta legible al valor interno del tipo
        label_to_key = {v: k for k, v in UMLRelation.TYPE_LABELS.items()}
        rel_type = label_to_key.get(self.type_var.get(), UMLRelation.ASSOCIATION)

        self.result = UMLRelation(
            source_id=0,  # Se actualizará después
            target_id=0,
            rel_type=rel_type,
            label=self.label_var.get().strip(),
            source_multiplicity=self.source_mult_var.get().strip(),
            target_multiplicity=self.target_mult_var.get().strip(),
        )
        self.destroy()

    def _center_on_parent(self, parent):
        """Centra el diálogo sobre el padre."""
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")


# ============================================================
# Editor UML principal
# ============================================================

class UMLEditor(tk.Frame):
    """Editor visual de diagramas de clases UML."""

    RESIZE_HANDLE = 7

    def __init__(self, parent, ide=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.ide = ide

        # Datos del diagrama
        self.classes = {}  # id -> UMLClass
        self.relations = []  # [UMLRelation]
        self.next_class_id = 0

        # Estado de interacción
        self.selected_class_id = None
        self.drag_offset = None
        self.dragging = False
        self.resizing = False
        self.resize_corner = None
        self.resize_start = None
        self.creating_relation = False
        self.relation_source_id = None
        self.relation_temp_line = None
        self.relation_temp_coords = None
        # Arrastre de una flecha de relación desde el panel lateral
        self._rel_drag_type = None
        self._rel_drag_active = False
        self._rel_drag_anchor = None

        # Zoom
        self.zoom_factor = 1.0

        # Colores del tema
        self.bg_color = "#FFFFFF"
        self.grid_color = "#E0E0E0"
        self.line_color = "#333333"
        self.selection_color = "#2196F3"

        self._build_ui()

    def _build_ui(self):
        """Construye la interfaz del editor UML."""
        # Barra de herramientas
        toolbar = ttk.Frame(self)
        toolbar.pack(side="top", fill="x", padx=2, pady=2)

        ttk.Button(toolbar, text="Clase", width=10,
                   command=self.add_class).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Editar", width=10,
                   command=self.edit_selected_class).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Eliminar", width=10,
                   command=self.delete_selected).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(
            side="left", fill="y", padx=5, pady=3)

        ttk.Button(toolbar, text="Guardar XML", width=12,
                   command=self.save_xml).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Abrir XML", width=12,
                   command=self.open_xml).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(
            side="left", fill="y", padx=5, pady=3)

        ttk.Button(toolbar, text="PDF", width=8,
                   command=self.export_pdf).pack(side="left", padx=2)
        ttk.Button(toolbar, text="PNG", width=8,
                   command=self.export_png).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(
            side="left", fill="y", padx=5, pady=3)

        ttk.Button(toolbar, text="+", width=4,
                   command=self.zoom_in).pack(side="left", padx=2)
        ttk.Button(toolbar, text="-", width=4,
                   command=self.zoom_out).pack(side="left", padx=2)
        ttk.Button(toolbar, text="↻", width=4,
                   command=self.reset_zoom).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(
            side="left", fill="y", padx=5, pady=3)

        ttk.Button(toolbar, text="Limpiar", width=10,
                   command=self.clear_all).pack(side="left", padx=2)

        # Panel lateral de relaciones + lienzo de dibujo
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        relation_panel = ttk.LabelFrame(body, text="Relaciones", padding=5)
        relation_panel.pack(side="left", fill="y", padx=(4, 2), pady=2)
        self._build_relation_panel(relation_panel)

        canvas_frame = ttk.Frame(body)
        canvas_frame.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg=self.bg_color,
            highlightthickness=0,
            scrollregion=(0, 0, 2000, 2000),
        )

        v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical",
                                 command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal",
                                 command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scroll.set,
                              xscrollcommand=h_scroll.set)

        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Bindings del canvas
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Double-1>", self._on_double_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Control-MouseWheel>", self._on_zoom_wheel)
        self.canvas.bind("<Motion>", self._on_motion)

        # Dibujar fondo
        self._draw_grid()

    def _build_relation_panel(self, panel):
        """Construye el panel lateral con los tipos de relación arrastrables."""
        types = [
            (UMLRelation.ASSOCIATION, "→", "Asociación"),
            (UMLRelation.INHERITANCE, "▷", "Herencia"),
            (UMLRelation.COMPOSITION, "◆", "Composición"),
            (UMLRelation.AGGREGATION, "◇", "Agregación"),
            (UMLRelation.DEPENDENCY, "⇢", "Dependencia"),
        ]

        ttk.Label(
            panel,
            text="Arrastre una flecha\nhasta la clase origen;\nluego haga clic en\nla clase destino.",
            foreground="#666666",
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        for rel_type, symbol, label in types:
            btn = tk.Button(
                panel,
                text=f"{symbol}  {label}",
                relief="raised",
                bd=1,
                width=16,
                anchor="w",
                cursor="hand2",
            )
            btn.pack(fill="x", pady=2)
            btn.bind("<ButtonPress-1>",
                     lambda e, t=rel_type: self._start_relation_drag(t, e))
            btn.bind("<B1-Motion>", self._on_relation_drag_motion)
            btn.bind("<ButtonRelease-1>", self._on_relation_drag_release)

    # --- Gestión de clases ---

    def add_class(self, uml_class=None):
        """Añade una nueva clase al diagrama."""
        if uml_class is None:
            dlg = ClassDialog(self, "Nueva clase UML")
            self.wait_window(dlg)
            if dlg.result is None:
                return
            uml_class = dlg.result

        class_id = self.next_class_id
        self.next_class_id += 1

        # Ubicar la clase en una cuadrícula para que las clases nuevas no
        # queden superpuestas y puedan seleccionarse al crear relaciones.
        col = class_id % 3
        row = (class_id // 3) % 3
        uml_class.x = 50 + col * 220
        uml_class.y = 50 + row * 200

        self.classes[class_id] = uml_class
        self.selected_class_id = class_id
        self.redraw()
        return class_id

    def edit_selected_class(self):
        """Edita la clase seleccionada."""
        if self.selected_class_id is None:
            messagebox.showinfo("Seleccionar", "Seleccione una clase para editar.",
                                parent=self)
            return

        uml_class = self.classes[self.selected_class_id]
        dlg = ClassDialog(self, f"Editar clase: {uml_class.name}", uml_class)
        self.wait_window(dlg)
        if dlg.result:
            self.classes[self.selected_class_id] = dlg.result
            self.redraw()

    def delete_selected(self):
        """Elimina la clase o relación seleccionada."""
        if self.selected_class_id is None:
            messagebox.showinfo("Seleccionar", "Seleccione un elemento para eliminar.",
                                parent=self)
            return

        # Verificar si hay una relación seleccionada
        if hasattr(self, "_selected_relation_idx") and self._selected_relation_idx is not None:
            idx = self._selected_relation_idx
            if messagebox.askyesno("Eliminar", "¿Eliminar la relación seleccionada?",
                                   parent=self):
                del self.relations[idx]
                self._selected_relation_idx = None
                self.redraw()
            return

        class_id = self.selected_class_id
        if messagebox.askyesno("Eliminar", f"¿Eliminar la clase '{self.classes[class_id].name}'?",
                               parent=self):
            # Eliminar relaciones asociadas
            self.relations = [r for r in self.relations
                              if r.source_id != class_id and r.target_id != class_id]
            del self.classes[class_id]
            self.selected_class_id = None
            self.redraw()

    def clear_all(self):
        """Limpia todo el diagrama."""
        if not self.classes and not self.relations:
            return
        if messagebox.askyesno("Limpiar", "¿Eliminar todas las clases y relaciones?",
                               parent=self):
            self.classes.clear()
            self.relations.clear()
            self.next_class_id = 0
            self.selected_class_id = None
            self.redraw()

    # --- Gestión de relaciones ---

    def _create_relation(self, source_id, target_id, rel_type=None):
        """Crea una relación entre dos clases."""
        if source_id == target_id:
            messagebox.showwarning("Advertencia",
                                   "No se puede crear una relación consigo misma.",
                                   parent=self)
            return

        # Verificar si ya existe
        for rel in self.relations:
            if (rel.source_id == source_id and rel.target_id == target_id) or \
               (rel.source_id == target_id and rel.target_id == source_id):
                messagebox.showinfo("Relación existente",
                                    "Ya existe una relación entre estas clases.",
                                    parent=self)
                return

        if rel_type is None:
            dlg = RelationDialog(self, "Nueva relación")
            self.wait_window(dlg)
            if dlg.result:
                dlg.result.source_id = source_id
                dlg.result.target_id = target_id
                self.relations.append(dlg.result)
        else:
            self.relations.append(UMLRelation(
                source_id=source_id,
                target_id=target_id,
                rel_type=rel_type,
            ))

        self.redraw()

    def _start_relation_drag(self, rel_type, event):
        """Inicia el arrastre de una flecha de relación desde el panel."""
        if len(self.classes) < 2:
            messagebox.showinfo(
                "Relación",
                "Necesita al menos 2 clases para crear una relación.",
                parent=self)
            return
        self._rel_drag_active = True
        self._rel_drag_type = rel_type
        self.relation_source_id = None
        self._rel_drag_anchor = self._event_to_canvas(event)
        try:
            event.widget.grab_set_global()
        except tk.TclError:
            pass
        self.canvas.configure(cursor="crosshair")
        self.update_status("Arrastre la flecha hasta la clase origen y suelte")

    def _on_relation_drag_motion(self, event):
        """Actualiza la línea temporal mientras se arrastra la flecha."""
        if not self._rel_drag_active:
            return
        cx, cy = self._event_to_canvas(event)
        ax, ay = self._rel_drag_anchor or (cx, cy)
        self.canvas.delete("rel_temp")
        self.canvas.create_line(ax, ay, cx, cy, fill=self.selection_color,
                                width=2, dash=(5, 3), tags="rel_temp")

    def _on_relation_drag_release(self, event):
        """Suelta la flecha: define la clase origen de la relación."""
        if not self._rel_drag_active:
            return
        try:
            event.widget.grab_release()
        except tk.TclError:
            pass
        cx, cy = self._event_to_canvas(event)
        self.canvas.delete("rel_temp")

        class_id = self._find_class_at(cx, cy)
        if class_id is None:
            self._finish_relation_mode()
            self.update_status("Arrastre cancelado: suelte sobre una clase origen")
            return

        self._rel_drag_active = False
        self.relation_source_id = class_id
        self.creating_relation = True
        self.selected_class_id = class_id
        self._selected_relation_idx = None
        self.redraw()
        self.update_status("Ahora haga clic en la clase destino")

    def _finish_relation_mode(self):
        """Limpia el estado del modo de creación de relaciones."""
        self.creating_relation = False
        self.relation_source_id = None
        self._rel_drag_type = None
        self._rel_drag_anchor = None
        self._rel_drag_active = False
        self.canvas.delete("rel_temp")
        self.canvas.configure(cursor="")

    def _event_to_canvas(self, event):
        """Convierte coordenadas de pantalla (root) a coordenadas del canvas."""
        wx = event.x_root - self.canvas.winfo_rootx()
        wy = event.y_root - self.canvas.winfo_rooty()
        return self.canvas.canvasx(wx), self.canvas.canvasy(wy)

    def _edit_relation(self, idx):
        """Edita una relación existente."""
        if idx < 0 or idx >= len(self.relations):
            return
        rel = self.relations[idx]
        dlg = RelationDialog(self, "Editar relación", rel)
        self.wait_window(dlg)
        if dlg.result:
            dlg.result.source_id = rel.source_id
            dlg.result.target_id = rel.target_id
            self.relations[idx] = dlg.result
            self.redraw()

    # --- Eventos del canvas ---

    def _on_click(self, event):
        """Maneja clics en el canvas."""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Modo creación de relación
        if self.creating_relation:
            class_id = self._find_class_at(x, y)
            if class_id is not None:
                if self.relation_source_id is None:
                    self.relation_source_id = class_id
                    self.update_status("Ahora haga clic en la clase destino")
                else:
                    self._create_relation(self.relation_source_id, class_id,
                                          self._rel_drag_type)
                    self._finish_relation_mode()
                    self.update_status("Relación creada")
            else:
                self._finish_relation_mode()
                self.update_status("Creación de relación cancelada")
            return

        # Redimensionar desde una esquina
        corner = self._get_resize_corner(x, y)
        if corner is not None:
            class_id, corner_name = corner
            self.selected_class_id = class_id
            self._selected_relation_idx = None
            uml_class = self.classes[class_id]
            self.resizing = True
            self.resize_corner = corner_name
            self.resize_start = (x, y, uml_class.x, uml_class.y,
                                 uml_class.width, uml_class.height)
            self.dragging = False
            self.redraw()
            return

        # Buscar clase en el punto
        class_id = self._find_class_at(x, y)
        if class_id is not None:
            self.selected_class_id = class_id
            self._selected_relation_idx = None
            self.drag_offset = (x - self.classes[class_id].x,
                                y - self.classes[class_id].y)
            self.dragging = True
            self.redraw()
        else:
            # Buscar relación cerca
            rel_idx = self._find_relation_near(x, y)
            if rel_idx is not None:
                self.selected_class_id = None
                self._selected_relation_idx = rel_idx
                self.redraw()
            else:
                self.selected_class_id = None
                self._selected_relation_idx = None
                self.redraw()

    def _on_drag(self, event):
        """Maneja arrastre de clases y redimensionado por las esquinas."""
        if self._rel_drag_active:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.resizing and self.selected_class_id is not None:
            self._resize_selected(x, y)
            self.redraw()
            return

        if not self.dragging or self.selected_class_id is None:
            return

        uml_class = self.classes[self.selected_class_id]
        uml_class.x = x - self.drag_offset[0]
        uml_class.y = y - self.drag_offset[1]

        # Mantener dentro del canvas
        uml_class.x = max(0, uml_class.x)
        uml_class.y = max(0, uml_class.y)

        self.redraw()

    def _on_release(self, event):
        """Maneja liberación del mouse."""
        self.dragging = False
        self.drag_offset = None
        self.resizing = False
        self.resize_corner = None
        self.resize_start = None

    def _on_motion(self, event):
        """Actualiza el cursor y la línea temporal según el puntero."""
        if self._rel_drag_active:
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.creating_relation and self.relation_source_id is not None:
            src = self.classes.get(self.relation_source_id)
            if src is not None:
                cx1, cy1 = self._get_class_center(src)
                self.canvas.delete("rel_temp")
                self.canvas.create_line(cx1, cy1, x, y, fill=self.selection_color,
                                        width=2, dash=(5, 3), tags="rel_temp")
                return

        corner = self._get_resize_corner(x, y)
        if corner is not None:
            if corner[1] in ("nw", "se"):
                self.canvas.configure(cursor="size_nw_se")
            else:
                self.canvas.configure(cursor="size_ne_sw")
        elif self._find_class_at(x, y) is not None:
            self.canvas.configure(cursor="fleur")
        else:
            self.canvas.configure(cursor="")

    def _get_resize_corner(self, x, y):
        """Devuelve (class_id, esquina) si el punto está sobre una esquina."""
        order = []
        if self.selected_class_id is not None:
            order.append(self.selected_class_id)
        for class_id in self.classes:
            if class_id not in order:
                order.append(class_id)

        for class_id in order:
            uml_class = self.classes.get(class_id)
            if uml_class is None:
                continue
            corners = [
                ("nw", uml_class.x, uml_class.y),
                ("ne", uml_class.x + uml_class.width, uml_class.y),
                ("sw", uml_class.x, uml_class.y + uml_class.height),
                ("se", uml_class.x + uml_class.width, uml_class.y + uml_class.height),
            ]
            for name, cx, cy in corners:
                if abs(x - cx) <= self.RESIZE_HANDLE and abs(y - cy) <= self.RESIZE_HANDLE:
                    return (class_id, name)
        return None

    def _resize_selected(self, x, y):
        """Redimensiona la clase seleccionada según la esquina arrastrada."""
        if self.selected_class_id is None or self.resize_start is None:
            return
        uml_class = self.classes.get(self.selected_class_id)
        if uml_class is None:
            return

        sx, sy, start_x, start_y, start_w, start_h = self.resize_start
        dx = x - sx
        dy = y - sy
        min_w, min_h = 120, 80
        corner = self.resize_corner

        if corner in ("se", "ne"):
            new_w = max(min_w, start_w + dx)
        else:
            new_w = max(min_w, start_w - dx)

        if corner in ("se", "sw"):
            new_h = max(min_h, start_h + dy)
        else:
            new_h = max(min_h, start_h - dy)

        new_x = start_x
        new_y = start_y
        if corner in ("nw", "sw"):
            new_x = start_x + (start_w - new_w)
        if corner in ("nw", "ne"):
            new_y = start_y + (start_h - new_h)

        uml_class.x = max(0, new_x)
        uml_class.y = max(0, new_y)
        uml_class.width = new_w
        uml_class.height = new_h

    def _on_double_click(self, event):
        """Maneja doble clic."""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        class_id = self._find_class_at(x, y)
        if class_id is not None:
            self.selected_class_id = class_id
            self.edit_selected_class()
            return

        # Doble clic en relación
        rel_idx = self._find_relation_near(x, y)
        if rel_idx is not None:
            self._edit_relation(rel_idx)

    def _on_right_click(self, event):
        """Muestra menú contextual."""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        class_id = self._find_class_at(x, y)
        rel_idx = self._find_relation_near(x, y)

        menu = tk.Menu(self, tearoff=0)

        if class_id is not None:
            self.selected_class_id = class_id
            self._selected_relation_idx = None
            uml_class = self.classes[class_id]
            menu.add_command(label=f"Editar '{uml_class.name}'",
                             command=self.edit_selected_class)
            menu.add_command(label="Añadir atributo",
                             command=lambda: self._add_attr_to_class(class_id))
            menu.add_command(label="Añadir método",
                             command=lambda: self._add_method_to_class(class_id))
            menu.add_separator()
            menu.add_command(label="Eliminar clase",
                             command=self.delete_selected)
        elif rel_idx is not None:
            self.selected_class_id = None
            self._selected_relation_idx = rel_idx
            menu.add_command(label="Editar relación",
                             command=lambda: self._edit_relation(rel_idx))
            menu.add_separator()
            menu.add_command(label="Eliminar relación",
                             command=self.delete_selected)
        else:
            menu.add_command(label="Añadir clase", command=self.add_class)
            menu.add_separator()
            menu.add_command(label="Limpiar todo", command=self.clear_all)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _on_zoom_wheel(self, event):
        """Maneja zoom con Ctrl + rueda del mouse."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def _add_attr_to_class(self, class_id):
        """Añade un atributo a una clase específica."""
        dlg = AttributeDialog(self, "Nuevo atributo")
        self.wait_window(dlg)
        if dlg.result:
            self.classes[class_id].add_attribute(dlg.result)
            self.redraw()

    def _add_method_to_class(self, class_id):
        """Añade un método a una clase específica."""
        dlg = MethodDialog(self, "Nuevo método",
                           class_name=self.classes[class_id].name)
        self.wait_window(dlg)
        if dlg.result:
            self.classes[class_id].add_method(dlg.result)
            self.redraw()

    def _find_class_at(self, x, y):
        """Encuentra la clase en un punto."""
        for class_id, uml_class in self.classes.items():
            if uml_class.contains_point(x, y):
                return class_id
        return None

    def _find_relation_near(self, x, y, threshold=10):
        """Encuentra una relación cerca de un punto."""
        for idx, rel in enumerate(self.relations):
            if rel.source_id not in self.classes or rel.target_id not in self.classes:
                continue
            src = self.classes[rel.source_id]
            tgt = self.classes[rel.target_id]
            x1, y1 = self._get_class_center(src)
            x2, y2 = self._get_class_center(tgt)
            dist = self._point_to_segment_distance(x, y, x1, y1, x2, y2)
            if dist < threshold:
                return idx
        return None

    def _point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        """Calcula la distancia de un punto a un segmento."""
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))

        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)

    def _get_class_center(self, uml_class):
        """Obtiene el centro de una clase."""
        return (uml_class.x + uml_class.width / 2,
                uml_class.y + uml_class.height / 2)

    # --- Dibujo ---

    def _draw_grid(self):
        """Dibuja la cuadrícula de fondo."""
        self.canvas.delete("grid")
        for x in range(0, 2000, 20):
            self.canvas.create_line(x, 0, x, 2000, fill=self.grid_color,
                                    tags="grid")
        for y in range(0, 2000, 20):
            self.canvas.create_line(0, y, 2000, y, fill=self.grid_color,
                                    tags="grid")

    def redraw(self):
        """Redibuja todo el diagrama."""
        self.canvas.delete("all")
        self._draw_grid()

        # Dibujar relaciones primero (detrás de las clases)
        for idx, rel in enumerate(self.relations):
            self._draw_relation(rel, idx)

        # Dibujar clases
        for class_id, uml_class in self.classes.items():
            self._draw_class(class_id, uml_class)

    def _draw_class(self, class_id, uml_class):
        """Dibuja una clase UML en el canvas."""
        x, y = uml_class.x, uml_class.y
        w, h = uml_class.width, uml_class.height

        # Determinar colores
        fill = uml_class.color
        outline = self.selection_color if class_id == self.selected_class_id else self.line_color
        outline_width = 3 if class_id == self.selected_class_id else 2

        # Fondo de la clase
        self.canvas.create_rectangle(
            x, y, x + w, y + h,
            fill=fill,
            outline=outline,
            width=outline_width,
            tags=f"class_{class_id}",
        )

        # Nombre de la clase
        name = uml_class.name
        if uml_class.is_interface:
            name = f"«interface»\n{name}"
        elif uml_class.is_abstract:
            name = f"«abstract»\n{name}"

        # Altura de la sección de nombre
        name_height = 40
        self.canvas.create_rectangle(
            x, y, x + w, y + name_height,
            fill=fill,
            outline=outline,
            width=outline_width,
            tags=f"class_{class_id}",
        )

        # Texto del nombre
        self.canvas.create_text(
            x + w / 2, y + name_height / 2,
            text=name,
            fill=uml_class.text_color,
            font=("Arial", 11, "bold"),
            justify="center",
            tags=f"class_{class_id}",
        )

        # Separador
        self.canvas.create_line(
            x, y + name_height, x + w, y + name_height,
            fill=outline,
            width=outline_width,
            tags=f"class_{class_id}",
        )

        # Atributos
        attr_y = y + name_height + 5
        for attr in uml_class.attributes:
            text = attr.to_string()
            font = ("Arial", 9, "italic" if attr.is_static else "normal")
            self.canvas.create_text(
                x + 5, attr_y,
                text=text,
                fill=uml_class.text_color,
                font=font,
                anchor="w",
                tags=f"class_{class_id}",
            )
            attr_y += 20

        # Separador de métodos
        if uml_class.methods:
            self.canvas.create_line(
                x, attr_y - 2, x + w, attr_y - 2,
                fill=outline,
                width=outline_width,
                tags=f"class_{class_id}",
            )

        # Métodos
        method_y = attr_y + 3
        for method in uml_class.methods:
            text = method.to_string()
            font = ("Arial", 9, "italic" if method.is_abstract else "normal")
            self.canvas.create_text(
                x + 5, method_y,
                text=text,
                fill=uml_class.text_color,
                font=font,
                anchor="w",
                tags=f"class_{class_id}",
            )
            method_y += 20

        # Asas de redimensionado en las esquinas (solo clase seleccionada)
        if class_id == self.selected_class_id:
            hs = self.RESIZE_HANDLE
            for cx, cy in ((x, y), (x + w, y), (x, y + h), (x + w, y + h)):
                self.canvas.create_rectangle(
                    cx - hs, cy - hs, cx + hs, cy + hs,
                    fill="white", outline=self.selection_color, width=1,
                    tags=f"class_{class_id}",
                )

    def _draw_relation(self, rel, idx):
        """Dibuja una relación UML."""
        if rel.source_id not in self.classes or rel.target_id not in self.classes:
            return

        src = self.classes[rel.source_id]
        tgt = self.classes[rel.target_id]

        # Puntos de conexión en los bordes
        x1, y1 = self._get_edge_point(src, tgt)
        x2, y2 = self._get_edge_point(tgt, src)

        # Color de selección
        is_selected = (hasattr(self, "_selected_relation_idx") and
                       self._selected_relation_idx == idx)
        color = self.selection_color if is_selected else self.line_color
        width = 3 if is_selected else 2

        # Dibujar línea según tipo
        if rel.rel_type == UMLRelation.INHERITANCE:
            # Triángulo vacío en el destino
            self._draw_line_with_arrow(x1, y1, x2, y2, color, width,
                                       arrow_type="triangle")
        elif rel.rel_type == UMLRelation.COMPOSITION:
            # Rombo relleno en el origen
            self._draw_line_with_diamond(x1, y1, x2, y2, color, width,
                                         filled=True)
        elif rel.rel_type == UMLRelation.AGGREGATION:
            # Rombo vacío en el origen
            self._draw_line_with_diamond(x1, y1, x2, y2, color, width,
                                         filled=False)
        elif rel.rel_type == UMLRelation.DEPENDENCY:
            # Línea discontinua con flecha
            self._draw_dashed_line_with_arrow(x1, y1, x2, y2, color, width)
        else:
            # Asociación: línea simple con flecha
            self._draw_line_with_arrow(x1, y1, x2, y2, color, width,
                                       arrow_type="arrow")

        # Etiqueta
        if rel.label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            self.canvas.create_text(
                mx, my - 10,
                text=rel.label,
                fill=color,
                font=("Arial", 9, "italic"),
                tags=f"relation_{idx}",
            )

        # Multiplicidades
        if rel.source_multiplicity:
            self.canvas.create_text(
                x1 + 10, y1 - 10,
                text=rel.source_multiplicity,
                fill=color,
                font=("Arial", 9),
                tags=f"relation_{idx}",
            )
        if rel.target_multiplicity:
            self.canvas.create_text(
                x2 - 10, y2 - 10,
                text=rel.target_multiplicity,
                fill=color,
                font=("Arial", 9),
                tags=f"relation_{idx}",
            )

    def _get_edge_point(self, src, tgt):
        """Obtiene el punto de borde de src hacia tgt."""
        cx1, cy1 = self._get_class_center(src)
        cx2, cy2 = self._get_class_center(tgt)

        dx = cx2 - cx1
        dy = cy2 - cy1

        if dx == 0 and dy == 0:
            return cx1, cy1

        # Calcular intersección con el rectángulo
        half_w = src.width / 2
        half_h = src.height / 2

        # Escalar para llegar al borde
        scale_x = half_w / abs(dx) if dx != 0 else float('inf')
        scale_y = half_h / abs(dy) if dy != 0 else float('inf')
        scale = min(scale_x, scale_y)

        return cx1 + dx * scale, cy1 + dy * scale

    def _draw_line_with_arrow(self, x1, y1, x2, y2, color, width, arrow_type="arrow"):
        """Dibuja una línea con flecha."""
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)

        # Calcular ángulo
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_len = 12

        if arrow_type == "triangle":
            # Triángulo vacío (herencia)
            ax1 = x2 - arrow_len * math.cos(angle - math.pi / 6)
            ay1 = y2 - arrow_len * math.sin(angle - math.pi / 6)
            ax2 = x2 - arrow_len * math.cos(angle + math.pi / 6)
            ay2 = y2 - arrow_len * math.sin(angle + math.pi / 6)
            self.canvas.create_polygon(
                x2, y2, ax1, ay1, ax2, ay2,
                fill="white",
                outline=color,
                width=width,
            )
        else:
            # Flecha simple
            ax1 = x2 - arrow_len * math.cos(angle - math.pi / 6)
            ay1 = y2 - arrow_len * math.sin(angle - math.pi / 6)
            ax2 = x2 - arrow_len * math.cos(angle + math.pi / 6)
            ay2 = y2 - arrow_len * math.sin(angle + math.pi / 6)
            self.canvas.create_line(x2, y2, ax1, ay1, fill=color, width=width)
            self.canvas.create_line(x2, y2, ax2, ay2, fill=color, width=width)

    def _draw_line_with_diamond(self, x1, y1, x2, y2, color, width, filled=False):
        """Dibuja una línea con rombo en el origen."""
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)

        # Rombo en el origen
        angle = math.atan2(y2 - y1, x2 - x1)
        diamond_size = 10

        # Puntos del rombo
        dx = diamond_size * math.cos(angle)
        dy = diamond_size * math.sin(angle)
        px = -dy / diamond_size * diamond_size
        py = dx / diamond_size * diamond_size

        points = [
            x1 + dx, y1 + dy,
            x1 + px, y1 + py,
            x1 - dx, y1 - dy,
            x1 - px, y1 - py,
        ]

        fill_color = color if filled else "white"
        self.canvas.create_polygon(
            points,
            fill=fill_color,
            outline=color,
            width=width,
        )

    def _draw_dashed_line_with_arrow(self, x1, y1, x2, y2, color, width):
        """Dibuja una línea discontinua con flecha."""
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width,
                                dash=(5, 3))

        # Flecha
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_len = 12
        ax1 = x2 - arrow_len * math.cos(angle - math.pi / 6)
        ay1 = y2 - arrow_len * math.sin(angle - math.pi / 6)
        ax2 = x2 - arrow_len * math.cos(angle + math.pi / 6)
        ay2 = y2 - arrow_len * math.sin(angle + math.pi / 6)
        self.canvas.create_line(x2, y2, ax1, ay1, fill=color, width=width)
        self.canvas.create_line(x2, y2, ax2, ay2, fill=color, width=width)

    # --- Zoom ---

    def zoom_in(self):
        """Aumenta el zoom."""
        self.zoom_factor = min(2.0, self.zoom_factor * 1.2)
        self.canvas.scale("all", 0, 0, 1.2, 1.2)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def zoom_out(self):
        """Disminuye el zoom."""
        self.zoom_factor = max(0.5, self.zoom_factor / 1.2)
        self.canvas.scale("all", 0, 0, 1 / 1.2, 1 / 1.2)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def reset_zoom(self):
        """Restablece el zoom."""
        self.zoom_factor = 1.0
        self.redraw()

    # --- Guardar / Cargar XML ---

    def save_xml(self, file_path=None):
        """Guarda el diagrama en formato XML."""
        if not file_path:
            file_path = filedialog.asksaveasfilename(
                parent=self,
                title="Guardar diagrama UML",
                defaultextension=".uml",
                filetypes=[
                    ("Diagramas UML", "*.uml"),
                    ("Archivos XML", "*.xml"),
                    ("Todos los archivos", "*.*"),
                ],
            )
            if not file_path:
                return False

        try:
            root = ET.Element("uml_diagram")
            root.set("version", "1.0")

            # Clases
            classes_elem = ET.SubElement(root, "classes")
            for class_id, uml_class in self.classes.items():
                class_elem = uml_class.to_xml()
                class_elem.set("id", str(class_id))
                classes_elem.append(class_elem)

            # Relaciones
            relations_elem = ET.SubElement(root, "relations")
            for rel in self.relations:
                relations_elem.append(rel.to_xml())

            # Serializar con formato
            xml_str = ET.tostring(root, encoding="unicode")
            pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(pretty_xml)

            self.update_status(f"Diagrama guardado: {file_path}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el diagrama:\n{e}",
                                 parent=self)
            return False

    def open_xml(self, file_path=None):
        """Carga un diagrama desde XML."""
        if not file_path:
            file_path = filedialog.askopenfilename(
                parent=self,
                title="Abrir diagrama UML",
                filetypes=[
                    ("Diagramas UML", "*.uml"),
                    ("Archivos XML", "*.xml"),
                    ("Todos los archivos", "*.*"),
                ],
            )
            if not file_path:
                return False

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            if root.tag != "uml_diagram":
                messagebox.showerror("Error", "El archivo no es un diagrama UML válido.",
                                     parent=self)
                return False

            # Limpiar datos actuales
            self.classes.clear()
            self.relations.clear()
            self.next_class_id = 0

            # Cargar clases
            classes_elem = root.find("classes")
            if classes_elem is not None:
                for class_elem in classes_elem.findall("class"):
                    class_id = int(class_elem.get("id", self.next_class_id))
                    uml_class = UMLClass.from_xml(class_elem)
                    self.classes[class_id] = uml_class
                    self.next_class_id = max(self.next_class_id, class_id + 1)

            # Cargar relaciones
            relations_elem = root.find("relations")
            if relations_elem is not None:
                for rel_elem in relations_elem.findall("relation"):
                    rel = UMLRelation.from_xml(rel_elem)
                    if rel.source_id in self.classes and rel.target_id in self.classes:
                        self.relations.append(rel)

            self.selected_class_id = None
            self.redraw()
            self.update_status(f"Diagrama cargado: {file_path}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el diagrama:\n{e}",
                                 parent=self)
            return False

    # --- Exportación ---

    def export_png(self, file_path=None):
        """Exporta el diagrama a PNG."""
        if not self.classes:
            messagebox.showinfo("Exportar", "No hay clases para exportar.",
                                parent=self)
            return False

        if not file_path:
            file_path = filedialog.asksaveasfilename(
                parent=self,
                title="Exportar a PNG",
                defaultextension=".png",
                filetypes=[("Imagen PNG", "*.png")],
            )
            if not file_path:
                return False

        if not PILLOW_AVAILABLE:
            return self._export_png_pure(file_path)

        try:
            # Calcular límites del diagrama
            min_x = min(c.x for c in self.classes.values())
            min_y = min(c.y for c in self.classes.values())
            max_x = max(c.x + c.width for c in self.classes.values())
            max_y = max(c.y + c.height for c in self.classes.values())

            # Margen
            margin = 50
            min_x = max(0, min_x - margin)
            min_y = max(0, min_y - margin)
            max_x += margin
            max_y += margin

            width = max_x - min_x
            height = max_y - min_y

            # Crear imagen
            img = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(img)

            # Fuentes
            try:
                font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
                font_normal = ImageFont.truetype("DejaVuSans.ttf", 12)
                font_small = ImageFont.truetype("DejaVuSans.ttf", 10)
            except:
                font_title = ImageFont.load_default()
                font_normal = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # Dibujar relaciones
            for rel in self.relations:
                if rel.source_id not in self.classes or rel.target_id not in self.classes:
                    continue
                src = self.classes[rel.source_id]
                tgt = self.classes[rel.target_id]

                x1, y1 = self._get_edge_point(src, tgt)
                x2, y2 = self._get_edge_point(tgt, src)

                # Ajustar coordenadas
                x1 -= min_x
                y1 -= min_y
                x2 -= min_x
                y2 -= min_y

                # Dibujar línea
                if rel.rel_type == UMLRelation.DEPENDENCY:
                    draw.line([(x1, y1), (x2, y2)], fill="black", width=2)
                else:
                    draw.line([(x1, y1), (x2, y2)], fill="black", width=2)

                # Etiqueta
                if rel.label:
                    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                    draw.text((mx, my - 15), rel.label, fill="black",
                              font=font_small)

            # Dibujar clases
            for uml_class in self.classes.values():
                x = uml_class.x - min_x
                y = uml_class.y - min_y
                w = uml_class.width
                h = uml_class.height

                # Fondo
                draw.rectangle([x, y, x + w, y + h], fill=uml_class.color,
                               outline="black", width=2)

                # Nombre
                name = uml_class.name
                if uml_class.is_interface:
                    name = f"«interface»\n{name}"
                elif uml_class.is_abstract:
                    name = f"«abstract»\n{name}"

                # Sección de nombre
                name_height = 40
                draw.rectangle([x, y, x + w, y + name_height],
                               fill=uml_class.color, outline="black", width=2)
                draw.text((x + 5, y + 5), name, fill="black", font=font_title)

                # Separador
                draw.line([(x, y + name_height), (x + w, y + name_height)],
                          fill="black", width=2)

                # Atributos
                attr_y = y + name_height + 5
                for attr in uml_class.attributes:
                    draw.text((x + 5, attr_y), attr.to_string(),
                              fill="black", font=font_normal)
                    attr_y += 20

                # Separador de métodos
                if uml_class.methods:
                    draw.line([(x, attr_y - 2), (x + w, attr_y - 2)],
                              fill="black", width=2)

                # Métodos
                method_y = attr_y + 3
                for method in uml_class.methods:
                    draw.text((x + 5, method_y), method.to_string(),
                              fill="black", font=font_normal)
                    method_y += 20

            img.save(file_path, "PNG")
            self.update_status(f"Diagrama exportado a PNG: {file_path}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar a PNG:\n{e}",
                                 parent=self)
            return False

    def export_pdf(self, file_path=None):
        """Exporta el diagrama a PDF."""
        if not self.classes:
            messagebox.showinfo("Exportar", "No hay clases para exportar.",
                                parent=self)
            return False

        if not file_path:
            file_path = filedialog.asksaveasfilename(
                parent=self,
                title="Exportar a PDF",
                defaultextension=".pdf",
                filetypes=[("Documento PDF", "*.pdf")],
            )
            if not file_path:
                return False

        if not REPORTLAB_AVAILABLE:
            return self._export_pdf_pure(file_path)

        try:
            # Calcular límites del diagrama
            min_x = min(c.x for c in self.classes.values())
            min_y = min(c.y for c in self.classes.values())
            max_x = max(c.x + c.width for c in self.classes.values())
            max_y = max(c.y + c.height for c in self.classes.values())

            # Margen
            margin = 50
            min_x = max(0, min_x - margin)
            min_y = max(0, min_y - margin)
            max_x += margin
            max_y += margin

            width = max_x - min_x
            height = max_y - min_y

            # Crear PDF
            c = rl_canvas.Canvas(file_path, pagesize=(width, height))
            c.setTitle("Diagrama UML")

            # Dibujar relaciones
            for rel in self.relations:
                if rel.source_id not in self.classes or rel.target_id not in self.classes:
                    continue
                src = self.classes[rel.source_id]
                tgt = self.classes[rel.target_id]

                x1, y1 = self._get_edge_point(src, tgt)
                x2, y2 = self._get_edge_point(tgt, src)

                # Ajustar coordenadas (invertir Y para PDF)
                y1_pdf = height - y1
                y2_pdf = height - y2

                # Dibujar línea
                c.setStrokeColor(rl_colors.black)
                c.setLineWidth(2)
                c.line(x1, y1_pdf, x2, y2_pdf)

                # Etiqueta
                if rel.label:
                    mx, my = (x1 + x2) / 2, (height - (y1 + y2) / 2)
                    c.setFont("Helvetica-Oblique", 10)
                    c.drawString(mx, my, rel.label)

            # Dibujar clases
            for uml_class in self.classes.values():
                x = uml_class.x
                y_pdf = height - (uml_class.y + uml_class.height)
                w = uml_class.width
                h = uml_class.height

                # Fondo
                c.setFillColor(rl_colors.HexColor(uml_class.color))
                c.setStrokeColor(rl_colors.black)
                c.setLineWidth(2)
                c.rect(x, y_pdf, w, h, fill=1, stroke=1)

                # Nombre
                name = uml_class.name
                if uml_class.is_interface:
                    name = f"«interface» {name}"
                elif uml_class.is_abstract:
                    name = f"«abstract» {name}"

                c.setFillColor(rl_colors.black)
                c.setFont("Helvetica-Bold", 12)
                c.drawString(x + 5, y_pdf + h - 20, name)

                # Separador
                c.setStrokeColor(rl_colors.black)
                c.setLineWidth(2)
                c.line(x, y_pdf + h - 40, x + w, y_pdf + h - 40)

                # Atributos
                attr_y = y_pdf + h - 60
                c.setFont("Helvetica", 10)
                for attr in uml_class.attributes:
                    c.drawString(x + 5, attr_y, attr.to_string())
                    attr_y -= 15

                # Separador de métodos
                if uml_class.methods:
                    c.line(x, attr_y + 2, x + w, attr_y + 2)

                # Métodos
                method_y = attr_y - 3
                for method in uml_class.methods:
                    c.drawString(x + 5, method_y, method.to_string())
                    method_y -= 15

            c.save()
            self.update_status(f"Diagrama exportado a PDF: {file_path}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar a PDF:\n{e}",
                                 parent=self)
            return False

    def _export_pdf_pure(self, file_path):
        """Exporta a PDF usando únicamente la biblioteca estándar."""
        try:
            classes = list(self.classes.values())
            min_x = min(c.x for c in classes)
            min_y = min(c.y for c in classes)
            max_x = max(c.x + c.width for c in classes)
            max_y = max(c.y + c.height for c in classes)
            margin = 50
            min_x = max(0, min_x - margin)
            min_y = max(0, min_y - margin)
            max_x += margin
            max_y += margin
            width = int(max_x - min_x)
            height = int(max_y - min_y)

            ops = []

            def px(x):
                return x - min_x

            def py(y):
                return height - (y - min_y)

            # Relaciones
            for rel in self.relations:
                if rel.source_id not in self.classes or rel.target_id not in self.classes:
                    continue
                src = self.classes[rel.source_id]
                tgt = self.classes[rel.target_id]
                x1, y1 = self._get_edge_point(src, tgt)
                x2, y2 = self._get_edge_point(tgt, src)
                ops.append(f"0 0 0 RG 2 w {px(x1):.2f} {py(y1):.2f} m "
                           f"{px(x2):.2f} {py(y2):.2f} l S\n")
                if rel.label:
                    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                    ops.append(f"BT /F3 10 Tf {px(mx):.2f} {py(my) - 12:.2f} Td "
                               f"({_pdf_escape(rel.label)}) Tj ET\n")

            # Clases
            for c in classes:
                x = px(c.x)
                y_bottom = py(c.y + c.height)
                w = c.width
                h = c.height
                r, g, b = _hex_to_rgb(c.color)
                ops.append(f"{r / 255:.3f} {g / 255:.3f} {b / 255:.3f} rg "
                           f"{x:.2f} {y_bottom:.2f} {w:.2f} {h:.2f} re f\n")
                ops.append(f"0 0 0 RG 2 w {x:.2f} {y_bottom:.2f} "
                           f"{w:.2f} {h:.2f} re S\n")

                name = c.name
                if c.is_interface:
                    name = "«interface» " + name
                elif c.is_abstract:
                    name = "«abstract» " + name
                ops.append(f"0 0 0 rg BT /F2 12 Tf {x + 5:.2f} "
                           f"{y_bottom + h - 18:.2f} Td "
                           f"({_pdf_escape(name)}) Tj ET\n")

                ops.append(f"0 0 0 RG 2 w {x:.2f} {y_bottom + h - 40:.2f} m "
                           f"{x + w:.2f} {y_bottom + h - 40:.2f} l S\n")

                attr_y = y_bottom + h - 60
                for attr in c.attributes:
                    ops.append(f"0 0 0 rg BT /F1 10 Tf {x + 5:.2f} {attr_y:.2f} Td "
                               f"({_pdf_escape(attr.to_string())}) Tj ET\n")
                    attr_y -= 15

                if c.methods:
                    ops.append(f"0 0 0 RG 2 w {x:.2f} {attr_y + 2:.2f} m "
                               f"{x + w:.2f} {attr_y + 2:.2f} l S\n")

                method_y = attr_y - 3
                for method in c.methods:
                    ops.append(f"0 0 0 rg BT /F1 10 Tf {x + 5:.2f} {method_y:.2f} Td "
                               f"({_pdf_escape(method.to_string())}) Tj ET\n")
                    method_y -= 15

            _write_pdf_file(file_path, width, height, "".join(ops).encode("latin-1"))
            self.update_status(f"Diagrama exportado a PDF: {file_path}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar a PDF:\n{e}",
                                 parent=self)
            return False


    def _export_png_pure(self, file_path):
        """Exporta a PNG usando únicamente la biblioteca estándar."""
        try:
            min_x = min(c.x for c in self.classes.values())
            min_y = min(c.y for c in self.classes.values())
            max_x = max(c.x + c.width for c in self.classes.values())
            max_y = max(c.y + c.height for c in self.classes.values())
            margin = 50
            min_x = max(0, min_x - margin)
            min_y = max(0, min_y - margin)
            max_x += margin
            max_y += margin
            width = int(max_x - min_x)
            height = int(max_y - min_y)

            img = _PngImage(width, height)

            # Relaciones (líneas)
            for rel in self.relations:
                if rel.source_id not in self.classes or rel.target_id not in self.classes:
                    continue
                src = self.classes[rel.source_id]
                tgt = self.classes[rel.target_id]
                x1, y1 = self._get_edge_point(src, tgt)
                x2, y2 = self._get_edge_point(tgt, src)
                img.line(x1 - min_x, y1 - min_y, x2 - min_x, y2 - min_y,
                         (0, 0, 0), 2)
                if rel.label:
                    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                    img.text(int(mx - min_x), int(my - min_y - 15),
                             _transliterate_ascii(rel.label), (0, 0, 0), 1)

            # Clases
            for uml_class in self.classes.values():
                x = uml_class.x - min_x
                y = uml_class.y - min_y
                w = int(uml_class.width)
                h = int(uml_class.height)
                fill = _hex_to_rgb(uml_class.color)
                img.fill_rect(x, y, x + w, y + h, fill)
                img.stroke_rect(x, y, x + w, y + h, (0, 0, 0), 2)

                name = uml_class.name
                if uml_class.is_interface:
                    name = "<<interface>> " + name
                elif uml_class.is_abstract:
                    name = "<<abstract>> " + name
                name_height = 40
                img.line(x, y + name_height, x + w, y + name_height, (0, 0, 0), 2)
                img.text(x + 5, y + 6, _transliterate_ascii(name), (0, 0, 0), 2)

                attr_y = y + name_height + 5
                for attr in uml_class.attributes:
                    img.text(x + 5, attr_y,
                             _transliterate_ascii(attr.to_string()), (0, 0, 0), 1)
                    attr_y += 20

                if uml_class.methods:
                    img.line(x, attr_y - 2, x + w, attr_y - 2, (0, 0, 0), 2)

                method_y = attr_y + 3
                for method in uml_class.methods:
                    img.text(x + 5, method_y,
                             _transliterate_ascii(method.to_string()), (0, 0, 0), 1)
                    method_y += 20

            with open(file_path, "wb") as f:
                f.write(img.to_png_bytes())
            self.update_status(f"Diagrama exportado a PNG: {file_path}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar a PNG:\n{e}",
                                 parent=self)
            return False


    # --- Utilidades ---

    def update_status(self, message):
        """Actualiza el mensaje de estado."""
        if self.ide and hasattr(self.ide, "update_status"):
            self.ide.update_status(message)

    def apply_theme(self, colors=None):
        """Aplica el tema al editor UML."""
        if colors is None and self.ide:
            colors = self.ide.theme_manager.get_colors()

        if colors:
            self.bg_color = colors.get("bg", "#FFFFFF")
            self.grid_color = colors.get("grid", "#E0E0E0")
            self.line_color = colors.get("fg", "#333333")
            self.canvas.configure(bg=self.bg_color)
            self.redraw()