"""
Editor de código con números de línea para MeriCode C++.

Este módulo contiene la clase LineNumbers que dibuja los números
de línea en un canvas Tkinter, sincronizados con el widget Text
del editor de código.
"""

import tkinter as tk
from tkinter import font as tkfont

from .theme import ThemeManager


class LineNumbers(tk.Canvas):
    """Canvas que muestra los números de línea sincronizado con el editor.

    Esta clase se encarga de dibujar los números de línea al lado
    del editor de texto y mantenerlos actualizados cuando el usuario
    edita, desplaza o cambia el contenido del editor.
    """

    def __init__(self, parent, text_widget, theme_manager=None, **kwargs):
        """
        Inicializa el canvas de números de línea.

        Args:
            parent: Widget padre donde se coloca el canvas.
            text_widget: Widget Text al que acompañan los números de línea.
            theme_manager: Gestor de temas (opcional, usa el predeterminado).
            **kwargs: Argumentos adicionales para tk.Canvas.
        """
        super().__init__(parent, width=50, **kwargs)
        self.text_widget = text_widget
        self.theme_manager = theme_manager or ThemeManager()
        colors = self.theme_manager.get_colors()
        self.configure(
            bg=colors["line_number_bg"],
            highlightthickness=0,
        )
        # Fuente con la que se dibujan los números
        self._font = tkfont.Font(family="Consolas", size=11)
        self._update()

    def apply_theme(self):
        """Reaplica los colores del tema al canvas de números de línea."""
        colors = self.theme_manager.get_colors()
        self.configure(bg=colors["line_number_bg"])
        self._update()

    def _update(self, event=None):
        """Actualiza los números de línea visibles en el canvas."""
        try:
            # Limpiar el canvas antes de redibujar
            self.delete("all")

            # Determinar la primera y última línea visible
            first_line = int(self.text_widget.index("@0,0").split(".")[0])
            last_line = int(self.text_widget.index(
                f"@0,{self.text_widget.winfo_height()}").split(".")[0])

            # Ajustar el ancho del canvas según el número de dígitos
            width = max(3, len(str(last_line)))
            self.configure(width=width * 8 + 10)

            # Obtener la línea actual del cursor para resaltarla
            current_line = int(self.text_widget.index("insert").split(".")[0])
            colors = self.theme_manager.get_colors()

            # Dibujar cada número de línea visible
            for line in range(first_line, last_line + 1):
                y = self._get_line_y(line)
                if y is None:
                    continue

                # La línea actual se dibuja en un color más claro
                color = colors["fg"] if line == current_line else colors["line_number"]
                self.create_text(5, y, anchor="nw", text=str(line),
                                 fill=color, font=self._font)
        except tk.TclError:
            # Ignorar errores si el widget ya no existe
            pass

    def _get_line_y(self, line):
        """
        Obtiene la coordenada Y de una línea del editor.

        Args:
            line: Número de línea a localizar.

        Returns:
            int: Coordenada Y en píxeles, o None si no se puede calcular.
        """
        try:
            bbox = self.text_widget.bbox(f"{line}.0")
            if bbox:
                return bbox[1]
        except tk.TclError:
            pass
        return None

    def attach(self):
        """Vincula eventos clave para mantener los números sincronizados.

        Cada vez que el texto cambia, se desplaza o se modifica de
        cualquier forma, los números de línea se vuelven a dibujar.
        """
        self.text_widget.bind("<KeyRelease>", self._update, add="+")
        self.text_widget.bind("<MouseWheel>", self._update, add="+")
        self.text_widget.bind("<Button-4>", self._update, add="+")
        self.text_widget.bind("<Button-5>", self._update, add="+")
        self.text_widget.bind("<Configure>", self._update, add="+")
        self.text_widget.bind("<<Change>>", self._update, add="+")
        self.text_widget.bind("<<Modified>>", self._update, add="+")
        self.text_widget.bind("<ButtonRelease-1>", self._update, add="+")
        self.text_widget.bind("<Button-1>", self._update, add="+")
        self.text_widget.bind("<B1-Motion>", self._update, add="+")
        self.text_widget.bind("<Return>", self._update, add="+")
        self.text_widget.bind("<BackSpace>", self._update, add="+")
        self.text_widget.bind("<Delete>", self._update, add="+")
        self.text_widget.bind("<Tab>", self._update, add="+")
        self.text_widget.bind("<Up>", self._update, add="+")
        self.text_widget.bind("<Down>", self._update, add="+")
        self.text_widget.bind("<Prior>", self._update, add="+")
        self.text_widget.bind("<Next>", self._update, add="+")
        self.text_widget.bind("<Control-v>", self._update, add="+")
        self.text_widget.bind("<Control-V>", self._update, add="+")
        self.text_widget.bind("<Control-x>", self._update, add="+")
        self.text_widget.bind("<Control-X>", self._update, add="+")
        self.text_widget.bind("<Control-z>", self._update, add="+")
        self.text_widget.bind("<Control-Z>", self._update, add="+")
        self.text_widget.bind("<Control-y>", self._update, add="+")
        self.text_widget.bind("<Control-Y>", self._update, add="+")
        # Actualización periódica para cubrir otros casos de edición
        self.text_widget.after(200, self._periodic_update)

    def _periodic_update(self):
        """Actualiza periódicamente mientras el widget exista."""
        try:
            if self.winfo_exists():
                self._update()
                self.after(200, self._periodic_update)
        except tk.TclError:
            # El widget fue destruido, detener la actualización
            pass