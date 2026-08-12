"""
Diálogo de buscar y reemplazar para el editor de código.

Este módulo proporciona un diálogo flotante que permite buscar
texto en el editor, buscar hacia atrás, reemplazar una ocurrencia
o reemplazar todas las ocurrencias de un texto.
"""

import tkinter as tk
from tkinter import ttk


class SearchDialog(tk.Toplevel):
    """Diálogo flotante para buscar y reemplazar texto en el editor.

    El diálogo es modal y se puede cerrar con la tecla Escape.
    Soporta búsqueda distinguir entre mayúsculas y minúsculas,
    buscar siguiente/anterior, reemplazar uno a uno o todos.
    """

    def __init__(self, parent, text_widget):
        """
        Inicializa el diálogo de búsqueda.

        Args:
            parent: Ventana padre del diálogo.
            text_widget: Widget Text del editor donde buscar.
        """
        super().__init__(parent)
        self.text_widget = text_widget
        self._last_search_index = "1.0"  # Índice de la última búsqueda
        self._search_string = ""         # Último texto buscado

        self.title("Buscar")
        self.geometry("420x140")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._create_bindings()

        # Centrar el diálogo sobre la ventana padre
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + 50
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        """Construye la interfaz del diálogo."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Campo de búsqueda
        search_row = ttk.Frame(main_frame)
        search_row.pack(fill="x", pady=3)
        ttk.Label(search_row, text="Buscar:").pack(side="left")
        self.search_entry = ttk.Entry(search_row)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.focus_set()

        # Campo de reemplazo
        replace_row = ttk.Frame(main_frame)
        replace_row.pack(fill="x", pady=3)
        ttk.Label(replace_row, text="Reemplazar:").pack(side="left")
        self.replace_entry = ttk.Entry(replace_row)
        self.replace_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Opción de sensibilidad a mayúsculas/minúsculas
        options_row = ttk.Frame(main_frame)
        options_row.pack(fill="x", pady=3)
        self.case_sensitive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_row, text="Mayúsculas/minúsculas",
                        variable=self.case_sensitive_var).pack(side="left")

        # Botones de acción
        buttons_row = ttk.Frame(main_frame)
        buttons_row.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons_row, text="Buscar siguiente",
                   command=self.find_next).pack(side="left", padx=2)
        ttk.Button(buttons_row, text="Buscar anterior",
                   command=self.find_previous).pack(side="left", padx=2)
        ttk.Button(buttons_row, text="Reemplazar",
                   command=self.replace_one).pack(side="left", padx=2)
        ttk.Button(buttons_row, text="Reemplazar todo",
                   command=self.replace_all).pack(side="left", padx=2)
        ttk.Button(buttons_row, text="Cerrar",
                   command=self.destroy).pack(side="right", padx=2)

        # Etiqueta de estado para mostrar el resultado de las búsquedas
        self.status_label = ttk.Label(main_frame, text="", foreground="#666")
        self.status_label.pack(fill="x", pady=(5, 0))

    def _create_bindings(self):
        """Crea los atajos de teclado del diálogo."""
        # Enter busca la siguiente ocurrencia
        self.search_entry.bind("<Return>", lambda e: self.find_next())
        # Shift+Enter busca la anterior
        self.search_entry.bind("<Shift-Return>", lambda e: self.find_previous())
        # Enter en el campo de reemplazo reemplaza la actual
        self.replace_entry.bind("<Return>", lambda e: self.replace_one())
        # Escape cierra el diálogo
        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _get_search_string(self):
        """Obtiene el texto a buscar del campo de entrada.

        Returns:
            str: El texto a buscar.
        """
        return self.search_entry.get()

    def _search_pattern(self, start_index):
        """
        Busca el patrón desde un índice dado.

        Args:
            start_index: Índice Tkinter desde donde iniciar la búsqueda.

        Returns:
            str: Índice de la coincidencia, o None si no se encontró.
        """
        search = self._get_search_string()
        if not search:
            self.status_label.config(text="Ingrese un texto para buscar")
            return None

        self._search_string = search
        flags = () if self.case_sensitive_var.get() else ("nocase",)
        try:
            match = self.text_widget.search(
                search, start_index, stopindex="end", **dict.fromkeys(flags)
            )
            return match
        except tk.TclError:
            return None

    def find_next(self):
        """Busca la siguiente ocurrencia del texto."""
        search = self._get_search_string()
        if not search:
            return

        # Si el texto cambió, comenzar desde el inicio del documento
        if search != self._search_string:
            self._last_search_index = "1.0"

        start = self.text_widget.index("insert")
        match = self._search_pattern(start)

        # Si no hay más coincidencias, buscar desde el inicio
        if not match:
            match = self._search_pattern("1.0")
            if not match:
                self.status_label.config(
                    text=f"No se encontró '{search}'")
                self.bell()
                return

        # Seleccionar la coincidencia encontrada
        self._last_search_index = match
        end = f"{match}+{len(search)}c"
        self.text_widget.tag_remove("sel", "1.0", "end")
        self.text_widget.tag_add("sel", match, end)
        self.text_widget.mark_set("insert", end)
        self.text_widget.see(match)
        self.status_label.config(
            text=f"Encontrado en línea {match.split('.')[0]}")

    def find_previous(self):
        """Busca la ocurrencia anterior del texto."""
        search = self._get_search_string()
        if not search:
            return

        # Si el texto cambió, comenzar desde el final del documento
        if search != self._search_string:
            self._last_search_index = "end"

        start = self.text_widget.index("insert-1c")
        match = self.text_widget.search(
            search, "1.0", stopindex=start, backwards=True,
            nocase=not self.case_sensitive_var.get()
        )

        # Si no hay más coincidencias, buscar desde el final
        if not match:
            match = self.text_widget.search(
                search, "1.0", stopindex="end", backwards=True,
                nocase=not self.case_sensitive_var.get()
            )
            if not match:
                self.status_label.config(
                    text=f"No se encontró '{search}'")
                self.bell()
                return

        # Seleccionar la coincidencia encontrada
        end = f"{match}+{len(search)}c"
        self.text_widget.tag_remove("sel", "1.0", "end")
        self.text_widget.tag_add("sel", match, end)
        self.text_widget.mark_set("insert", match)
        self.text_widget.see(match)
        self.status_label.config(
            text=f"Encontrado en línea {match.split('.')[0]}")

    def replace_one(self):
        """Reemplaza la ocurrencia actualmente seleccionada."""
        search = self._get_search_string()
        replace = self.replace_entry.get()
        if not search:
            return

        # Obtener el texto seleccionado actualmente
        try:
            selected = self.text_widget.get("sel.first", "sel.last")
        except tk.TclError:
            selected = ""

        # Verificar que la selección coincida con el texto buscado
        if selected == search or (
            self.case_sensitive_var.get() is False
            and selected.lower() == search.lower()
        ):
            # Reemplazar la selección
            self.text_widget.delete("sel.first", "sel.last")
            self.text_widget.insert("sel.first", replace)
            self.text_widget.tag_remove("sel", "1.0", "end")
            self.status_label.config(text="Reemplazado")
        else:
            self.status_label.config(
                text="No hay texto seleccionado para reemplazar")

        # Avanzar a la siguiente ocurrencia
        self.find_next()

    def replace_all(self):
        """Reemplaza todas las ocurrencias del texto en el documento."""
        search = self._get_search_string()
        replace = self.replace_entry.get()
        if not search:
            return

        content = self.text_widget.get("1.0", "end-1c")

        if self.case_sensitive_var.get():
            # Reemplazo con distinción de mayúsculas/minúsculas
            count = content.count(search)
            new_content = content.replace(search, replace)
        else:
            # Reemplazo sin distinción de mayúsculas/minúsculas
            lower_content = content.lower()
            lower_search = search.lower()
            count = lower_content.count(lower_search)
            # Construir el nuevo contenido preservando el texto original
            parts = []
            pos = 0
            while True:
                idx = lower_content.find(lower_search, pos)
                if idx == -1:
                    parts.append(content[pos:])
                    break
                parts.append(content[pos:idx])
                parts.append(replace)
                pos = idx + len(search)
            new_content = "".join(parts)

        # Preservar el historial de deshacer
        self.text_widget.configure(undo=True)
        self.text_widget.edit_separator()
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", new_content)
        self.text_widget.tag_remove("sel", "1.0", "end")
        self.status_label.config(text=f"Se reemplazaron {count} ocurrencias")