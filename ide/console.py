"""
Consola de salida para MeriCode C++.

Este módulo proporciona el panel de consola inferior del IDE,
con pestañas para mostrar la salida del programa, los errores
de compilación y la información de depuración.
"""

import tkinter as tk
from tkinter import ttk

from .theme import ThemeManager


class ConsolePanel(ttk.Frame):
    """Panel de consola con pestañas para salida, errores y depuración.

    La consola tiene tres pestañas:
    - Salida: Muestra la salida estándar de los programas ejecutados.
    - Errores: Muestra los errores de compilación.
    - Depuración: Muestra la información de las sesiones de GDB.
    """

    # Colores estáticos por defecto (serán reemplazados por el tema)
    COLORS = {
        "background": "#1e1e1e",    # Fondo de la consola
        "foreground": "#d4d4d4",    # Texto normal
        "error": "#f14c4c",         # Mensajes de error
        "success": "#6a9955",       # Mensajes de éxito
        "info": "#4fc1ff",          # Mensajes informativos
        "warning": "#cca700",       # Mensajes de advertencia
    }

    def __init__(self, parent, theme_manager=None, **kwargs):
        """
        Inicializa el panel de consola.

        Args:
            parent: Widget padre del panel.
            theme_manager: Gestor de temas (opcional).
            **kwargs: Argumentos adicionales para ttk.Frame.
        """
        super().__init__(parent, **kwargs)
        self.theme_manager = theme_manager or ThemeManager()
        self._build_ui()

    def apply_theme(self):
        """Reaplica los colores del tema a todos los widgets de la consola."""
        colors = self.theme_manager.get_colors()
        self.COLORS["background"] = colors["bg"]
        self.COLORS["foreground"] = colors["fg"]
        self.COLORS["error"] = colors["error"]
        self.COLORS["success"] = colors["success"]
        self.COLORS["info"] = colors["info"]
        self.COLORS["warning"] = colors["warning"]

        # Actualizar todos los widgets de texto de la consola
        for text in (self.output_text, self.error_text, self.debug_text):
            text.configure(
                bg=self.COLORS["background"],
                fg=self.COLORS["foreground"],
                insertbackground=self.COLORS["foreground"],
            )
            # Reconfigurar las etiquetas de color
            text.tag_configure("error", foreground=self.COLORS["error"])
            text.tag_configure("success", foreground=self.COLORS["success"])
            text.tag_configure("info", foreground=self.COLORS["info"])
            text.tag_configure("warning", foreground=self.COLORS["warning"])
            text.tag_configure("normal", foreground=self.COLORS["foreground"])

    def _build_ui(self):
        """Construye la interfaz de la consola."""
        # Barra de herramientas superior de la consola
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=2, pady=2)

        # Botón para limpiar toda la consola
        ttk.Button(toolbar, text="🗑  Limpiar", command=self.clear_all,
                   width=12).pack(side="left", padx=2)

        # Checkbox para activar/desactivar el auto-scroll
        self._auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(toolbar, text="Auto scroll",
                        variable=self._auto_scroll_var).pack(side="left", padx=2)

        # Notebook de pestañas de la consola
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Pestaña de salida
        self.output_frame = self._create_tab("Salida", "#1e1e1e")
        self.output_text = self._create_text_widget(self.output_frame)

        # Pestaña de errores
        self.error_frame = self._create_tab("Errores", "#1e1e1e")
        self.error_text = self._create_text_widget(self.error_frame)

        # Pestaña de depuración
        self.debug_frame = self._create_tab("Depuración", "#1e1e1e")
        self.debug_text = self._create_text_widget(self.debug_frame)

    def _create_tab(self, title, bg):
        """
        Crea una pestaña en el notebook de la consola.

        Args:
            title: Título de la pestaña.
            bg: Color de fondo (se actualizará con el tema).

        Returns:
            ttk.Frame: El frame de la pestaña creada.
        """
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=title)
        return frame

    def _create_text_widget(self, parent):
        """
        Crea un widget de texto estilizado para la consola.

        Args:
            parent: Widget padre del texto.

        Returns:
            tk.Text: Widget de texto configurado para la consola.
        """
        text = tk.Text(
            parent,
            bg=self.COLORS["background"],
            fg=self.COLORS["foreground"],
            insertbackground=self.COLORS["foreground"],
            relief="flat",
            borderwidth=0,
            font=("Consolas", 10),
            wrap="word",
            padx=5,
            pady=5,
            state="disabled",  # La consola es solo lectura
        )
        text.pack(fill="both", expand=True)

        # Scrollbar vertical para el texto
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.configure(yscrollcommand=scrollbar.set)

        # Configurar las etiquetas de color del texto
        text.tag_configure("error", foreground=self.COLORS["error"])
        text.tag_configure("success", foreground=self.COLORS["success"])
        text.tag_configure("info", foreground=self.COLORS["info"])
        text.tag_configure("warning", foreground=self.COLORS["warning"])
        text.tag_configure("normal", foreground=self.COLORS["foreground"])

        return text

    def _write(self, text_widget, message, tag="normal"):
        """
        Escribe un mensaje en un widget de texto de la consola.

        Args:
            text_widget: Widget de texto donde escribir.
            message: Mensaje a escribir.
            tag: Etiqueta de color a utilizar.
        """
        text_widget.configure(state="normal")
        text_widget.insert("end", message, tag)
        # Auto-scroll al final si está activado
        if self._auto_scroll_var.get():
            text_widget.see("end")
        text_widget.configure(state="disabled")

    def output(self, message):
        """Escribe un mensaje normal en la pestaña de salida."""
        self._write(self.output_text, message, "normal")

    def error(self, message):
        """Escribe un mensaje de error (rojo) en la pestaña de errores."""
        self._write(self.error_text, message, "error")

    def debug(self, message):
        """Escribe un mensaje de depuración en la pestaña de depuración."""
        self._write(self.debug_text, message, "info")

    def success(self, message):
        """Escribe un mensaje de éxito (verde) en la pestaña de salida."""
        self._write(self.output_text, message, "success")

    def warning(self, message):
        """Escribe un mensaje de advertencia (amarillo) en la pestaña de salida."""
        self._write(self.output_text, message, "warning")

    def info(self, message):
        """Escribe un mensaje informativo (azul) en la pestaña de salida."""
        self._write(self.output_text, message, "info")

    def clear_all(self):
        """Limpia todas las pestañas de la consola."""
        for text in (self.output_text, self.error_text, self.debug_text):
            text.configure(state="normal")
            text.delete("1.0", "end")
            text.configure(state="disabled")

    def clear_output(self):
        """Limpia solo la pestaña de salida."""
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")

    def clear_errors(self):
        """Limpia solo la pestaña de errores."""
        self.error_text.configure(state="normal")
        self.error_text.delete("1.0", "end")
        self.error_text.configure(state="disabled")

    def clear_debug(self):
        """Limpia solo la pestaña de depuración."""
        self.debug_text.configure(state="normal")
        self.debug_text.delete("1.0", "end")
        self.debug_text.configure(state="disabled")

    def show_output_tab(self):
        """Muestra la pestaña de salida."""
        self.notebook.select(self.output_frame)

    def show_error_tab(self):
        """Muestra la pestaña de errores."""
        self.notebook.select(self.error_frame)

    def show_debug_tab(self):
        """Muestra la pestaña de depuración."""
        self.notebook.select(self.debug_frame)