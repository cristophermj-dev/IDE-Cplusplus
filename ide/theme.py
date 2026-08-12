"""
Sistema de temas (claro/oscuro) para MeriCode C++.

Este módulo gestiona los colores de toda la interfaz del IDE,
permitiendo alternar entre un tema claro y uno oscuro.
"""


class ThemeManager:
    """Gestiona los temas disponibles del IDE."""

    # ==============================
    # TEMA OSCURO (estilo VS Code Dark)
    # ==============================
    DARK = {
        # --- Colores base de la ventana ---
        "name": "Oscuro",            # Nombre visible del tema
        "bg": "#1e1e1e",             # Fondo principal de la ventana
        "bg_light": "#252526",       # Fondo ligeramente más claro
        "bg_lighter": "#2a2d2e",     # Fondo más claro aún
        "fg": "#d4d4d4",             # Color de texto principal

        # --- Colores de acento y estado ---
        "accent": "#0e639c",         # Color de acento para selecciones
        "accent_hover": "#1177bb",   # Acento al pasar el mouse
        "border": "#3c3c3c",         # Color de bordes

        # --- Barras de herramientas y estado ---
        "toolbar_bg": "#333333",     # Fondo de la barra de herramientas
        "statusbar_bg": "#007acc",   # Fondo de la barra de estado
        "statusbar_fg": "#ffffff",   # Texto de la barra de estado

        # --- Editor ---
        "selection": "#264f78",      # Color de selección de texto
        "line_number": "#858585",    # Color de los números de línea
        "line_number_bg": "#252526", # Fondo de los números de línea
        "current_line": "#2a2d2e",   # Color de la línea actual del cursor

        # --- Resaltado de sintaxis ---
        "keyword": "#569cd6",        # Palabras reservadas: if, for, while, return, int, float, char, bool, void, true, false, nullptr...
        "type": "#4ec9b0",           # Tipos de la STL (string, vector, map, list...)
        "namespace": "#c586c0",      # Espacios de nombres del sistema (std, cout, cin...)
        "string": "#ce9178",         # Cadenas de texto
        "comment": "#6a9955",        # Comentarios
        "number": "#b5cea8",         # Números
        "preprocessor": "#c586c0",   # Directivas de preprocesador
        "function": "#dcdcaa",       # Llamadas a funciones
        "operator": "#d4d4d4",       # Operadores
        "bracket": "#ffd700",        # Corchetes/paréntesis
        "library": "#ce9178",        # Nombres de librerías en #include <...>
        "user_class": "#4ec9b0",     # Clases definidas por el usuario

        # --- Mensajes de la consola ---
        "error": "#f14c4c",          # Mensajes de error
        "success": "#6a9955",        # Mensajes de éxito
        "info": "#4fc1ff",           # Mensajes informativos
        "warning": "#cca700",        # Advertencias

        # --- Pestañas del notebook ---
        "tab_selected": "#0e639c",   # Fondo de pestaña seleccionada
        "tab_selected_fg": "#ffffff",# Texto de pestaña seleccionada

        # --- Explorador de archivos ---
        "tree_bg": "#252526",        # Fondo del árbol
        "tree_fg": "#d4d4d4",        # Texto del árbol
        "tree_field_bg": "#252526",  # Fondo del campo del árbol

        # --- Entradas y formularios ---
        "entry_bg": "#252526",       # Fondo de campos de texto
        "entry_fg": "#d4d4d4",       # Texto de campos

        # --- Menús ---
        "menu_bg": "#252526",        # Fondo de menús
        "menu_fg": "#d4d4d4",        # Texto de menús
        "menu_active_bg": "#0e639c", # Fondo de menú activo
        "menu_active_fg": "#ffffff", # Texto de menú activo

        # --- Scrollbars ---
        "scrollbar_bg": "#252526",   # Fondo de la barra de scroll
        "scrollbar_trough": "#1e1e1e", # Canal de la scrollbar
        "scrollbar_arrow": "#d4d4d4",  # Flechas de la scrollbar

        # --- Checkbuttons y combos ---
        "checkbutton_bg": "#1e1e1e", # Fondo de checkbuttons
        "checkbutton_fg": "#d4d4d4", # Texto de checkbuttons
        "combobox_bg": "#252526",    # Fondo de combos
        "combobox_fg": "#d4d4d4",    # Texto de combos

        # --- Notebook y botones ---
        "notebook_bg": "#1e1e1e",    # Fondo del notebook
        "notebook_tab_bg": "#252526",# Fondo de pestañas
        "notebook_tab_fg": "#d4d4d4",# Texto de pestañas
        "button_bg": "#252526",      # Fondo de botones
        "button_fg": "#d4d4d4",      # Texto de botones
        "button_active_bg": "#0e639c", # Botón al pasar el mouse
        "button_pressed_bg": "#1177bb",# Botón presionado

        # --- Labels y frames ---
        "label_bg": "#1e1e1e",       # Fondo de etiquetas
        "label_fg": "#d4d4d4",       # Texto de etiquetas
        "frame_bg": "#1e1e1e",       # Fondo de frames
        "panel_bg": "#252526",       # Fondo de paneles

        # --- Explorador y archivos abiertos ---
        "explorer_header_bg": "#252526", # Cabecera del explorador
        "explorer_header_fg": "#d4d4d4", # Texto del explorador
        "open_files_bg": "#252526",      # Fondo de archivos abiertos
        "open_files_fg": "#d4d4d4",      # Texto de archivos abiertos
        "open_files_item_bg": "#2a2d2e", # Elemento de la lista
        "open_files_item_fg": "#d4d4d4", # Texto del elemento
        "open_files_close_bg": "#f14c4c",# Botón cerrar
        "open_files_close_fg": "#ffffff",# Texto del botón cerrar
    }

    # ==============================
    # TEMA CLARO (estilo VS Code Light)
    # ==============================
    LIGHT = {
        # --- Colores base de la ventana ---
        "name": "Claro",             # Nombre visible del tema
        "bg": "#ffffff",             # Fondo principal blanco
        "bg_light": "#f3f3f3",       # Fondo gris claro
        "bg_lighter": "#e8e8e8",     # Fondo gris más oscuro
        "fg": "#1e1e1e",             # Texto principal oscuro

        # --- Colores de acento y estado ---
        "accent": "#0078d4",         # Azul de acento
        "accent_hover": "#1a8ad4",   # Acento al pasar el mouse
        "border": "#d4d4d4",         # Bordes grises

        # --- Barras de herramientas y estado ---
        "toolbar_bg": "#e8e8e8",     # Fondo de la barra de herramientas
        "statusbar_bg": "#0078d4",   # Fondo de la barra de estado
        "statusbar_fg": "#ffffff",   # Texto de la barra de estado

        # --- Editor ---
        "selection": "#add6ff",      # Selección de texto azul claro
        "line_number": "#237893",    # Números de línea azulados
        "line_number_bg": "#f3f3f3", # Fondo de números de línea
        "current_line": "#e8f0fe",   # Línea actual del cursor

        # --- Resaltado de sintaxis ---
        "keyword": "#0000ff",        # Palabras reservadas azules: if, for, while, return, int, float, char, bool, void, true, false, nullptr...
        "type": "#267f99",           # Tipos de la STL azul verdoso (string, vector, map...)
        "namespace": "#af00db",      # Espacios de nombres del sistema (std, cout, cin...)
        "string": "#a31515",         # Cadenas rojas oscuras
        "comment": "#008000",        # Comentarios verdes
        "number": "#098658",         # Números verdes oscuros
        "preprocessor": "#af00db",   # Preprocesador magenta
        "function": "#795e26",       # Funciones marrones
        "operator": "#1e1e1e",       # Operadores oscuros
        "bracket": "#811f3f",        # Corchetes rojo oscuro
        "library": "#a31515",        # Nombres de librerías en #include <...>
        "user_class": "#267f99",     # Clases definidas por el usuario

        # --- Mensajes de la consola ---
        "error": "#f14c4c",          # Errores rojos
        "success": "#008000",        # Éxito verde
        "info": "#0078d4",           # Información azul
        "warning": "#cca700",        # Advertencias amarillas

        # --- Pestañas del notebook ---
        "tab_selected": "#0078d4",   # Pestaña seleccionada azul
        "tab_selected_fg": "#ffffff",# Texto de pestaña seleccionada

        # --- Explorador de archivos ---
        "tree_bg": "#f3f3f3",        # Fondo del árbol
        "tree_fg": "#1e1e1e",        # Texto del árbol
        "tree_field_bg": "#f3f3f3",  # Fondo del campo

        # --- Entradas y formularios ---
        "entry_bg": "#ffffff",       # Fondo blanco
        "entry_fg": "#1e1e1e",       # Texto oscuro

        # --- Menús ---
        "menu_bg": "#f3f3f3",        # Fondo de menús
        "menu_fg": "#1e1e1e",        # Texto de menús
        "menu_active_bg": "#0078d4", # Menú activo azul
        "menu_active_fg": "#ffffff", # Texto de menú activo

        # --- Scrollbars ---
        "scrollbar_bg": "#e8e8e8",   # Fondo de la scrollbar
        "scrollbar_trough": "#ffffff",# Canal blanco
        "scrollbar_arrow": "#1e1e1e",# Flechas oscuras

        # --- Checkbuttons y combos ---
        "checkbutton_bg": "#ffffff", # Fondo blanco
        "checkbutton_fg": "#1e1e1e", # Texto oscuro
        "combobox_bg": "#ffffff",    # Fondo blanco
        "combobox_fg": "#1e1e1e",    # Texto oscuro

        # --- Notebook y botones ---
        "notebook_bg": "#ffffff",    # Fondo del notebook
        "notebook_tab_bg": "#f3f3f3",# Fondo de pestañas
        "notebook_tab_fg": "#1e1e1e",# Texto de pestañas
        "button_bg": "#f3f3f3",      # Fondo de botones
        "button_fg": "#1e1e1e",      # Texto de botones
        "button_active_bg": "#0078d4", # Botón al pasar el mouse
        "button_pressed_bg": "#1a8ad4",# Botón presionado

        # --- Labels y frames ---
        "label_bg": "#ffffff",       # Fondo de etiquetas
        "label_fg": "#1e1e1e",       # Texto de etiquetas
        "frame_bg": "#ffffff",       # Fondo de frames
        "panel_bg": "#f3f3f3",       # Fondo de paneles

        # --- Explorador y archivos abiertos ---
        "explorer_header_bg": "#f3f3f3", # Cabecera del explorador
        "explorer_header_fg": "#1e1e1e", # Texto del explorador
        "open_files_bg": "#f3f3f3",      # Fondo de archivos abiertos
        "open_files_fg": "#1e1e1e",      # Texto de archivos abiertos
        "open_files_item_bg": "#e8e8e8", # Elemento de la lista
        "open_files_item_fg": "#1e1e1e", # Texto del elemento
        "open_files_close_bg": "#f14c4c",# Botón cerrar
        "open_files_close_fg": "#ffffff",# Texto del botón cerrar
    }

    # Diccionario con todos los temas disponibles
    THEMES = {
        "dark": DARK,
        "light": LIGHT,
    }

    def __init__(self):
        # Tema por defecto: claro (el usuario lo prefiere como inicio)
        self.current = "light"

    def get_colors(self):
        """Obtiene los colores del tema actual."""
        return self.THEMES[self.current]

    def set_theme(self, name):
        """
        Cambia el tema actual.

        Args:
            name: Nombre del tema ('light' o 'dark')

        Returns:
            bool: True si el tema se cambió correctamente, False si no existe.
        """
        # Verificar que el tema solicitado exista
        if name in self.THEMES:
            self.current = name
            return True
        return False

    def toggle(self):
        """
        Alterna entre claro y oscuro.

        Returns:
            str: Nombre del tema activo después del cambio.
        """
        # Si el tema actual es oscuro, cambiar a claro y viceversa
        self.current = "light" if self.current == "dark" else "dark"
        return self.current

    def is_dark(self):
        """
        Verifica si el tema actual es oscuro.

        Returns:
            bool: True si el tema activo es oscuro.
        """
        return self.current == "dark"