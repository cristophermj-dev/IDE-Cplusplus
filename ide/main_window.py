"""
Ventana principal de MeriCode C++ - interfaz gráfica completa.

Este módulo contiene la ventana principal del IDE con todas sus
funcionalidades:
- Editor de código con resaltado de sintaxis y números de línea.
- Explorador de archivos con archivos abiertos y árbol de directorios.
- Barra de herramientas con acciones de archivo, proyecto y compilación.
- Menús completos (Archivo, Proyecto, Editar, Ver, Compilar, Ejecutar, Depurar, Ayuda).
- Consola de salida con pestañas para salida, errores y depuración.
- Gestión de proyectos .cmj y creación de clases.
- Compilación, ejecución y depuración de programas C++.
- Temas claro y oscuro.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter import font as tkfont
import subprocess
import threading
from datetime import datetime

# Si se ejecuta directamente (python3 ide/main_window.py), ajustar el path
# para que los imports absolutos del paquete funcionen correctamente.
if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ide.syntax_highlighter import SyntaxHighlighter
    from ide.editor import LineNumbers
    from ide.console import ConsolePanel
    from ide.search_dialog import SearchDialog
    from ide.compiler import Compiler
    from ide.theme import ThemeManager
    from ide.project import Project, ProjectManager
    from ide.uml_editor import UMLEditor
    from ide.github_sync import GitHubSync, GitHubCredentialsDialog
else:
    from .syntax_highlighter import SyntaxHighlighter
    from .editor import LineNumbers
    from .console import ConsolePanel
    from .search_dialog import SearchDialog
    from .compiler import Compiler
    from .theme import ThemeManager
    from .project import Project, ProjectManager
    from .uml_editor import UMLEditor
    from .github_sync import GitHubSync, GitHubCredentialsDialog


class CodeEditor(tk.Frame):
    """Editor de código con resaltado de sintaxis y números de línea.

    Esta clase representa una pestaña individual del editor de código.
    Incluye un widget Text de Tkinter con resaltado de sintaxis C++,
    números de línea sincronizados, barras de desplazamiento horizontal
    y vertical, autocompletado de brackets y comillas, indentación
    automática y resaltado de la línea actual del cursor.
    """

    def __init__(self, parent, ide, **kwargs):
        super().__init__(parent, **kwargs)
        self.ide = ide
        self.file_path = None
        self._modified = False

        colors = ide.theme_manager.get_colors()
        self.configure(bg=colors["bg"])

        # Fuentes
        self.editor_font = tkfont.Font(family="Consolas", size=11)
        self.line_numbers_font = tkfont.Font(family="Consolas", size=11)

        # Widget de texto
        self.text = tk.Text(
            self,
            bg=colors["bg"],
            fg=colors["fg"],
            insertbackground=colors["fg"],
            selectbackground=colors["selection"],
            selectforeground=colors["fg"],
            font=self.editor_font,
            wrap="none",
            undo=True,
            autoseparators=True,
            maxundo=-1,
            padx=5,
            pady=5,
            relief="flat",
            borderwidth=0,
            tabs=("4c",),
        )

        # Números de línea
        self.line_numbers = LineNumbers(self, self.text, ide.theme_manager)
        self.line_numbers.pack(side="left", fill="y")

        # Scrollbars
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.text.pack(side="left", fill="both", expand=True)

        # Resaltador de sintaxis
        self.highlighter = SyntaxHighlighter(self.text, ide.theme_manager)
        self.line_numbers.attach()

        # Bindings del editor
        self._setup_bindings()

        # Línea actual resaltada
        self.text.tag_configure("current_line", background=colors["current_line"])
        self._highlight_current_line()

    def apply_theme(self):
        """Reaplica el tema al editor."""
        colors = self.ide.theme_manager.get_colors()
        self.configure(bg=colors["bg"])
        self.text.configure(
            bg=colors["bg"],
            fg=colors["fg"],
            insertbackground=colors["fg"],
            selectbackground=colors["selection"],
            selectforeground=colors["fg"],
        )
        self.text.tag_configure("current_line", background=colors["current_line"])
        self.line_numbers.apply_theme()
        self.highlighter.apply_theme()
        self._highlight_current_line()

    def _setup_bindings(self):
        """Configura los bindings del editor."""
        self.text.bind("<Control-s>", lambda e: self.ide.save_file())
        self.text.bind("<Control-S>", lambda e: self.ide.save_file())
        self.text.bind("<Control-o>", lambda e: self.ide.open_file())
        self.text.bind("<Control-O>", lambda e: self.ide.open_file())
        self.text.bind("<Control-n>", lambda e: self.ide.new_file(add_to_project=True))
        self.text.bind("<Control-N>", lambda e: self.ide.new_file(add_to_project=True))
        self.text.bind("<Control-f>", lambda e: self.ide.show_search())
        self.text.bind("<Control-F>", lambda e: self.ide.show_search())
        self.text.bind("<Control-h>", lambda e: self.ide.show_replace())
        self.text.bind("<Control-H>", lambda e: self.ide.show_replace())
        self.text.bind("<F5>", lambda e: self.ide.run_program())
        self.text.bind("<F7>", lambda e: self.ide.compile_program())
        self.text.bind("<F6>", lambda e: self.ide.debug_program())
        self.text.bind("<Control-Shift-S>", lambda e: self.ide.save_file_as())
        self.text.bind("<Control-Shift-s>", lambda e: self.ide.save_file_as())
        self.text.bind("<Escape>", lambda e: self.ide.hide_panel())

        # Modificación del texto
        self.text.bind("<<Modified>>", self._on_modified)

        # Autocompletado de llaves, paréntesis y corchetes
        self.text.bind("(", self._auto_close_bracket)
        self.text.bind("[", self._auto_close_bracket)
        self.text.bind("{", self._auto_close_bracket)
        self.text.bind('"', self._auto_close_quote)
        self.text.bind("'", self._auto_close_quote)

        # Enter con indentación automática
        self.text.bind("<Return>", self._auto_indent)

        # Tab para indentar
        self.text.bind("<Tab>", self._insert_tab)

        # Resaltar línea actual
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<ButtonRelease-1>", self._on_click)

        # Scroll sincronizado con números de línea
        self.text.bind("<MouseWheel>", self._on_mousewheel)
        self.text.bind("<Button-4>", self._on_mousewheel)
        self.text.bind("<Button-5>", self._on_mousewheel)

    def _on_modified(self, event=None):
        """Marca el archivo como modificado."""
        if self.text.edit_modified():
            self._modified = True
            self.ide.update_title()
            self.ide.update_status("Archivo modificado")
            self.ide.file_explorer.refresh_open_files()
        self.text.edit_modified(False)

    def _highlight_current_line(self):
        """Resalta la línea actual del cursor."""
        try:
            self.text.tag_remove("current_line", "1.0", "end")
            current_line = self.text.index("insert").split(".")[0]
            self.text.tag_add("current_line", f"{current_line}.0",
                              f"{current_line}.0 lineend")
        except tk.TclError:
            pass

    def _on_key_release(self, event=None):
        """Maneja la liberación de teclas."""
        self._highlight_current_line()
        if event and event.keysym in ("Up", "Down", "Left", "Right",
                                      "Home", "End", "Prior", "Next"):
            self.ide.update_cursor_position()

    def _on_click(self, event=None):
        """Maneja los clics del mouse."""
        self._highlight_current_line()
        self.ide.update_cursor_position()

    def _on_mousewheel(self, event=None):
        """Maneja el scroll del mouse."""
        self.ide.after(50, self._highlight_current_line)

    def _auto_close_bracket(self, event):
        """Autocompleta brackets."""
        pairs = {"(": ")", "[": "]", "{": "}"}
        char = event.char
        if char in pairs:
            # Verificar si hay texto seleccionado
            try:
                sel_start = self.text.index("sel.first")
                sel_end = self.text.index("sel.last")
                selected = self.text.get(sel_start, sel_end)
                self.text.insert("insert", char + selected + pairs[char])
                self.text.tag_add("sel", sel_start, f"{sel_start}+{len(char + selected)}c")
                return "break"
            except tk.TclError:
                pass
            self.text.insert("insert", char + pairs[char])
            self.text.mark_set("insert", "insert-1c")
            return "break"
        return None

    def _auto_close_quote(self, event):
        """Autocompleta comillas."""
        char = event.char
        try:
            # Si hay selección, rodearla
            sel_start = self.text.index("sel.first")
            sel_end = self.text.index("sel.last")
            selected = self.text.get(sel_start, sel_end)
            self.text.insert("insert", char + selected + char)
            self.text.tag_add("sel", sel_start, f"{sel_start}+{len(char + selected)}c")
            return "break"
        except tk.TclError:
            pass

        # Verificar si ya hay una comilla de cierre
        try:
            current_pos = self.text.index("insert")
            next_char = self.text.get(current_pos, f"{current_pos}+1c")
            if next_char == char:
                self.text.mark_set("insert", f"{current_pos}+1c")
                return "break"
        except tk.TclError:
            pass

        self.text.insert("insert", char + char)
        self.text.mark_set("insert", "insert-1c")
        return "break"

    def _auto_indent(self, event=None):
        """Indentación automática al presionar Enter."""
        current_line = self.text.index("insert").split(".")[0]
        line_start = f"{current_line}.0"
        line_end = f"{current_line}.0 lineend"
        line_text = self.text.get(line_start, line_end)

        # Obtener la indentación de la línea actual
        indent = ""
        for char in line_text:
            if char in " \t":
                indent += char
            else:
                break

        # Si la línea termina con {, aumentar indentación
        stripped = line_text.strip()
        if stripped.endswith("{") or stripped.endswith("("):
            indent += "    "

        # Si la línea empieza con }, reducir indentación
        if stripped.startswith("}"):
            indent = indent[:-4] if len(indent) >= 4 else ""

        self.text.insert("insert", "\n" + indent)
        return "break"

    def _insert_tab(self, event=None):
        """Inserta 4 espacios al presionar Tab."""
        self.text.insert("insert", "    ")
        return "break"

    def get_content(self):
        """Obtiene el contenido del editor."""
        return self.text.get("1.0", "end-1c")

    def set_content(self, content):
        """Establece el contenido del editor."""
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.edit_reset()
        self._modified = False
        # Resaltar el contenido recién cargado
        self.highlighter.highlight()

    def get_breakpoints(self):
        """Devuelve el conjunto de líneas con breakpoints del editor."""
        return self.line_numbers.breakpoints

    def is_modified(self):
        """Verifica si el archivo ha sido modificado."""
        return self._modified

    def set_modified(self, value):
        """Establece el estado de modificación."""
        self._modified = value
        self.ide.update_title()

    def clear(self):
        """Limpia el editor."""
        self.text.delete("1.0", "end")
        self.file_path = None
        self._modified = False


class FileExplorer(tk.Frame):
    """Explorador de archivos lateral con archivos abiertos y proyecto.

    Muestra tres secciones principales:
    - Proyecto: Nombre y botón para cerrar el proyecto activo.
    - Archivos abiertos: Lista de pestañas abiertas en el editor.
    - Árbol de archivos: Explorador de directorios del sistema.

    Incluye botones para navegar hacia arriba, actualizar el árbol,
    y hacer doble clic para abrir archivos en el editor.
    """

    def __init__(self, parent, ide, **kwargs):
        super().__init__(parent, **kwargs)
        self.ide = ide
        self._current_dir = None

        self._build_ui()

    def _build_ui(self):
        """Construye la interfaz del explorador."""
        colors = self.ide.theme_manager.get_colors()

        style = ttk.Style()
        style.configure("Explorer.Treeview",
                        background=colors["tree_bg"],
                        foreground=colors["tree_fg"],
                        fieldbackground=colors["tree_field_bg"],
                        borderwidth=0)
        style.configure("Explorer.Treeview.Item",
                        padding=(2, 2))

        # Barra superior
        header = ttk.Frame(self)
        header.pack(fill="x", padx=3, pady=3)
        ttk.Label(header, text="📁 EXPLORADOR",
                  font=("Arial", 9, "bold")).pack(side="left")

        # Botones del explorador
        btn_frame = ttk.Frame(header)
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="⬆", width=3,
                   command=self.go_up).pack(side="left", padx=1)
        ttk.Button(btn_frame, text="🔄", width=3,
                   command=self.refresh).pack(side="left", padx=1)

        # --- Sección de proyecto ---
        self.project_frame = ttk.Frame(self)
        self.project_frame.pack(fill="x", padx=3, pady=(5, 0))

        self.project_label = ttk.Label(self.project_frame,
                                       text="📦 Sin proyecto",
                                       font=("Arial", 9, "bold"))
        self.project_label.pack(side="left", padx=2)

        self.close_project_btn = ttk.Button(self.project_frame, text="✖ Cerrar",
                                            width=7,
                                            command=self.ide.close_project,
                                            state="disabled")
        self.close_project_btn.pack(side="right", padx=2)

        # --- Sección de archivos abiertos ---
        open_files_header = ttk.Frame(self)
        open_files_header.pack(fill="x", padx=3, pady=(8, 0))
        ttk.Label(open_files_header, text="📂 ARCHIVOS ABIERTOS",
                  font=("Arial", 9, "bold")).pack(side="left")

        # Lista de archivos abiertos
        self.open_files_frame = ttk.Frame(self)
        self.open_files_frame.pack(fill="x", padx=3, pady=(2, 0))

        self.open_files_list = tk.Listbox(
            self.open_files_frame,
            height=5,
            bg=colors["open_files_bg"],
            fg=colors["open_files_fg"],
            selectbackground=colors["accent"],
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            font=("Consolas", 9),
            activestyle="none",
        )
        self.open_files_list.pack(fill="x", side="left", expand=True)
        self.open_files_list.bind("<Double-1>", self._on_open_file_click)
        self.open_files_list.bind("<Button-3>", self._on_open_file_right_click)

        # --- Separador ---
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=3, pady=5)

        # Árbol de archivos
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            self.tree_frame,
            style="Explorer.Treeview",
            show="tree",
            selectmode="browse",
        )
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical",
                                  command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Bindings
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Return>", self._on_double_click)

    def apply_theme(self):
        """Reaplica el tema al explorador."""
        colors = self.ide.theme_manager.get_colors()
        style = ttk.Style()
        style.configure("Explorer.Treeview",
                        background=colors["tree_bg"],
                        foreground=colors["tree_fg"],
                        fieldbackground=colors["tree_field_bg"],
                        borderwidth=0)
        self.open_files_list.configure(
            bg=colors["open_files_bg"],
            fg=colors["open_files_fg"],
            selectbackground=colors["accent"],
        )

    def refresh_open_files(self):
        """Actualiza la lista de archivos abiertos."""
        self.open_files_list.delete(0, "end")
        for file_id, editor in self.ide.open_files.items():
            if editor.file_path:
                name = os.path.basename(editor.file_path)
                if editor.is_modified():
                    name = "• " + name
                self.open_files_list.insert("end", name)
            else:
                tab_text = self.ide.notebook.tab(editor, "text")
                self.open_files_list.insert("end", tab_text)

    def _on_open_file_click(self, event=None):
        """Abre el archivo seleccionado en la lista de archivos abiertos."""
        selection = self.open_files_list.curselection()
        if not selection:
            return
        index = selection[0]
        editors = list(self.ide.open_files.values())
        if index < len(editors):
            editor = editors[index]
            self.ide.notebook.select(editor)
            self.ide.current_editor = editor
            self.ide.update_title()
            self.ide.update_cursor_position()

    def _on_open_file_right_click(self, event=None):
        """Muestra menú contextual para archivos abiertos."""
        selection = self.open_files_list.curselection()
        if not selection:
            return
        index = selection[0]
        editors = list(self.ide.open_files.values())
        if index >= len(editors):
            return

        editor = editors[index]
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Cerrar archivo",
                         command=lambda: self.ide.close_editor(editor))
        menu.add_command(label="Guardar",
                         command=lambda: self.ide.save_editor(editor))
        menu.add_separator()
        menu.add_command(label="Cerrar todos",
                         command=self.ide.close_all_tabs)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def update_project_display(self):
        """Actualiza la visualización del proyecto."""
        if self.ide.project_manager.has_project():
            project = self.ide.project_manager.current_project
            self.project_label.config(text=f"📦 {project.name}")
            self.close_project_btn.config(state="normal")
        else:
            self.project_label.config(text="📦 Sin proyecto")
            self.close_project_btn.config(state="disabled")

    def open_directory(self, path=None):
        """Abre un directorio en el explorador."""
        if path is None:
            path = filedialog.askdirectory(parent=self.ide, title="Abrir carpeta")
            if not path:
                return

        self._current_dir = os.path.abspath(path)
        self.refresh()
        self.ide.update_status(f"Carpeta: {self._current_dir}")

    def refresh(self):
        """Refresca el árbol de archivos."""
        if not self._current_dir:
            return

        self.tree.delete(*self.tree.get_children())
        root_item = self.tree.insert("", "end", text=f"📁 {os.path.basename(self._current_dir) or self._current_dir}",
                                     open=True)
        self._populate_directory(self._current_dir, root_item)

    def _populate_directory(self, path, parent_item):
        """Puebla el árbol con el contenido del directorio."""
        try:
            entries = sorted(os.listdir(path))
            # Separar directorios y archivos
            dirs = [e for e in entries if os.path.isdir(os.path.join(path, e))]
            files = [e for e in entries if os.path.isfile(os.path.join(path, e))]

            # Omitir directorios ocultos
            dirs = [d for d in dirs if not d.startswith(".")]
            files = [f for f in files if not f.startswith(".")]

            for d in dirs:
                item = self.tree.insert(parent_item, "end",
                                        text=f"📁 {d}", open=False)
                # Añadir placeholder para expansión
                self._populate_directory(os.path.join(path, d), item)

            for f in files:
                ext = os.path.splitext(f)[1].lower()
                icon = self._get_file_icon(ext)
                self.tree.insert(parent_item, "end", text=f"{icon} {f}",
                                 values=(os.path.join(path, f),))

        except PermissionError:
            pass

    def _get_file_icon(self, ext):
        """Obtiene un icono para el tipo de archivo."""
        icons = {
            ".cpp": "📄", ".cc": "📄", ".cxx": "📄", ".c": "📄",
            ".h": "📋", ".hpp": "📋", ".hh": "📋",
            ".cmj": "📦",
            ".txt": "📝", ".md": "📝", ".py": "🐍",
            ".json": "📊", ".xml": "📊", ".yaml": "📊", ".yml": "📊",
            ".sh": "⚙", ".bash": "⚙",
            ".png": "🖼", ".jpg": "🖼", ".jpeg": "🖼", ".gif": "🖼",
            ".pdf": "📕",
        }
        return icons.get(ext, "📄")

    def _on_double_click(self, event=None):
        """Abre un archivo al hacer doble clic."""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, "values")
        if values:
            file_path = values[0]
            if os.path.isfile(file_path):
                self.ide.open_file_path(file_path)

    def go_up(self):
        """Sube un nivel de directorio."""
        if self._current_dir:
            parent = os.path.dirname(self._current_dir)
            if parent and os.path.isdir(parent):
                self._current_dir = parent
                self.refresh()

    def get_current_dir(self):
        """Obtiene el directorio actual."""
        return self._current_dir


class MainWindow(tk.Tk):
    """Ventana principal de MeriCode C++.

    Esta es la clase principal que orquesta toda la aplicación.
    Configura la ventana, los estilos, los menús, la barra de
    herramientas, la barra de estado, y todos los paneles:

    - Explorador de archivos (izquierda).
    - Editor de código con pestañas (centro).
    - Consola de salida (abajo).

    También maneja la gestión de archivos, proyectos, compilación,
    ejecución, depuración, temas y atajos de teclado.
    """

    def __init__(self):
        super().__init__()

        self.title("MeriCode C++")
        self.geometry("1200x750")
        self.minsize(800, 500)

        # Gestor de temas
        self.theme_manager = ThemeManager()

        # Gestor de proyectos
        self.project_manager = ProjectManager()

        # Sincronización con GitHub
        self.github = GitHubSync()

        # Configurar estilo
        self._setup_styles()

        # Compilador
        self.compiler = Compiler()

        # Gestión de archivos
        self.open_files = {}  # id -> CodeEditor
        self.current_editor = None
        self.next_file_id = 0

        # Diálogo de búsqueda
        self.search_dialog = None

        self._build_ui()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()
        self._setup_shortcuts()

        # Vincular cierre de ventana
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Crear archivo inicial
        self.new_file()

        # Verificar compilador
        self._check_compiler_status()

        # Actualizar título
        self.update_title()

    def _setup_styles(self):
        """Configura los estilos de la aplicación."""
        style = ttk.Style()
        style.theme_use("clam")

        colors = self.theme_manager.get_colors()

        # Configurar colores base
        self.configure(bg=colors["bg"])

        style.configure(".", background=colors["bg"], foreground=colors["fg"])
        style.configure("TFrame", background=colors["bg"])
        style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
        style.configure("TButton", background=colors["button_bg"], foreground=colors["button_fg"],
                        borderwidth=1, padding=(8, 4),
                        relief="flat", focusthickness=0)
        style.map("TButton",
                  background=[("active", colors["button_active_bg"]),
                              ("pressed", colors["button_pressed_bg"])],
                  foreground=[("active", "#ffffff")])
        style.configure("TNotebook", background=colors["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=colors["notebook_tab_bg"],
                        foreground=colors["notebook_tab_fg"],
                        padding=(12, 6), borderwidth=1)
        style.map("TNotebook.Tab",
                  background=[("selected", colors["tab_selected"])],
                  foreground=[("selected", colors["tab_selected_fg"])])
        style.configure("TEntry", fieldbackground=colors["entry_bg"],
                        foreground=colors["entry_fg"],
                        insertcolor=colors["entry_fg"], borderwidth=1)
        style.configure("TCombobox", fieldbackground=colors["combobox_bg"],
                        foreground=colors["combobox_fg"])
        style.configure("TCheckbutton", background=colors["checkbutton_bg"],
                        foreground=colors["checkbutton_fg"])
        style.map("TCheckbutton",
                  background=[("active", colors["checkbutton_bg"])])
        style.configure("TScrollbar", background=colors["scrollbar_bg"],
                        troughcolor=colors["scrollbar_trough"],
                        borderwidth=0, arrowcolor=colors["scrollbar_arrow"])
        style.configure("Toolbar.TFrame", background=colors["toolbar_bg"])
        style.configure("Statusbar.TFrame", background=colors["statusbar_bg"])
        style.configure("Statusbar.TLabel", background=colors["statusbar_bg"],
                        foreground=colors["statusbar_fg"])
        style.configure("Panel.TFrame", background=colors["panel_bg"])
        style.configure("Menu", background=colors["menu_bg"], foreground=colors["menu_fg"])

        # Menú
        self.option_add("*Menu.background", colors["menu_bg"])
        self.option_add("*Menu.foreground", colors["menu_fg"])
        self.option_add("*Menu.activeBackground", colors["menu_active_bg"])
        self.option_add("*Menu.activeForeground", colors["menu_active_fg"])

    def apply_theme(self):
        """Aplica el tema actual a toda la interfaz."""
        self._setup_styles()

        # Aplicar a editores abiertos
        for editor in self.open_files.values():
            editor.apply_theme()

        # Aplicar al explorador
        self.file_explorer.apply_theme()

        # Aplicar a la consola
        self.console.apply_theme()

        # Aplicar al editor UML
        if hasattr(self, "uml_editor") and self.uml_editor is not None:
            try:
                if self.uml_editor.winfo_exists():
                    self.uml_editor.apply_theme()
            except tk.TclError:
                pass

        # Actualizar título
        self.update_title()

    def toggle_theme(self):
        """Alterna entre tema claro y oscuro."""
        self.theme_manager.toggle()
        self.apply_theme()
        theme_name = self.theme_manager.get_colors()["name"]
        self.update_status(f"Tema: {theme_name}")

    def _build_ui(self):
        """Construye la interfaz principal."""
        # Panel principal dividido (horizontal: explorador | editor)
        self.main_paned = ttk.PanedWindow(self, orient="horizontal")
        self.main_paned.pack(fill="both", expand=True)

        # Explorador de archivos (izquierda)
        self.explorer_frame = ttk.Frame(self.main_paned, style="Panel.TFrame")
        self.file_explorer = FileExplorer(self.explorer_frame, self)
        self.file_explorer.pack(fill="both", expand=True)
        self.main_paned.add(self.explorer_frame, weight=1)

        # Área del editor (centro)
        editor_container = ttk.Frame(self.main_paned)
        self.main_paned.add(editor_container, weight=4)

        # Panel vertical (editor arriba, consola abajo) - redimensionable
        self.vertical_paned = ttk.PanedWindow(editor_container, orient="vertical")
        self.vertical_paned.pack(fill="both", expand=True)

        # Notebook para los archivos abiertos
        self.notebook = ttk.Notebook(self.vertical_paned)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.vertical_paned.add(self.notebook, weight=3)

        # Panel de consola (abajo) - se crea pero se mantiene oculto
        self.console = ConsolePanel(self.vertical_paned, self.theme_manager)
        # La consola NO se añade al layout inicialmente.
        # Solo se muestra automáticamente cuando el programa se ejecuta
        # o cuando hay errores de compilación que el estudiante debe ver.

        self._toggle_console_var = tk.BooleanVar(value=False)
        self._toggle_explorer_var = tk.BooleanVar(value=True)

    def _update_panel_buttons(self):
        """Actualiza los textos de los botones de visibilidad."""
        if hasattr(self, "explorer_toggle_btn"):
            self.explorer_toggle_btn.config(
                text="📁 OCULTAR" if self._toggle_explorer_var.get() else "📁 MOSTRAR")
        if hasattr(self, "console_toggle_btn"):
            self.console_toggle_btn.config(
                text="▤ OCULTAR" if self._toggle_console_var.get() else "▤ MOSTRAR")
        # Mostrar u ocultar los controles de consola en la parte superior
        # según si la consola está visible o no
        if hasattr(self, "top_console_controls"):
            if self._toggle_console_var.get():
                # Consola visible: ocultar controles superiores
                self.top_console_controls.pack_forget()
            else:
                # Consola oculta: mostrar controles superiores
                self.top_console_controls.pack(side="left", padx=2, pady=3)

    def _sync_auto_scroll(self):
        """Sincroniza el auto scroll de la barra superior con la consola."""
        if hasattr(self, "console") and hasattr(self.console, "_auto_scroll_var"):
            self.console._auto_scroll_var.set(self.top_auto_scroll_var.get())

    def _toggle_console(self):
        """Muestra u oculta la consola."""
        if self._toggle_console_var.get():
            # Verificar si ya está en el PanedWindow antes de añadirlo
            try:
                self.vertical_paned.pane(self.console)
            except tk.TclError:
                self.vertical_paned.add(self.console, weight=1)
        else:
            try:
                self.vertical_paned.forget(self.console)
            except tk.TclError:
                pass
        self._update_panel_buttons()

    def toggle_console(self):
        """Alterna la visibilidad de la consola."""
        self._toggle_console_var.set(not self._toggle_console_var.get())
        self._toggle_console()
        # Sincronizar el estado del auto-scroll de la barra superior
        # con el de la consola al mostrar/ocultar
        if self._toggle_console_var.get() and hasattr(self, "console"):
            self.console._auto_scroll_var.set(self.top_auto_scroll_var.get())

    def show_console(self):
        """Muestra la consola automáticamente.

        Se utiliza cuando el programa se ejecuta o cuando la
        compilación produce errores que el estudiante debe ver.
        """
        self._toggle_console_var.set(True)
        self._toggle_console()

    def _toggle_explorer(self):
        """Muestra u oculta el explorador de archivos."""
        if self._toggle_explorer_var.get():
            # Verificar si ya está en el PanedWindow antes de añadirlo
            try:
                self.main_paned.pane(self.explorer_frame)
            except tk.TclError:
                self.main_paned.add(self.explorer_frame, weight=1)
        else:
            try:
                self.main_paned.forget(self.explorer_frame)
            except tk.TclError:
                pass
        self._update_panel_buttons()

    def toggle_explorer(self):
        """Alterna la visibilidad del explorador de archivos."""
        self._toggle_explorer_var.set(not self._toggle_explorer_var.get())
        self._toggle_explorer()

    def _create_menus(self):
        """Crea la barra de menús."""
        menubar = tk.Menu(self)

        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Nuevo archivo", accelerator="Ctrl+N",
                              command=lambda: self.new_file(add_to_project=True))
        file_menu.add_command(label="Abrir archivo...", accelerator="Ctrl+O",
                              command=self.open_file)
        file_menu.add_command(label="Abrir carpeta...",
                              command=self.file_explorer.open_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Guardar", accelerator="Ctrl+S",
                              command=self.save_file)
        file_menu.add_command(label="Guardar como...", accelerator="Ctrl+Shift+S",
                              command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Cerrar archivo", command=self.close_current_tab)
        file_menu.add_command(label="Cerrar todos", command=self.close_all_tabs)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", accelerator="Alt+F4",
                              command=self._on_close)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # Menú Proyecto
        project_menu = tk.Menu(menubar, tearoff=False)
        project_menu.add_command(label="Nuevo proyecto...",
                                 command=self.new_project)
        project_menu.add_command(label="Abrir proyecto...",
                                 command=self.open_project)
        project_menu.add_separator()
        project_menu.add_command(label="Guardar proyecto",
                                 command=self.save_project)
        project_menu.add_command(label="Cerrar proyecto",
                                 command=self.close_project)
        project_menu.add_separator()
        project_menu.add_command(label="Nueva clase (.h y .cpp)...",
                                 command=self.new_class)
        menubar.add_cascade(label="Proyecto", menu=project_menu)

        # Menú Editar
        edit_menu = tk.Menu(menubar, tearoff=False)
        edit_menu.add_command(label="Deshacer", accelerator="Ctrl+Z",
                              command=lambda: self._editor_action("edit_undo"))
        edit_menu.add_command(label="Rehacer", accelerator="Ctrl+Y",
                              command=lambda: self._editor_action("edit_redo"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Cortar", accelerator="Ctrl+X",
                              command=lambda: self._editor_action("edit_cut"))
        edit_menu.add_command(label="Copiar", accelerator="Ctrl+C",
                              command=lambda: self._editor_action("edit_copy"))
        edit_menu.add_command(label="Pegar", accelerator="Ctrl+V",
                              command=lambda: self._editor_action("edit_paste"))
        edit_menu.add_separator()
        edit_menu.add_command(label="Buscar...", accelerator="Ctrl+F",
                              command=self.show_search)
        edit_menu.add_command(label="Reemplazar...", accelerator="Ctrl+H",
                              command=self.show_replace)
        edit_menu.add_separator()
        edit_menu.add_command(label="Seleccionar todo", accelerator="Ctrl+A",
                              command=lambda: self._editor_action("edit_select_all"))
        edit_menu.add_command(label="Ir a línea...", accelerator="Ctrl+G",
                              command=self.go_to_line)
        menubar.add_cascade(label="Editar", menu=edit_menu)

        # Menú Ver
        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_checkbutton(label="Explorador de archivos",
                                  variable=self._toggle_explorer_var,
                                  command=self._toggle_explorer)
        view_menu.add_checkbutton(label="Consola", variable=self._toggle_console_var,
                                  command=self._toggle_console)
        view_menu.add_separator()
        view_menu.add_command(label="Tema claro", command=lambda: self.set_theme("light"))
        view_menu.add_command(label="Tema oscuro", command=lambda: self.set_theme("dark"))
        view_menu.add_command(label="Alternar tema", accelerator="Ctrl+T",
                              command=self.toggle_theme)
        view_menu.add_separator()
        view_menu.add_command(label="Acercar", accelerator="Ctrl++",
                              command=lambda: self.change_font_size(1))
        view_menu.add_command(label="Alejar", accelerator="Ctrl+-",
                              command=lambda: self.change_font_size(-1))
        view_menu.add_command(label="Restablecer zoom", accelerator="Ctrl+0",
                              command=self.reset_font_size)
        menubar.add_cascade(label="Ver", menu=view_menu)

        # Menú Compilar
        compile_menu = tk.Menu(menubar, tearoff=False)
        compile_menu.add_command(label="Compilar", accelerator="F7",
                                 command=self.compile_program)
        compile_menu.add_command(label="Compilar y ejecutar", accelerator="F6",
                                 command=self.compile_and_run)
        compile_menu.add_separator()
        compile_menu.add_command(label="Detener", accelerator="Shift+F5",
                                 command=self.stop_program)
        menubar.add_cascade(label="Compilar", menu=compile_menu)

        # Menú Ejecutar
        run_menu = tk.Menu(menubar, tearoff=False)
        run_menu.add_command(label="Ejecutar", accelerator="F5",
                             command=self.run_program)
        run_menu.add_command(label="Ejecutar con argumentos...",
                             command=self.run_with_args)
        run_menu.add_separator()
        run_menu.add_command(label="Detener", accelerator="Shift+F5",
                             command=self.stop_program)
        menubar.add_cascade(label="Ejecutar", menu=run_menu)

        # Menú Depurar
        debug_menu = tk.Menu(menubar, tearoff=False)
        debug_menu.add_command(label="Depurar con GDB", accelerator="F6",
                               command=self.debug_program)
        debug_menu.add_separator()
        debug_menu.add_command(label="Configurar depurador...",
                               command=self.show_debug_settings)
        menubar.add_cascade(label="Depurar", menu=debug_menu)

        # Menú UML
        uml_menu = tk.Menu(menubar, tearoff=False)
        uml_menu.add_command(label="Nuevo diagrama UML",
                             command=self.open_uml_editor)
        uml_menu.add_separator()
        uml_menu.add_command(label="Guardar XML",
                             command=self.save_uml_xml)
        uml_menu.add_command(label="Abrir XML...",
                             command=self.open_uml_xml)
        uml_menu.add_separator()
        uml_menu.add_command(label="Exportar a PDF...",
                             command=self.export_uml_pdf)
        uml_menu.add_command(label="Exportar a PNG...",
                             command=self.export_uml_png)
        menubar.add_cascade(label="UML", menu=uml_menu)

        # Menú GitHub
        github_menu = tk.Menu(menubar, tearoff=False)
        github_menu.add_command(label="⚙ Configurar GitHub...",
                                command=self.configure_github)
        github_menu.add_separator()
        github_menu.add_command(label="📂 Clonar proyecto desde GitHub...",
                                command=self.github_clone)
        github_menu.add_command(label="🚀 Publicar proyecto en GitHub...",
                                command=self.github_publish)
        github_menu.add_command(label="📤 Commit y sincronizar (push)...",
                                command=self.github_push)
        github_menu.add_command(label="📥 Sincronizar (pull)",
                                command=self.github_pull)
        github_menu.add_separator()
        github_menu.add_command(label="🔎 Estado del repositorio",
                                command=self.github_status)
        menubar.add_cascade(label="GitHub", menu=github_menu)

        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        help_menu.add_command(label="Atajos de teclado", command=self.show_shortcuts)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        self.config(menu=menubar)

    def _create_toolbar(self):
        """Crea la barra de herramientas."""
        toolbar = ttk.Frame(self, style="Toolbar.TFrame")
        toolbar.pack(side="top", fill="x")

        # Botones de visibilidad de paneles
        self.explorer_toggle_btn = ttk.Button(
            toolbar, text="📁 OCULTAR", width=9,
            command=self.toggle_explorer)
        self.explorer_toggle_btn.pack(side="left", padx=2, pady=3)

        self.console_toggle_btn = ttk.Button(
            toolbar, text="▤ OCULTAR", width=9,
            command=self.toggle_console)
        self.console_toggle_btn.pack(side="left", padx=2, pady=3)

        # Controles de consola en la parte superior (visibles solo cuando la consola está oculta)
        self.top_console_controls = ttk.Frame(toolbar, style="Toolbar.TFrame")
        # Inicialmente la consola está oculta, así que estos controles se mostrarán
        # mediante _update_panel_buttons() al final de este método.

        # Botón para limpiar la consola
        ttk.Button(self.top_console_controls, text="🗑 Limpiar", width=10,
                   command=self.console.clear_all).pack(side="left", padx=2)

        # Checkbox de auto-scroll sincronizado con la consola
        self.top_auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.top_console_controls, text="Auto scroll",
                        variable=self.top_auto_scroll_var,
                        command=self._sync_auto_scroll).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5, pady=3)

        # Botones de archivo
        ttk.Button(toolbar, text="📄 Nuevo", width=8,
                   command=lambda: self.new_file(add_to_project=True)).pack(side="left", padx=2, pady=3)
        ttk.Button(toolbar, text="📂 Abrir", width=8,
                   command=self.open_file).pack(side="left", padx=2, pady=3)
        ttk.Button(toolbar, text="💾 Guardar", width=8,
                   command=self.save_file).pack(side="left", padx=2, pady=3)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5, pady=3)

        # Botones de proyecto
        ttk.Button(toolbar, text="📦 Proyecto", width=10,
                   command=self.new_project).pack(side="left", padx=2, pady=3)
        ttk.Button(toolbar, text="➕ Clase", width=8,
                   command=self.new_class).pack(side="left", padx=2, pady=3)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5, pady=3)

        # Botones de compilación/ejecución
        ttk.Button(toolbar, text="🛠 Compilar", width=10,
                   command=self.compile_program).pack(side="left", padx=2, pady=3)
        ttk.Button(toolbar, text="▶ Ejecutar", width=10,
                   command=self.run_program).pack(side="left", padx=2, pady=3)
        ttk.Button(toolbar, text="🐛 Depurar", width=10,
                   command=self.debug_program).pack(side="left", padx=2, pady=3)
        ttk.Button(toolbar, text="⏹ Detener", width=9,
                   command=self.stop_program).pack(side="left", padx=2, pady=3)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5, pady=3)

        # Selector de estándar C++
        ttk.Label(toolbar, text="C++:").pack(side="left", padx=2)
        self.std_var = tk.StringVar(value="c++17")
        std_combo = ttk.Combobox(toolbar, textvariable=self.std_var,
                                 values=["c++11", "c++14", "c++17", "c++20"],
                                 width=8, state="readonly")
        std_combo.pack(side="left", padx=2)

        # Botón tema
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5, pady=3)
        ttk.Button(toolbar, text="🌓 Tema", width=7,
                   command=self.toggle_theme).pack(side="left", padx=2, pady=3)

        # Botón UML
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5, pady=3)
        ttk.Button(toolbar, text="📐 UML", width=8,
                   command=self.open_uml_editor).pack(side="left", padx=2, pady=3)

        # Botón GitHub
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5, pady=3)
        ttk.Button(toolbar, text="📂 Clonar",
                   command=self.github_clone).pack(side="left", padx=2, pady=3)
        ttk.Button(toolbar, text="🐙 GitHub", width=9,
                   command=self.github_publish).pack(side="left", padx=2, pady=3)

        # Botón buscar
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=5, pady=3)
        ttk.Button(toolbar, text="🔍 Buscar", width=8,
                   command=self.show_search).pack(side="left", padx=2, pady=3)

        # Configurar visibilidad inicial de los controles de consola superiores
        # (visibles porque la consola está oculta al inicio)
        self._update_panel_buttons()

    def _create_statusbar(self):
        """Crea la barra de estado."""
        self.status_bar = ttk.Frame(self, style="Statusbar.TFrame")
        self.status_bar.pack(side="bottom", fill="x")

        # Mensajes de estado
        self.status_label = ttk.Label(self.status_bar, text="Listo",
                                      style="Statusbar.TLabel")
        self.status_label.pack(side="left", padx=10, pady=3)

        # Información compilador
        self.compiler_label = ttk.Label(self.status_bar, text="",
                                        style="Statusbar.TLabel")
        self.compiler_label.pack(side="right", padx=10, pady=3)

        # Posición del cursor
        self.cursor_label = ttk.Label(self.status_bar, text="Línea 1, Columna 1",
                                      style="Statusbar.TLabel")
        self.cursor_label.pack(side="right", padx=10, pady=3)

        # Estado de compilación
        self.build_status_label = ttk.Label(self.status_bar, text="",
                                            style="Statusbar.TLabel")
        self.build_status_label.pack(side="right", padx=10, pady=3)

    def _setup_shortcuts(self):
        """Configura los atajos de teclado globales."""
        self.bind("<Control-g>", lambda e: self.go_to_line())
        self.bind("<Control-G>", lambda e: self.go_to_line())
        self.bind("<Control-plus>", lambda e: self.change_font_size(1))
        self.bind("<Control-minus>", lambda e: self.change_font_size(-1))
        self.bind("<Control-0>", lambda e: self.reset_font_size())
        self.bind("<Shift-F5>", lambda e: self.stop_program())
        self.bind("<F6>", lambda e: self.compile_and_run())
        self.bind("<Control-Shift-S>", lambda e: self.save_file_as())
        self.bind("<Control-t>", lambda e: self.toggle_theme())
        self.bind("<Control-T>", lambda e: self.toggle_theme())

    # --- Gestión de temas ---

    def set_theme(self, theme_name):
        """Establece un tema específico."""
        if self.theme_manager.set_theme(theme_name):
            self.apply_theme()
            theme_name_display = self.theme_manager.get_colors()["name"]
            self.update_status(f"Tema: {theme_name_display}")

    # --- Gestión de proyectos ---

    def new_project(self):
        """Crea un nuevo proyecto .cmj."""
        import tkinter.simpledialog as simpledialog

        name = simpledialog.askstring(
            "Nuevo proyecto",
            "Nombre del proyecto:",
            parent=self,
        )
        if not name:
            return

        # Validar nombre
        name = name.strip()
        if not name:
            messagebox.showwarning("Advertencia", "El nombre del proyecto no puede estar vacío.")
            return

        directory = filedialog.askdirectory(
            parent=self,
            title="Seleccione la carpeta donde crear el proyecto",
        )
        if not directory:
            return

        try:
            project = self.project_manager.create_project(name, directory)
            self.file_explorer.open_directory(project.path)
            self.file_explorer.update_project_display()
            self.update_status(f"Proyecto creado: {project.name}")

            # Abrir main.cpp
            main_cpp = os.path.join(project.path, "main.cpp")
            if os.path.exists(main_cpp):
                self.open_file_path(main_cpp)

            self.console.success(f"✓ Proyecto '{project.name}' creado en {project.path}\n")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el proyecto:\n{e}")

    def open_project(self):
        """Abre un proyecto .cmj existente."""
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Abrir proyecto",
            filetypes=[
                ("Proyectos C++", "*.cmj"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not file_path:
            return

        try:
            project = self.project_manager.open_project(file_path)
            self.file_explorer.open_directory(project.path)
            self.file_explorer.update_project_display()
            self.update_status(f"Proyecto abierto: {project.name}")

            # Abrir main.cpp si existe
            main_cpp = os.path.join(project.path, "main.cpp")
            if os.path.exists(main_cpp):
                self.open_file_path(main_cpp)

            self.console.success(f"✓ Proyecto '{project.name}' abierto\n")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el proyecto:\n{e}")

    def save_project(self):
        """Guarda el proyecto actual."""
        if not self.project_manager.has_project():
            messagebox.showinfo("Sin proyecto", "No hay un proyecto abierto.")
            return

        try:
            file_path = self.project_manager.save_project()
            self.update_status(f"Proyecto guardado: {file_path}")
            self.console.success(f"✓ Proyecto guardado: {file_path}\n")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el proyecto:\n{e}")

    def close_project(self):
        """Cierra el proyecto actual."""
        if not self.project_manager.has_project():
            return

        # Verificar archivos sin guardar
        unsaved = [ed for ed in self.open_files.values() if ed.is_modified()]
        if unsaved:
            result = messagebox.askyesnocancel(
                "Cerrar proyecto",
                f"Hay {len(unsaved)} archivos sin guardar. ¿Desea guardarlos antes de cerrar el proyecto?",
            )
            if result is None:
                return
            if result:
                for ed in unsaved:
                    self.current_editor = ed
                    self.save_file()

        project_name = self.project_manager.current_project.name
        self.project_manager.close_project()
        self.file_explorer.update_project_display()
        self.file_explorer._current_dir = None
        self.file_explorer.tree.delete(*self.file_explorer.tree.get_children())
        self.update_status(f"Proyecto cerrado: {project_name}")
        self.console.info(f"Proyecto '{project_name}' cerrado.\n")

    def new_class(self):
        """Crea una nueva clase con archivos .h y .cpp."""
        if not self.project_manager.has_project():
            messagebox.showinfo(
                "Sin proyecto",
                "Primero debe crear o abrir un proyecto para agregar clases.",
            )
            return

        import tkinter.simpledialog as simpledialog

        class_name = simpledialog.askstring(
            "Nueva clase",
            "Nombre de la clase:",
            parent=self,
        )
        if not class_name:
            return

        class_name = class_name.strip()
        if not class_name:
            messagebox.showwarning("Advertencia", "El nombre de la clase no puede estar vacío.")
            return

        # Validar nombre de clase (solo letras, números y guiones bajos)
        if not class_name.replace("_", "").isalnum() or class_name[0].isdigit():
            messagebox.showwarning(
                "Advertencia",
                "El nombre de la clase debe ser un identificador válido de C++.",
            )
            return

        try:
            result = self.project_manager.add_class(class_name)
            if result:
                header_path, source_path = result
                self.file_explorer.refresh()
                self.open_file_path(header_path)
                self.open_file_path(source_path)
                self.update_status(f"Clase '{class_name}' creada")
                self.console.success(f"✓ Clase '{class_name}' creada:\n  {header_path}\n  {source_path}\n")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la clase:\n{e}")

    # --- Sincronización con GitHub ---

    def configure_github(self):
        """Abre el diálogo para configurar el token y el repositorio."""

        def on_saved(cfg):
            alias = f"@{cfg['owner']} / {cfg['repo']}"
            self.update_status(f"GitHub configurado: {alias}")
            self.console.success(
                f"✓ GitHub configurado: {alias}\n"
                f"  Repositorio {'privado' if cfg['private'] else 'público'}.\n"
            )

        GitHubCredentialsDialog(self, self.github, on_saved=on_saved)

    def _github_requires_project(self):
        """Muestra un aviso y devuelve False si no hay proyecto abierto."""
        if not self.project_manager.has_project():
            messagebox.showinfo(
                "Sin proyecto",
                "Primero crea o abre un proyecto para poder publicarlo "
                "o sincronizarlo con GitHub.",
            )
            return False
        return True

    def _github_credentials(self):
        """Devuelve (token, owner, repo) si están configurados; si no, None.

        Abre el diálogo de configuración cuando faltan credenciales.
        """
        cfg = self.github.load_config()
        token = cfg.get("token", "")
        owner = cfg.get("owner", "")
        repo = cfg.get("repo", "")
        if not token or not owner or not repo:
            messagebox.showinfo(
                "Configuración pendiente",
                "Primero debes configurar tu token y el repositorio "
                "de GitHub.",
            )
            self.configure_github()
            return None
        return token, owner, repo

    def _run_github(self, target, action):
        """Ejecuta una operación de GitHub en un hilo de fondo.

        Args:
            target: Función que recibe la ruta del proyecto y devuelve
                    un resumen en texto.
            action: Descripción corta de la operación (para la UI).
        """
        if not self._github_requires_project():
            return
        project_path = self.project_manager.current_project.path

        def worker():
            try:
                result = target(project_path)
            except Exception as e:  # noqa: BLE001 - mostrar cualquier error
                err = str(e)
                self.after(0, lambda: self._github_done(False, action, err))
            else:
                self.after(0, lambda r=result: self._github_done(True, action, r))

        threading.Thread(target=worker, daemon=True).start()
        self.update_status(f"GitHub: {action} en curso…")

    def _github_done(self, ok, action, text):
        """Muestra el resultado de una operación de GitHub."""
        if ok:
            self.console.success(f"✓ GitHub ({action}):\n{text}\n")
            self.update_status(f"GitHub: {action} completado")
            try:
                self.file_explorer.refresh()
            except Exception:
                pass
            messagebox.showinfo("GitHub", f"{text}")
        else:
            self.console.error(f"✗ GitHub ({action}):\n{text}\n")
            self.update_status("GitHub: error")
            messagebox.showerror("Error de GitHub", text)

    def github_publish(self):
        """Publica el proyecto actual en GitHub (primer push)."""
        if not self._github_requires_project():
            return
        if not self.github.has_token():
            messagebox.showinfo(
                "Configura GitHub",
                "Primero configura tu Personal Access Token de GitHub.",
            )
            self.configure_github()
            return
        if not self._save_all_open_files():
            return  # El usuario canceló el guardado

        import tkinter.simpledialog as simpledialog

        project = self.project_manager.current_project
        cfg = self.github.load_config()
        token = cfg["token"]
        owner = cfg.get("owner") or simpledialog.askstring(
            "GitHub", "Dueño (usuario u organización):", parent=self,
        )
        if not owner:
            return
        repo = cfg.get("repo") or simpledialog.askstring(
            "GitHub", "Nombre del repositorio:",
            initialvalue=project.name, parent=self,
        )
        if not repo:
            return
        private = bool(cfg.get("private", False))
        message = (
            simpledialog.askstring(
                "GitHub",
                "Mensaje del commit inicial:",
                initialvalue=f"Publicar proyecto {project.name}",
                parent=self,
            )
            or f"Publicar proyecto {project.name}"
        )

        def target(path):
            return self.github.publish(
                path, token, owner, repo, private, message
            )

        self._run_github(target, "publicación")

    def github_push(self):
        """Confirma los cambios y los sube al remoto (commit + push)."""
        from tkinter import simpledialog

        if not self._save_all_open_files():
            return  # El usuario canceló el guardado

        creds = self._github_credentials()
        if not creds:
            return
        token, owner, repo = creds
        message = (
            simpledialog.askstring(
                "GitHub",
                "Mensaje del commit:",
                initialvalue="Sincronizar cambios desde MeriCode",
                parent=self,
            )
            or "Sincronizar cambios desde MeriCode"
        )

        def target(path):
            return self.github.push_changes(path, token, owner, repo, message)

        self._run_github(target, "push")

    def github_pull(self):
        """Descarga los cambios remotos al proyecto local (pull)."""
        creds = self._github_credentials()
        if not creds:
            return
        token, owner, repo = creds

        def target(path):
            return self.github.sync_pull(path, token, owner, repo)

        self._run_github(target, "pull")

    def github_status(self):
        """Muestra el estado del repositorio git del proyecto."""
        if not self._github_requires_project():
            return
        project_path = self.project_manager.current_project.path
        try:
            info = self.github.status(project_path)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Error de GitHub", str(e))
            return
        self.console.info(f"--- Estado del repositorio ---\n{info}\n")
        self.update_status("Estado del repositorio obtenido")
        messagebox.showinfo("Estado del repositorio", info)

    def github_clone(self):
        """Clona un proyecto de GitHub en el equipo y lo abre en el IDE."""
        cfg = self.github.load_config()
        token = cfg.get("token", "")
        if not token:
            response = messagebox.askyesno(
                "GitHub",
                "No hay un token configurado. Podrás clonar repositorios\n"
                "públicos sin token, pero los privados requieren uno.\n\n"
                "¿Quieres continuar sin token?\n"
                "Elige 'No' para configurar el token.",
            )
            if response is None:
                return
            if not response:
                self.configure_github()
                return

        import tkinter.simpledialog as simpledialog

        owner = simpledialog.askstring(
            "GitHub",
            "Dueño (usuario u organización):",
            initialvalue=cfg.get("owner", ""),
            parent=self,
        )
        if not owner:
            return
        repo = simpledialog.askstring(
            "GitHub",
            "Nombre del repositorio:",
            initialvalue=cfg.get("repo", ""),
            parent=self,
        )
        if not repo:
            return

        dest_dir = filedialog.askdirectory(
            parent=self,
            title="Seleccione la carpeta donde clonar el proyecto",
        )
        if not dest_dir:
            return

        target_name = simpledialog.askstring(
            "GitHub",
            "Nombre de la carpeta local\n"
            "(vacío para usar el nombre del repositorio):",
            initialvalue=repo,
            parent=self,
        )
        target_name = (target_name or "").strip() or repo

        def worker():
            try:
                clone_dir = self.github.clone(
                    dest_dir, token, owner, repo, target_name
                )
            except Exception as e:  # noqa: BLE001
                err = str(e)
                self.after(
                    0, lambda: self._github_clone_done(False, err)
                )
            else:
                self.after(
                    0, lambda d=clone_dir: self._github_clone_done(True, d)
                )

        threading.Thread(target=worker, daemon=True).start()
        self.update_status(f"GitHub: clonando {owner}/{repo}…")

    def _github_clone_done(self, ok, info):
        """Muestra el resultado del clonado y abre el proyecto si fue bien."""
        if not ok:
            self.console.error(f"✗ GitHub (clonar):\n{info}\n")
            self.update_status("GitHub: error al clonar")
            messagebox.showerror("Error al clonar", info)
            return

        clone_dir = info
        self.console.success(f"✓ Proyecto clonado en {clone_dir}\n")
        self.update_status("GitHub: proyecto clonado")
        messagebox.showinfo("GitHub", f"Proyecto clonado en:\n{clone_dir}")

        # Abrir el proyecto clonado en el IDE.
        repo_name = os.path.basename(clone_dir)
        self._open_cloned_project(clone_dir, repo_name)

    def _open_cloned_project(self, clone_dir, repo_name):
        """Abre el proyecto clonado (usa su .cmj si existe, o crea uno).

        Args:
            clone_dir: Directorio raíz del proyecto clonado.
            repo_name: Nombre del repositorio (para el proyecto .cmj).
        """
        try:
            cmj = self._find_cmj_file(clone_dir)
            if cmj:
                project = self.project_manager.open_project(cmj)
            else:
                # Crear un proyecto .cmj dentro de la carpeta clonada.
                project = Project(name=repo_name, path=clone_dir)
                project_file = project.save()
                project.scan_files()
                self.project_manager.current_project = project
                self.project_manager.project_file = project_file

            self.file_explorer.open_directory(project.path)
            self.file_explorer.update_project_display()
            self.update_title()

            # Abrir main.cpp si existe.
            main_cpp = os.path.join(project.path, "main.cpp")
            if os.path.exists(main_cpp):
                self.open_file_path(main_cpp)

            self.console.success(
                f"✓ Proyecto '{project.name}' abierto desde GitHub\n"
            )
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(
                "Error", f"No se pudo abrir el proyecto clonado:\n{e}"
            )

    def _find_cmj_file(self, project_dir):
        """Busca un archivo .cmj dentro del directorio (evitando .git).

        Returns:
            str: Ruta del primer archivo .cmj encontrado, o None.
        """
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d != ".git"]
            for name in files:
                if name.endswith(".cmj"):
                    return os.path.join(root, name)
        return None

    # --- Gestión de archivos ---

    def _save_all_open_files(self):
        """Guarda todos los archivos abiertos que tengan modificaciones.

        Devuelve True si todos los archivos modificados se guardaron
        (o no había nada que guardar), y False si hay archivos nuevos
        sin ruta o el usuario canceló el guardado.

        Requiere que haya un editor actual activo (self.current_editor).
        """
        modified = [
            ed for ed in self.open_files.values()
            if ed.is_modified()
        ]
        if not modified:
            return True

        # Separar archivos con y sin ruta.
        with_path = [ed for ed in modified if ed.file_path]
        without_path = [ed for ed in modified if not ed.file_path]

        # Guardar los que ya tienen ruta.
        for ed in with_path:
            old = self.current_editor
            self.current_editor = ed
            self._save_to_path(ed.file_path)
            self.current_editor = old

        # Los archivos nuevos (sin ruta) requieren "Guardar como".
        if without_path:
            messagebox.showinfo(
                "Archivos nuevos sin guardar",
                "Hay archivos abiertos sin nombre que no se pueden "
                "guardar automáticamente. Se abrirá el diálogo 'Guardar "
                "como' para cada uno antes de sincronizar.",
            )
            for ed in without_path:
                old = self.current_editor
                self.current_editor = ed
                self.save_file_as()
                self.current_editor = old
                # Si tras "Guardar como" siguió sin ruta, el usuario canceló.
                if not ed.file_path:
                    messagebox.showinfo(
                        "Sincronización cancelada",
                        "Guardado cancelado. La sincronización con "
                        "GitHub se detuvo y los cambios no se subieron.",
                    )
                    return False

        # Verificar que no quede nada sin guardar.
        remaining = [ed for ed in self.open_files.values() if ed.is_modified()]
        if remaining:
            messagebox.showinfo(
                "Sincronización cancelada",
                "Algunos archivos no se pudieron guardar. La "
                "sincronización con GitHub se detuvo.",
            )
            return False

        self.update_status("Archivos guardados antes de sincronizar")
        return True

    def new_file(self, content=None, add_to_project=False):
        """Crea un nuevo archivo.

        Si no se especifica contenido y se crea un archivo .cpp,
        se genera automáticamente un programa "Hola mundo" funcional
        (a menos que forme parte de un proyecto, donde se usa el
        template del proyecto).

        Cuando add_to_project es True y hay un proyecto abierto,
        el archivo se crea dentro del directorio del proyecto y se
        registra en la lista de archivos del proyecto (.cmj).

        Args:
            content: Contenido inicial opcional para el editor.
            add_to_project: Si True, al crear el archivo con un
                proyecto abierto se agrega automáticamente al proyecto.

        Returns:
            CodeEditor: El editor creado (o None si el usuario canceló
            la creación en el proyecto).
        """
        # Al crear un archivo nuevo con un proyecto abierto, agregarlo
        # directamente al proyecto (crearlo en su directorio).
        if add_to_project and self.project_manager.has_project():
            return self._new_project_file()

        file_id = self.next_file_id
        self.next_file_id += 1

        editor = CodeEditor(self.notebook, self)
        tab_title = f"sin_título_{file_id}.cpp"

        if content:
            # Usar el contenido proporcionado
            editor.set_content(content)
        else:
            # Si no hay contenido y no hay un proyecto abierto,
            # crear un archivo .cpp con el formato de "Hola mundo" funcional
            if not self.project_manager.has_project():
                # Plantilla de programa C++ básico con "Hola mundo"
                hola_mundo = (
                    '#include <iostream>\n'
                    '\n'
                    'using namespace std;\n'
                    '\n'
                    'int main() {\n'
                    '    cout << "Hola, mundo!" << endl;\n'
                    '    return 0;\n'
                    '}\n'
                )
                editor.set_content(hola_mundo)

        self.notebook.add(editor, text=tab_title)
        self.notebook.select(editor)
        self.open_files[file_id] = editor
        self.current_editor = editor

        self.update_title()
        self.update_cursor_position()
        self.file_explorer.refresh_open_files()
        return editor

    def _new_project_file(self):
        """Crea un archivo nuevo dentro del directorio del proyecto activo.

        Pide el nombre del archivo (con un nombre sugerido único) y lo
        crea en el directorio del proyecto, registrándolo en la lista de
        archivos del proyecto (.cmj).

        Returns:
            CodeEditor: El editor con el archivo creado, o None si el
            usuario cancela o el nombre no es válido.
        """
        project = self.project_manager.current_project
        import tkinter.simpledialog as simpledialog

        name = self._suggest_new_filename(project.path)
        file_name = simpledialog.askstring(
            "Nuevo archivo en el proyecto",
            f"Nombre del archivo nuevo\n"
            f"Se creará dentro de: {project.name}\n"
            f"(ejemplo: nuevo_archivo.cpp)",
            initialvalue=name,
            parent=self,
        )
        if not file_name:
            return None
        file_name = file_name.strip()
        if not file_name:
            messagebox.showwarning(
                "Advertencia", "El nombre del archivo no puede estar vacío."
            )
            return None

        # Asegurar la extensión por defecto si no tiene ninguna.
        if not os.path.splitext(file_name)[1]:
            file_name += ".cpp"

        file_path = os.path.abspath(os.path.join(project.path, file_name))

        # Evitar que la ruta se salga del directorio del proyecto.
        project_dir = os.path.abspath(project.path)
        try:
            inside = os.path.commonpath([project_dir, file_path]) == project_dir
        except ValueError:
            inside = False
        if not inside:
            messagebox.showwarning(
                "Advertencia",
                "El archivo debe ubicarse dentro del directorio del proyecto.",
            )
            return None

        if os.path.exists(file_path):
            messagebox.showwarning(
                "Advertencia", f"El archivo '{file_path}' ya existe."
            )
            return None

        # Crear el archivo en disco (vacío).
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("")
        except OSError as e:
            messagebox.showerror(
                "Error", f"No se pudo crear el archivo:\n{e}"
            )
            return None

        # Abrirlo en una pestaña del editor.
        editor = self.new_file("")
        editor.file_path = file_path
        editor.set_modified(False)
        self.notebook.tab(editor, text=os.path.basename(file_path))
        self.update_title()

        # Registrar el archivo en el proyecto (lista .cmj).
        self._register_file_in_project(file_path, notify=True)
        return editor

    def _suggest_new_filename(self, project_dir):
        """Devuelve un nombre de archivo .cpp único en el directorio.

        Args:
            project_dir: Directorio del proyecto.

        Returns:
            str: Nombre como 'nuevo_archivo.cpp' (o _1, _2... si ya
            existe).
        """
        base = "nuevo_archivo"
        name = f"{base}.cpp"
        counter = 1
        while os.path.exists(os.path.join(project_dir, name)):
            name = f"{base}_{counter}.cpp"
            counter += 1
        return name

    def _register_file_in_project(self, file_path, notify=False):
        """Registra un archivo en el proyecto activo si aún no está.

        Si el archivo pertenece al directorio del proyecto abierto y no
        figura en su lista de archivos, lo agrega (reescanea el directorio
        y guarda el .cmj).

        Args:
            file_path: Ruta del archivo creado o guardado.
            notify: True para informar en consola y barra de estado.

        Returns:
            bool: True si el archivo fue agregado al proyecto.
        """
        if not self.project_manager.has_project():
            return False

        project = self.project_manager.current_project
        project_dir = os.path.abspath(project.path)
        abs_path = os.path.abspath(file_path)

        # Debe estar dentro del directorio del proyecto.
        try:
            inside = os.path.commonpath([project_dir, abs_path]) == project_dir
        except ValueError:
            inside = False
        if not inside:
            return False

        # Si ya está registrado, no hay nada que hacer.
        known = {os.path.abspath(f) for f in project.files}
        if abs_path in known:
            return False

        project.scan_files()
        self.project_manager.save_project()
        self.file_explorer.refresh()

        if notify:
            self.update_status(f"Archivo agregado al proyecto: {abs_path}")
            self.console.success(
                f"✓ Archivo agregado al proyecto: {abs_path}\n"
            )
        return True

    def open_file(self):
        """Abre un archivo mediante diálogo."""
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Abrir archivo",
            filetypes=[
                ("Archivos C++", "*.cpp *.cc *.cxx *.hpp *.h *.cxx"),
                ("Archivos C", "*.c"),
                ("Archivos de cabecera", "*.h *.hpp"),
                ("Proyectos", "*.cmj"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if file_path:
            if file_path.endswith(".cmj"):
                self.project_manager.open_project(file_path)
                self.file_explorer.open_directory(os.path.dirname(file_path))
                self.file_explorer.update_project_display()
            else:
                self.open_file_path(file_path)

    def open_file_path(self, file_path):
        """Abre un archivo existente."""
        # Verificar si ya está abierto
        for file_id, editor in self.open_files.items():
            if editor.file_path and os.path.abspath(editor.file_path) == os.path.abspath(file_path):
                self.notebook.select(editor)
                self.current_editor = editor
                return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")
                return
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")
            return

        editor = self.new_file(content)
        editor.file_path = os.path.abspath(file_path)
        editor.set_modified(False)
        self.notebook.tab(editor, text=os.path.basename(file_path))
        self.update_title()
        self.update_status(f"Abierto: {file_path}")
        self.file_explorer.refresh_open_files()

    def save_file(self):
        """Guarda el archivo actual."""
        if not self.current_editor:
            return

        # Si es el editor UML, guardar como XML
        if hasattr(self, "uml_editor") and self.current_editor == self.uml_editor:
            self.save_uml_xml()
            return

        if self.current_editor.file_path:
            self._save_to_path(self.current_editor.file_path)
        else:
            self.save_file_as()

    def save_editor(self, editor):
        """Guarda un editor específico."""
        if not editor:
            return

        old_editor = self.current_editor
        self.current_editor = editor
        self.save_file()
        self.current_editor = old_editor

    def save_file_as(self):
        """Guarda el archivo actual con un nombre nuevo."""
        if not self.current_editor:
            return

        # Si es el editor UML, guardar como XML
        if hasattr(self, "uml_editor") and self.current_editor == self.uml_editor:
            self.save_uml_xml()
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar como",
            defaultextension=".cpp",
            filetypes=[
                ("Archivos C++", "*.cpp"),
                ("Archivos de cabecera", "*.h"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if file_path:
            self.current_editor.file_path = os.path.abspath(file_path)
            self._save_to_path(self.current_editor.file_path)
            self.notebook.tab(self.current_editor, text=os.path.basename(file_path))
            self.update_title()
            self.file_explorer.refresh_open_files()

    def _save_to_path(self, file_path):
        """Guarda el contenido del editor en una ruta."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.current_editor.get_content())
            self.current_editor.set_modified(False)
            self.update_status(f"Guardado: {file_path}")
            self.file_explorer.refresh_open_files()
            # Si el archivo pertenece a un proyecto abierto y aún no
            # estaba registrado (p. ej. un archivo sin título guardado
            # con "Guardar como"), agregarlo al proyecto.
            self._register_file_in_project(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{e}")

    def close_editor(self, editor, create_new_if_empty=True):
        """Cierra un editor específico.

        Args:
            editor: El editor (pestaña) a cerrar.
            create_new_if_empty: Si es True (predeterminado), crea un
                archivo nuevo automáticamente cuando se cierra la última
                pestaña. Si es False (usado por "Cerrar todos"), NO crea
                ninguna pestaña nueva, para poder cerrar todas de una vez.

        Returns:
            bool: True si el editor se cerró correctamente,
                  False si el usuario canceló el cierre o el editor no existe.
        """
        if not editor:
            return False

        # Si es el editor UML, cerrar sin verificar modificación
        if hasattr(self, "uml_editor") and editor == self.uml_editor:
            self.notebook.forget(editor)
            editor.destroy()
            self.uml_editor = None
            # Actualizar editor actual
            if self.notebook.tabs():
                current_tab = self.notebook.select()
                for ed in self.open_files.values():
                    if str(ed) == current_tab:
                        self.current_editor = ed
                        break
            else:
                self.current_editor = None
                if create_new_if_empty:
                    self.new_file()
            self.update_title()
            self.update_cursor_position()
            self.file_explorer.refresh_open_files()
            return True

        if editor.is_modified():
            result = messagebox.askyesnocancel(
                "Archivo sin guardar",
                "¿Desea guardar los cambios antes de cerrar?",
            )
            if result is None:
                return False  # El usuario canceló la operación
            if result:
                old_editor = self.current_editor
                self.current_editor = editor
                self.save_file()
                self.current_editor = old_editor
                if editor.is_modified():
                    return False  # No se pudo guardar, no cerrar

        self.notebook.forget(editor)
        editor.destroy()

        # Limpiar referencias
        to_remove = None
        for file_id, ed in self.open_files.items():
            if ed == editor:
                to_remove = file_id
                break
        if to_remove is not None:
            del self.open_files[to_remove]

        # Actualizar editor actual
        if self.notebook.tabs():
            current_tab = self.notebook.select()
            for ed in self.open_files.values():
                if str(ed) == current_tab:
                    self.current_editor = ed
                    break
        else:
            self.current_editor = None
            # Solo crear una pestaña nueva si estamos cerrando directamente
            # (no dentro de "Cerrar todos")
            if create_new_if_empty:
                self.new_file()

        self.update_title()
        self.update_cursor_position()
        self.file_explorer.refresh_open_files()
        return True

    def close_current_tab(self):
        """Cierra la pestaña actual."""
        if not self.current_editor:
            return
        self.close_editor(self.current_editor)

    def close_all_tabs(self):
        """Cierra todas las pestañas que el IDE tiene abiertas.

        Se toma una copia de los archivos abiertos ANTES de empezar
        para garantizar que solo se cierren los que están abiertos en
        este momento y no se creen pestañas nuevas en el proceso.

        Si el usuario cancela el cierre de alguno con cambios sin
        guardar, se detiene la operación sin cerrar el resto.
        """
        # Copia de seguridad de los abiertos actualmente
        editors = list(self.open_files.values())

        # Cerrar cada editor sin permitir que se creen pestañas nuevas
        for editor in editors:
            if not self.close_editor(editor, create_new_if_empty=False):
                break  # El usuario canceló; no cerrar las demás

        # Si no quedó ninguna pestaña abierta, crear una vacía para
        # que el IDE siempre tenga un editor en el que trabajar
        if not self.open_files and not self.notebook.tabs():
            self.new_file()

    def _on_tab_changed(self, event=None):
        """Actualiza el editor actual al cambiar de pestaña."""
        try:
            current_tab = self.notebook.select()
            # Verificar si es el editor UML
            if hasattr(self, "uml_editor") and self.uml_editor is not None:
                try:
                    if str(self.uml_editor) == current_tab:
                        self.current_editor = self.uml_editor
                        self.update_title()
                        self.update_cursor_position()
                        self.file_explorer.refresh_open_files()
                        return
                except tk.TclError:
                    pass
            for file_id, editor in self.open_files.items():
                if str(editor) == current_tab:
                    self.current_editor = editor
                    break
            self.update_title()
            self.update_cursor_position()
            self.file_explorer.refresh_open_files()
        except tk.TclError:
            pass

    def _editor_action(self, action):
        """Ejecuta una acción de edición en el editor actual."""
        if not self.current_editor:
            return
        # Si es el editor UML, no ejecutar acciones de texto
        if hasattr(self, "uml_editor") and self.current_editor == self.uml_editor:
            return
        text = self.current_editor.text
        action_map = {
            "edit_undo": lambda: text.edit_undo(),
            "edit_redo": lambda: text.edit_redo(),
            "edit_cut": lambda: text.event_generate("<<Cut>>"),
            "edit_copy": lambda: text.event_generate("<<Copy>>"),
            "edit_paste": lambda: text.event_generate("<<Paste>>"),
            "edit_select_all": lambda: text.tag_add("sel", "1.0", "end"),
        }
        if action in action_map:
            try:
                action_map[action]()
            except tk.TclError:
                pass

    # --- Compilación / Ejecución / Depuración ---

    def compile_program(self):
        """Compila el programa actual."""
        if not self.current_editor:
            return

        if self.compiler.is_busy():
            messagebox.showwarning("Ocupado", "Ya hay un proceso en ejecución.")
            return

        if not self._ensure_saved():
            return

        source_file = self.current_editor.file_path
        self.console.clear_errors()
        self.console.show_output_tab()
        self.console.output(f"=== Compilando {os.path.basename(source_file)} ===\n")
        self.build_status_label.config(text="Compilando...")

        # Compilar con símbolos de depuración
        extra_flags = ["-g", "-Wall"]

        def on_output(line, tag):
            self._console_output(line, tag)

        def on_done(code):
            self.build_status_label.config(text="")
            if code == 0:
                self.update_status("Compilación exitosa")
            else:
                # Mostrar la consola para que el estudiante vea los errores
                self.update_status("Error de compilación")
                self.show_console()
                self.console.show_error_tab()

        self.compiler.compile_source(
            source_file,
            std=self.std_var.get(),
            extra_flags=extra_flags,
            on_output=on_output,
            on_done=on_done,
        )

    def run_program(self, args=None):
        """Ejecuta el programa actual."""
        if not self.current_editor:
            return

        if self.compiler.is_busy():
            messagebox.showwarning("Ocupado", "Ya hay un proceso en ejecución.")
            return

        # Mostrar la consola al ejecutar el programa
        self.show_console()

        if self.current_editor.file_path:
            source_file = self.current_editor.file_path
            base = os.path.splitext(source_file)[0]
            executable = base + (".exe" if os.name == "nt" else "")

            # Si no existe el ejecutable, compilar primero
            if not os.path.exists(executable):
                if not self._ensure_saved():
                    return
                self.console.clear_output()
                self.console.show_output_tab()
                self.console.output("Compilando antes de ejecutar...\n")
                self.compiler.compile_and_run(
                    source_file,
                    args=args,
                    on_output=self._console_output,
                    on_done=self._on_program_done,
                )
                return

            self.console.clear_output()
            self.console.show_output_tab()
            self.compiler.run_program(
                executable,
                args=args,
                cwd=os.path.dirname(source_file),
                on_output=self._console_output,
                on_done=self._on_program_done,
            )
        else:
            self.save_file_as()
            if self.current_editor.file_path:
                self.run_program(args)

    def compile_and_run(self):
        """Compila y ejecuta el programa."""
        if not self.current_editor:
            return

        if self.compiler.is_busy():
            messagebox.showwarning("Ocupado", "Ya hay un proceso en ejecución.")
            return

        if not self._ensure_saved():
            return

        source_file = self.current_editor.file_path
        self.console.clear_output()
        self.console.clear_errors()
        self.console.show_output_tab()
        self.console.output(f"=== Compilando y ejecutando ===\n")
        self.build_status_label.config(text="Compilando...")

        extra_flags = ["-g", "-Wall"]

        def on_output(line, tag):
            self._console_output(line, tag)

        self.compiler.compile_source(
            source_file,
            std=self.std_var.get(),
            extra_flags=extra_flags,
            on_output=on_output,
            on_done=lambda code: self._after_compile_for_run(code),
        )

    def _after_compile_for_run(self, code):
        """Continuación de compilar y ejecutar."""
        self.build_status_label.config(text="")
        if code == 0:
            if self.current_editor and self.current_editor.file_path:
                # Mostrar la consola al comenzar la ejecución
                self.show_console()
                source_file = self.current_editor.file_path
                base = os.path.splitext(source_file)[0]
                executable = base + (".exe" if os.name == "nt" else "")
                self.console.output("Ejecutando programa...\n")
                self.compiler.run_program(
                    executable,
                    cwd=os.path.dirname(source_file),
                    on_output=self._console_output,
                    on_done=self._on_program_done,
                )
        else:
            # Mostrar la consola con los errores de compilación
            self.update_status("Error de compilación")
            self.show_console()
            self.console.show_error_tab()

    def debug_program(self):
        """Depura el programa actual con GDB."""
        if not self.current_editor:
            return

        if self.compiler.is_busy():
            messagebox.showwarning("Ocupado", "Ya hay un proceso en ejecución.")
            return

        if not self._ensure_saved():
            return

        source_file = self.current_editor.file_path
        base = os.path.splitext(source_file)[0]
        executable = base + (".exe" if os.name == "nt" else "")

        # Recoger los breakpoints marcados en el editor actual
        breakpoints = (
            self.current_editor.get_breakpoints()
            if hasattr(self.current_editor, "get_breakpoints")
            else set()
        )

        # Verificar si está compilado con -g
        if not os.path.exists(executable):
            result = messagebox.askyesno(
                "Depurar",
                "El programa no está compilado. ¿Desea compilarlo con símbolos de depuración?",
            )
            if not result:
                return

            self.console.clear_debug()
            self.console.show_debug_tab()
            self.console.debug("Compilando con símbolos de depuración (-g)...\n")
            self.compiler.compile_source(
                source_file,
                std=self.std_var.get(),
                extra_flags=["-g", "-Wall", "-O0"],
                on_output=self._debug_output,
                on_done=lambda code: self._start_debug_after_compile(code, executable, breakpoints),
            )
        else:
            self._start_debug(executable, breakpoints)

    def _start_debug_after_compile(self, code, executable, breakpoints=None):
        """Inicia depuración después de compilar."""
        if code == 0:
            self._start_debug(executable, breakpoints)
        else:
            # Mostrar la consola con los errores de compilación
            self.show_console()
            self.console.show_error_tab()
            self.update_status("Error de compilación para depuración")

    def _start_debug(self, executable, breakpoints=None):
        """Inicia la sesión de depuración."""
        # Mostrar la consola al depurar
        self.show_console()
        self.console.clear_debug()
        self.console.show_debug_tab()
        self.console.debug(f"=== Sesión de depuración ===\n")
        if breakpoints:
            self.console.debug(
                "Breakpoints: " + ", ".join(str(b) for b in sorted(breakpoints)) + "\n"
            )
        self.build_status_label.config(text="Depurando...")

        def on_output(line, tag):
            self._debug_output(line, tag)

        def on_done(code):
            self.build_status_label.config(text="")

        self.compiler.debug_program(
            executable,
            self.current_editor.file_path,
            breakpoints=breakpoints,
            on_output=on_output,
            on_done=on_done,
        )

    def run_with_args(self):
        """Ejecuta el programa con argumentos."""
        import tkinter.simpledialog as simpledialog
        args_str = simpledialog.askstring(
            "Argumentos",
            "Ingrese los argumentos separados por espacios:",
            parent=self,
        )
        if args_str is not None:
            args = args_str.split() if args_str.strip() else None
            self.run_program(args)

    def stop_program(self):
        """Detiene el proceso en ejecución."""
        if self.compiler.is_busy():
            self.compiler.stop()
            self.console.output("\n⏹ Proceso detenido por el usuario.\n")
            self.update_status("Proceso detenido")

    def show_debug_settings(self):
        """Muestra la configuración del depurador."""
        info = self.compiler.get_compiler_info()
        gdb_path = subprocess.run(["which", "gdb"], capture_output=True, text=True)
        gdb_available = gdb_path.returncode == 0

        messagebox.showinfo(
            "Configuración del depurador",
            f"Compilador: {info['name'] or 'No disponible'}\n"
            f"Versión: {info['version']}\n\n"
            f"GDB: {'Disponible' if gdb_available else 'No instalado'}\n\n"
            "Para depurar necesitas:\n"
            "1. Compilar con -g (automático)\n"
            "2. GDB instalado (sudo apt install gdb)",
        )

    def _console_output(self, line, tag):
        """Escribe la salida de un proceso en la pestaña de consola adecuada."""
        if tag == "error":
            self.console.error(line)
        elif tag == "debug":
            self.console.debug(line)
        else:
            self.console.output(line)

    def _debug_output(self, line, tag):
        """Escribe la salida de depuración; los errores van a la pestaña de errores."""
        if tag == "error":
            self.console.error(line)
        else:
            self.console.debug(line)

    def _on_program_done(self, code):
        """Maneja la finalización del programa."""
        self.build_status_label.config(text="")
        self.update_status(f"Proceso terminado con código {code}")

    def _ensure_saved(self):
        """Asegura que el archivo actual esté guardado."""
        if not self.current_editor:
            return False
        # Si es el editor UML, no necesita guardar
        if hasattr(self, "uml_editor") and self.current_editor == self.uml_editor:
            return True
        if not self.current_editor.file_path:
            self.save_file_as()
            return self.current_editor.file_path is not None
        if self.current_editor.is_modified():
            result = messagebox.askyesnocancel(
                "Archivo sin guardar",
                "Hay cambios sin guardar. ¿Desea guardar antes de continuar?",
            )
            if result is None:
                return False
            if result:
                self.save_file()
            # Si el usuario elige "No", continuar sin guardar
        return True

    # --- Utilidades de editor ---

    def show_search(self):
        """Muestra el diálogo de búsqueda."""
        if not self.current_editor:
            return
        # Si es el editor UML, no mostrar búsqueda
        if hasattr(self, "uml_editor") and self.current_editor == self.uml_editor:
            return
        self.search_dialog = SearchDialog(self, self.current_editor.text)

    def show_replace(self):
        """Muestra el diálogo de búsqueda y reemplazo."""
        if not self.current_editor:
            return
        # Si es el editor UML, no mostrar búsqueda
        if hasattr(self, "uml_editor") and self.current_editor == self.uml_editor:
            return
        self.search_dialog = SearchDialog(self, self.current_editor.text)

    def go_to_line(self):
        """Va a una línea específica."""
        import tkinter.simpledialog as simpledialog
        if not self.current_editor:
            return
        # Si es el editor UML, no ir a línea
        if hasattr(self, "uml_editor") and self.current_editor == self.uml_editor:
            return

        line = simpledialog.askinteger(
            "Ir a línea",
            "Número de línea:",
            parent=self,
            minvalue=1,
        )
        if line:
            self.current_editor.text.mark_set("insert", f"{line}.0")
            self.current_editor.text.see(f"{line}.0")
            self.update_cursor_position()

    def change_font_size(self, delta):
        """Cambia el tamaño de la fuente del editor."""
        if not self.current_editor:
            return
        # Si es el editor UML, no cambiar fuente
        if hasattr(self, "uml_editor") and self.current_editor == self.uml_editor:
            return
        size = self.current_editor.editor_font.cget("size")
        new_size = max(8, min(24, size + delta))
        self.current_editor.editor_font.configure(size=new_size)
        self.current_editor.line_numbers._font.configure(size=new_size)

    def reset_font_size(self):
        """Restablece el tamaño de fuente."""
        if not self.current_editor:
            return
        # Si es el editor UML, no cambiar fuente
        if hasattr(self, "uml_editor") and self.current_editor == self.uml_editor:
            return
        self.current_editor.editor_font.configure(size=11)
        self.current_editor.line_numbers._font.configure(size=11)

    def hide_panel(self):
        """Oculta paneles al presionar Escape."""
        # Cerrar diálogo de búsqueda si está abierto
        if self.search_dialog and self.search_dialog.winfo_exists():
            self.search_dialog.destroy()
            self.search_dialog = None

    def update_title(self):
        """Actualiza el título de la ventana."""
        title = "MeriCode C++"
        if self.project_manager.has_project():
            title = f"{self.project_manager.current_project.name} - {title}"
        if self.current_editor:
            tab_title = self.notebook.tab(self.current_editor, "text")
            title = f"{tab_title} - {title}"
            # Solo verificar modificación si es un editor de código
            if hasattr(self.current_editor, "is_modified"):
                try:
                    if self.current_editor.is_modified():
                        title = f"• {title}"
                except (AttributeError, tk.TclError):
                    pass
        self.title(title)

    def update_status(self, message):
        """Actualiza el mensaje de estado."""
        self.status_label.config(text=message)
        # Auto limpiar después de 5 segundos
        self.after(5000, lambda: self.status_label.config(text="Listo"))

    def update_cursor_position(self):
        """Actualiza la posición del cursor en la barra de estado."""
        if not self.current_editor:
            return
        # Si es el editor UML, no actualizar posición de cursor
        if hasattr(self, "uml_editor") and self.current_editor == self.uml_editor:
            return
        try:
            pos = self.current_editor.text.index("insert")
            line, col = pos.split(".")
            self.cursor_label.config(text=f"Línea {line}, Columna {int(col) + 1}")
        except tk.TclError:
            pass

    def _check_compiler_status(self):
        """Verifica y muestra el estado del compilador."""
        info = self.compiler.get_compiler_info()
        if info["available"]:
            self.compiler_label.config(
                text=f"⚙ {info['name']} {info['version'].split()[-1] if info['version'] else ''}"
            )
        else:
            self.compiler_label.config(text="⚠ Sin compilador C++")
            self.console.warning(
                "⚠ No se encontró un compilador C++. Instale g++ o clang++.\n"
                "  En Ubuntu/Debian: sudo apt install g++\n"
                "  En Fedora: sudo dnf install gcc-c++\n"
            )

    # --- Editor UML ---

    def open_uml_editor(self):
        """Abre el editor de diagramas UML."""
        # Verificar si ya hay un editor UML abierto
        if hasattr(self, "uml_editor") and self.uml_editor is not None:
            try:
                if self.uml_editor.winfo_exists():
                    self.notebook.select(self.uml_editor)
                    self.current_editor = self.uml_editor
                    return
            except tk.TclError:
                pass

        # Crear nuevo editor UML
        self.uml_editor = UMLEditor(self.notebook, self)
        self.notebook.add(self.uml_editor, text="📐 Diagrama UML")
        self.notebook.select(self.uml_editor)
        self.current_editor = self.uml_editor
        self.update_status("Editor UML abierto")

    def save_uml_xml(self):
        """Guarda el diagrama UML actual en XML."""
        if not hasattr(self, "uml_editor") or self.uml_editor is None:
            messagebox.showinfo("UML", "Primero abra el editor UML.")
            return
        try:
            if self.uml_editor.winfo_exists():
                self.uml_editor.save_xml()
        except tk.TclError:
            messagebox.showinfo("UML", "Primero abra el editor UML.")

    def open_uml_xml(self):
        """Abre un diagrama UML desde XML."""
        if not hasattr(self, "uml_editor") or self.uml_editor is None:
            self.open_uml_editor()
        try:
            if self.uml_editor.winfo_exists():
                self.uml_editor.open_xml()
        except tk.TclError:
            self.open_uml_editor()
            self.uml_editor.open_xml()

    def export_uml_pdf(self):
        """Exporta el diagrama UML a PDF."""
        if not hasattr(self, "uml_editor") or self.uml_editor is None:
            messagebox.showinfo("UML", "Primero abra el editor UML.")
            return
        try:
            if self.uml_editor.winfo_exists():
                self.uml_editor.export_pdf()
        except tk.TclError:
            messagebox.showinfo("UML", "Primero abra el editor UML.")

    def export_uml_png(self):
        """Exporta el diagrama UML a PNG."""
        if not hasattr(self, "uml_editor") or self.uml_editor is None:
            messagebox.showinfo("UML", "Primero abra el editor UML.")
            return
        try:
            if self.uml_editor.winfo_exists():
                self.uml_editor.export_png()
        except tk.TclError:
            messagebox.showinfo("UML", "Primero abra el editor UML.")

    def show_about(self):
        """Muestra información sobre el IDE."""
        messagebox.showinfo(
            "Acerca de MeriCode C++",
            "MeriCode C++ v2.0\n\n"
            "Un IDE completo para programar en C++\n"
            "desarrollado en Python con Tkinter.\n\n"
            "Autor: MSc. Cristopher Montero Jiménez\n"
            "© 2026 MERIMAD. Todos los derechos reservados.\n\n"
            "Características:\n"
            "• Editor con resaltado de sintaxis\n"
            "• Números de línea y autocompletado\n"
            "• Compilación con g++/clang++\n"
            "• Ejecución de programas\n"
            "• Depuración con GDB\n"
            "• Explorador de archivos\n"
            "• Archivos abiertos visibles\n"
            "• Proyectos .cmj\n"
            "• Creación de clases .h y .cpp\n"
            "• Temas claro y oscuro\n"
            "• Buscar y reemplazar\n"
            "• Editor de diagramas UML\n"
            "• Exportar UML a PDF y PNG",
        )

    def show_shortcuts(self):
        """Muestra los atajos de teclado."""
        messagebox.showinfo(
            "Atajos de teclado",
            "Atajos de teclado:\n\n"
            "• Ctrl+N: Nuevo archivo\n"
            "• Ctrl+O: Abrir archivo\n"
            "• Ctrl+S: Guardar\n"
            "• Ctrl+Shift+S: Guardar como\n"
            "• Ctrl+F: Buscar\n"
            "• Ctrl+H: Buscar y reemplazar\n"
            "• Ctrl+G: Ir a línea\n"
            "• Ctrl+Z: Deshacer\n"
            "• Ctrl+Y: Rehacer\n"
            "• Ctrl+T: Alternar tema\n"
            "• F5: Ejecutar\n"
            "• F6: Compilar y ejecutar\n"
            "• F7: Compilar\n"
            "• Shift+F5: Detener\n"
            "• Ctrl++ / Ctrl+-: Zoom\n"
            "• UML: Editor de diagramas de clases",
        )

    def _on_close(self):
        """Maneja el cierre de la ventana."""
        # Detener procesos en ejecución
        if self.compiler.is_busy():
            self.compiler.stop()

        # Verificar archivos sin guardar
        unsaved = [ed for ed in self.open_files.values() if ed.is_modified()]
        if unsaved:
            result = messagebox.askyesnocancel(
                "Salir",
                f"Hay {len(unsaved)} archivos sin guardar. ¿Desea guardarlos antes de salir?",
            )
            if result is None:
                return
            if result:
                for ed in unsaved:
                    self.current_editor = ed
                    self.save_file()

        self.destroy()


def run():
    """Inicia la aplicación."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    run()
