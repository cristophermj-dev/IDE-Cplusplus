"""
Sistema de temas (claro/oscuro) para el IDE C++.
"""


class ThemeManager:
    """Gestiona los temas disponibles del IDE."""

    DARK = {
        "name": "Oscuro",
        "bg": "#1e1e1e",
        "bg_light": "#252526",
        "bg_lighter": "#2a2d2e",
        "fg": "#d4d4d4",
        "accent": "#0e639c",
        "accent_hover": "#1177bb",
        "border": "#3c3c3c",
        "toolbar_bg": "#333333",
        "statusbar_bg": "#007acc",
        "statusbar_fg": "#ffffff",
        "selection": "#264f78",
        "line_number": "#858585",
        "line_number_bg": "#252526",
        "current_line": "#2a2d2e",
        "keyword": "#569cd6",
        "type": "#4ec9b0",
        "string": "#ce9178",
        "comment": "#6a9955",
        "number": "#b5cea8",
        "preprocessor": "#c586c0",
        "function": "#dcdcaa",
        "operator": "#d4d4d4",
        "bracket": "#ffd700",
        "error": "#f14c4c",
        "success": "#6a9955",
        "info": "#4fc1ff",
        "warning": "#cca700",
        "tab_selected": "#0e639c",
        "tab_selected_fg": "#ffffff",
        "tree_bg": "#252526",
        "tree_fg": "#d4d4d4",
        "tree_field_bg": "#252526",
        "entry_bg": "#252526",
        "entry_fg": "#d4d4d4",
        "menu_bg": "#252526",
        "menu_fg": "#d4d4d4",
        "menu_active_bg": "#0e639c",
        "menu_active_fg": "#ffffff",
        "scrollbar_bg": "#252526",
        "scrollbar_trough": "#1e1e1e",
        "scrollbar_arrow": "#d4d4d4",
        "checkbutton_bg": "#1e1e1e",
        "checkbutton_fg": "#d4d4d4",
        "combobox_bg": "#252526",
        "combobox_fg": "#d4d4d4",
        "notebook_bg": "#1e1e1e",
        "notebook_tab_bg": "#252526",
        "notebook_tab_fg": "#d4d4d4",
        "button_bg": "#252526",
        "button_fg": "#d4d4d4",
        "button_active_bg": "#0e639c",
        "button_pressed_bg": "#1177bb",
        "label_bg": "#1e1e1e",
        "label_fg": "#d4d4d4",
        "frame_bg": "#1e1e1e",
        "panel_bg": "#252526",
        "explorer_header_bg": "#252526",
        "explorer_header_fg": "#d4d4d4",
        "open_files_bg": "#252526",
        "open_files_fg": "#d4d4d4",
        "open_files_item_bg": "#2a2d2e",
        "open_files_item_fg": "#d4d4d4",
        "open_files_close_bg": "#f14c4c",
        "open_files_close_fg": "#ffffff",
    }

    LIGHT = {
        "name": "Claro",
        "bg": "#ffffff",
        "bg_light": "#f3f3f3",
        "bg_lighter": "#e8e8e8",
        "fg": "#1e1e1e",
        "accent": "#0078d4",
        "accent_hover": "#1a8ad4",
        "border": "#d4d4d4",
        "toolbar_bg": "#e8e8e8",
        "statusbar_bg": "#0078d4",
        "statusbar_fg": "#ffffff",
        "selection": "#add6ff",
        "line_number": "#237893",
        "line_number_bg": "#f3f3f3",
        "current_line": "#e8f0fe",
        "keyword": "#0000ff",
        "type": "#267f99",
        "string": "#a31515",
        "comment": "#008000",
        "number": "#098658",
        "preprocessor": "#af00db",
        "function": "#795e26",
        "operator": "#1e1e1e",
        "bracket": "#811f3f",
        "error": "#f14c4c",
        "success": "#008000",
        "info": "#0078d4",
        "warning": "#cca700",
        "tab_selected": "#0078d4",
        "tab_selected_fg": "#ffffff",
        "tree_bg": "#f3f3f3",
        "tree_fg": "#1e1e1e",
        "tree_field_bg": "#f3f3f3",
        "entry_bg": "#ffffff",
        "entry_fg": "#1e1e1e",
        "menu_bg": "#f3f3f3",
        "menu_fg": "#1e1e1e",
        "menu_active_bg": "#0078d4",
        "menu_active_fg": "#ffffff",
        "scrollbar_bg": "#e8e8e8",
        "scrollbar_trough": "#ffffff",
        "scrollbar_arrow": "#1e1e1e",
        "checkbutton_bg": "#ffffff",
        "checkbutton_fg": "#1e1e1e",
        "combobox_bg": "#ffffff",
        "combobox_fg": "#1e1e1e",
        "notebook_bg": "#ffffff",
        "notebook_tab_bg": "#f3f3f3",
        "notebook_tab_fg": "#1e1e1e",
        "button_bg": "#f3f3f3",
        "button_fg": "#1e1e1e",
        "button_active_bg": "#0078d4",
        "button_pressed_bg": "#1a8ad4",
        "label_bg": "#ffffff",
        "label_fg": "#1e1e1e",
        "frame_bg": "#ffffff",
        "panel_bg": "#f3f3f3",
        "explorer_header_bg": "#f3f3f3",
        "explorer_header_fg": "#1e1e1e",
        "open_files_bg": "#f3f3f3",
        "open_files_fg": "#1e1e1e",
        "open_files_item_bg": "#e8e8e8",
        "open_files_item_fg": "#1e1e1e",
        "open_files_close_bg": "#f14c4c",
        "open_files_close_fg": "#ffffff",
    }

    THEMES = {
        "dark": DARK,
        "light": LIGHT,
    }

    def __init__(self):
        self.current = "dark"

    def get_colors(self):
        """Obtiene los colores del tema actual."""
        return self.THEMES[self.current]

    def set_theme(self, name):
        """Cambia el tema actual."""
        if name in self.THEMES:
            self.current = name
            return True
        return False

    def toggle(self):
        """Alterna entre claro y oscuro."""
        self.current = "light" if self.current == "dark" else "dark"
        return self.current

    def is_dark(self):
        """Verifica si el tema actual es oscuro."""
        return self.current == "dark"