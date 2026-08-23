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
        return f"{prefix} {self.name}({self.params}): {self.return_type}{static}{abstract}"

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
        self.transient(parent)
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

    def __init__(self, parent, title="Método", method=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None

        # Variables
        self.name_var = tk.StringVar(value=method.name if method else "")
        self.return_var = tk.StringVar(value=method.return_type if method else "void")
        self.params_var = tk.StringVar(value=method.params if method else "")
        self.visibility_var = tk.StringVar(value=method.visibility if method else "+")
        self.static_var = tk.BooleanVar(value=method.is_static if method else False)
        self.abstract_var = tk.BooleanVar(value=method.is_abstract if method else False)

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

        # Tipo de retorno
        ttk.Label(frame, text="Retorno:").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.return_var, width=25).grid(
            row=1, column=1, sticky="ew", pady=3, padx=(5, 0))

        # Parámetros
        ttk.Label(frame, text="Parámetros:").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(frame, textvariable=self.params_var, width=25).grid(
            row=2, column=1, sticky="ew", pady=3, padx=(5, 0))
        ttk.Label(frame, text="(ej: int a, string b)").grid(
            row=3, column=1, sticky="w", padx=(5, 0))

        # Visibilidad
        ttk.Label(frame, text="Visibilidad:").grid(row=4, column=0, sticky="w", pady=3)
        vis_frame = ttk.Frame(frame)
        vis_frame.grid(row=4, column=1, sticky="w", pady=3, padx=(5, 0))
        for vis, label in [("+", "+ público"), ("-", "- privado"),
                           ("#", "# protegido"), ("~", "~ paquete")]:
            ttk.Radiobutton(vis_frame, text=label, value=vis,
                            variable=self.visibility_var).pack(side="left", padx=3)

        # Opciones
        opts_frame = ttk.Frame(frame)
        opts_frame.grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Checkbutton(opts_frame, text="Estático",
                        variable=self.static_var).pack(side="left", padx=5)
        ttk.Checkbutton(opts_frame, text="Abstracto",
                        variable=self.abstract_var).pack(side="left", padx=5)

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0))
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
        self.result = UMLMethod(
            name=name,
            return_type=self.return_var.get().strip() or "void",
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
        self.geometry("500x450")
        self.transient(parent)
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
        ttk.Button(attrs_btns, text="➕ Añadir", width=10,
                   command=self._add_attribute).pack(side="left", padx=2)
        ttk.Button(attrs_btns, text="✏️ Editar", width=10,
                   command=self._edit_attribute).pack(side="left", padx=2)
        ttk.Button(attrs_btns, text="🗑 Eliminar", width=10,
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
        ttk.Button(methods_btns, text="➕ Añadir", width=10,
                   command=self._add_method).pack(side="left", padx=2)
        ttk.Button(methods_btns, text="✏️ Editar", width=10,
                   command=self._edit_method).pack(side="left", padx=2)
        ttk.Button(methods_btns, text="🗑 Eliminar", width=10,
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
        dlg = MethodDialog(self, "Nuevo método")
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
                           self.uml_class.methods[idx])
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
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.class_names = class_names or []

        # Variables
        self.type_var = tk.StringVar(
            value=relation.rel_type if relation else UMLRelation.ASSOCIATION)
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
        type_combo["values"] = list(UMLRelation.TYPE_LABELS.keys())
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
        self.result = UMLRelation(
            source_id=0,  # Se actualizará después
            target_id=0,
            rel_type=self.type_var.get(),
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
        self.creating_relation = False
        self.relation_source_id = None
        self.relation_temp_line = None
        self.relation_temp_coords = None

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

        ttk.Button(toolbar, text="➕ Clase", width=10,
                   command=self.add_class).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🔗 Relación", width=10,
                   command=self.start_relation_mode).pack(side="left", padx=2)
        ttk.Button(toolbar, text="✏️ Editar", width=10,
                   command=self.edit_selected_class).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🗑 Eliminar", width=10,
                   command=self.delete_selected).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(
            side="left", fill="y", padx=5, pady=3)

        ttk.Button(toolbar, text="💾 Guardar XML", width=12,
                   command=self.save_xml).pack(side="left", padx=2)
        ttk.Button(toolbar, text="📂 Abrir XML", width=12,
                   command=self.open_xml).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(
            side="left", fill="y", padx=5, pady=3)

        ttk.Button(toolbar, text="📄 PDF", width=8,
                   command=self.export_pdf).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🖼 PNG", width=8,
                   command=self.export_png).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(
            side="left", fill="y", padx=5, pady=3)

        ttk.Button(toolbar, text="🔍 +", width=4,
                   command=self.zoom_in).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🔍 -", width=4,
                   command=self.zoom_out).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🔄", width=4,
                   command=self.reset_zoom).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(
            side="left", fill="y", padx=5, pady=3)

        ttk.Button(toolbar, text="🗑 Limpiar", width=10,
                   command=self.clear_all).pack(side="left", padx=2)

        # Canvas con scrollbars
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill="both", expand=True)

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

        # Dibujar fondo
        self._draw_grid()

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

    def start_relation_mode(self):
        """Inicia el modo de creación de relaciones."""
        if len(self.classes) < 2:
            messagebox.showinfo("Relación", "Necesita al menos 2 clases para crear una relación.",
                                parent=self)
            return
        self.creating_relation = True
        self.relation_source_id = None
        self.canvas.configure(cursor="crosshair")
        self.update_status("Haga clic en la clase origen y luego en la clase destino")

    def _create_relation(self, source_id, target_id):
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

        dlg = RelationDialog(self, "Nueva relación")
        self.wait_window(dlg)
        if dlg.result:
            dlg.result.source_id = source_id
            dlg.result.target_id = target_id
            self.relations.append(dlg.result)
            self.redraw()

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
                    self._create_relation(self.relation_source_id, class_id)
                    self.creating_relation = False
                    self.relation_source_id = None
                    self.canvas.configure(cursor="")
                    self.update_status("Relación creada")
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
        """Maneja arrastre de clases."""
        if not self.dragging or self.selected_class_id is None:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

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
        dlg = MethodDialog(self, "Nuevo método")
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

        if not PILLOW_AVAILABLE:
            messagebox.showerror("Error",
                                 "Pillow no está instalado. Instale con: pip install Pillow",
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

        if not REPORTLAB_AVAILABLE:
            messagebox.showerror(
                "Error",
                "reportlab no está instalado. Instale con: pip install reportlab",
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