"""
Resaltador de sintaxis para C++ usando Tkinter Text widget.

Este módulo aplica colores a las palabras clave, tipos, cadenas,
comentarios, números, directivas de preprocesador, funciones,
operadores y corchetes del código C++ en el editor.
"""

import tkinter as tk
import re

from .theme import ThemeManager


class SyntaxHighlighter:
    """Aplica resaltado de sintaxis C++ a un widget Text de Tkinter.

    El resaltador utiliza expresiones regulares para identificar
    los diferentes elementos del lenguaje C++ y les aplica etiquetas
    (tags) de color configuradas según el tema activo.
    """

    # Palabras clave de C++ (incluye C++11, C++14, C++17 y C++20)
    KEYWORDS = {
        "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand",
        "bitor", "bool", "break", "case", "catch", "char", "char8_t",
        "char16_t", "char32_t", "class", "compl", "concept", "const",
        "consteval", "constexpr", "constinit", "const_cast", "continue",
        "co_await", "co_return", "co_yield", "decltype", "default",
        "delete", "do", "double", "dynamic_cast", "else", "enum", "explicit",
        "export", "extern", "false", "float", "for", "friend", "goto", "if",
        "inline", "int", "long", "mutable", "namespace", "new", "noexcept",
        "not", "not_eq", "nullptr", "operator", "or", "or_eq", "private",
        "protected", "public", "register", "reinterpret_cast", "requires",
        "return", "short", "signed", "sizeof", "static", "static_assert",
        "static_cast", "struct", "switch", "template", "this", "thread_local",
        "throw", "true", "try", "typedef", "typeid", "typename", "union",
        "unsigned", "using", "virtual", "void", "volatile", "wchar_t",
        "while", "xor", "xor_eq",
    }

    # Tipos de datos comunes de C++ y la STL
    TYPES = {
        "int", "float", "double", "char", "bool", "void", "long", "short",
        "unsigned", "signed", "string", "vector", "map", "set", "list",
        "array", "auto", "size_t", "uint8_t", "uint16_t", "uint32_t",
        "uint64_t", "int8_t", "int16_t", "int32_t", "int64_t", "ostream",
        "istream", "fstream", "ifstream", "ofstream", "stringstream",
        "unique_ptr", "shared_ptr", "weak_ptr", "function", "pair", "tuple",
        "optional", "variant", "any", "initializer_list", "iterator",
        "const_iterator", "reverse_iterator", "stack", "queue",
        "deque", "priority_queue", "unordered_map", "unordered_set",
        "multimap", "multiset", "bitset", "complex", "valarray",
    }

    # Directivas de preprocesador de C++
    PREPROCESSOR = {
        "#include", "#define", "#undef", "#ifdef", "#ifndef", "#if",
        "#else", "#elif", "#endif", "#pragma", "#error", "#line",
        "#import", "#using",
    }

    # Elementos del sistema (espacios de nombres, streams, constantes)
    NAMESPACES = {
        "std", "cout", "cin", "cerr", "clog", "endl", "flush", "boolalpha",
        "noboolalpha", "hex", "dec", "oct", "fixed", "scientific",
        "true", "false", "nullptr", "NULL", "EXIT_SUCCESS", "EXIT_FAILURE",
        "string_view", "max_size", "size_type", "nullopt", "npos",
    }

    # Colores del tema (por defecto oscuro estilo VS Code)
    COLORS = {
        "background": "#1e1e1e",     # Fondo del editor
        "foreground": "#d4d4d4",     # Texto normal
        "keyword": "#569cd6",        # Palabras clave
        "type": "#4ec9b0",           # Tipos de datos
        "string": "#ce9178",         # Cadenas de texto
        "comment": "#6a9955",        # Comentarios
        "number": "#b5cea8",         # Números
        "preprocessor": "#c586c0",   # Directivas de preprocesador
        "function": "#dcdcaa",       # Llamadas a funciones
        "line_number": "#858585",    # Números de línea
        "line_number_bg": "#252526", # Fondo de números de línea
        "current_line": "#2a2d2e",   # Línea actual
        "selection": "#264f78",      # Selección de texto
        "operator": "#d4d4d4",       # Operadores
        "bracket": "#ffd700",        # Corchetes y paréntesis
    }

    def __init__(self, text_widget, theme_manager=None):
        """
        Inicializa el resaltador de sintaxis.

        Args:
            text_widget: Widget Text de Tkinter al que aplicar el resaltado.
            theme_manager: Gestor de temas (opcional).
        """
        self.text = text_widget
        self.theme_manager = theme_manager or ThemeManager()
        self._setup_tags()
        self._setup_bindings()

    def apply_theme(self):
        """Reaplica los colores del tema actual al resaltado."""
        self._setup_tags()
        self.highlight()

    def _setup_tags(self):
        """Configura las etiquetas (tags) de color para el resaltado."""
        c = self.theme_manager.get_colors()
        self.text.tag_configure("keyword", foreground=c["keyword"])
        self.text.tag_configure("type", foreground=c["type"])
        self.text.tag_configure("namespace", foreground=c["namespace"])
        self.text.tag_configure("string", foreground=c["string"])
        self.text.tag_configure("comment", foreground=c["comment"])
        self.text.tag_configure("number", foreground=c["number"])
        self.text.tag_configure("preprocessor", foreground=c["preprocessor"])
        self.text.tag_configure("function", foreground=c["function"])
        self.text.tag_configure("operator", foreground=c["operator"])
        self.text.tag_configure("bracket", foreground=c["bracket"])

    def _setup_bindings(self):
        """Configura los eventos para el resaltado en tiempo real."""
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<<Modified>>", self._on_modified)

    def _on_key_release(self, event=None):
        """Maneja el evento de liberación de tecla para re-resaltar."""
        self.highlight()

    def _on_modified(self, event=None):
        """Maneja el evento de modificación del texto para re-resaltar."""
        if self.text.edit_modified():
            self.highlight()
            self.text.edit_modified(False)

    def highlight(self):
        """Aplica el resaltado de sintaxis a todo el documento."""
        # Limpiar todas las etiquetas existentes
        self.text.tag_remove("keyword", "1.0", "end")
        self.text.tag_remove("type", "1.0", "end")
        self.text.tag_remove("namespace", "1.0", "end")
        self.text.tag_remove("string", "1.0", "end")
        self.text.tag_remove("comment", "1.0", "end")
        self.text.tag_remove("number", "1.0", "end")
        self.text.tag_remove("preprocessor", "1.0", "end")
        self.text.tag_remove("function", "1.0", "end")
        self.text.tag_remove("operator", "1.0", "end")
        self.text.tag_remove("bracket", "1.0", "end")

        # Obtener el contenido completo del editor
        content = self.text.get("1.0", "end-1c")
        if not content:
            return

        # Aplicar cada tipo de resaltado en orden
        self._highlight_comments(content)
        self._highlight_strings(content)
        self._highlight_preprocessor(content)
        self._highlight_keywords(content)
        self._highlight_types(content)
        self._highlight_namespaces(content)
        self._highlight_numbers(content)
        self._highlight_functions(content)
        self._highlight_operators(content)
        self._highlight_brackets(content)

    def _highlight_comments(self, content):
        """Resalta comentarios de línea (//) y de bloque (/* ... */)."""
        # Comentarios de bloque /* ... */
        pattern = r"/\*.*?\*/"
        for match in re.finditer(pattern, content, re.DOTALL):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("comment", start, end)

        # Comentarios de línea //
        pattern = r"//[^\n]*"
        for match in re.finditer(pattern, content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("comment", start, end)

    def _highlight_strings(self, content):
        """Resalta cadenas de texto con comillas dobles y simples."""
        # Cadenas con comillas dobles
        pattern = r'"(?:\\.|[^"\\])*"'
        for match in re.finditer(pattern, content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("string", start, end)

        # Caracteres con comillas simples
        pattern = r"'(?:\\.|[^'\\])*'"
        for match in re.finditer(pattern, content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("string", start, end)

    def _highlight_preprocessor(self, content):
        """Resalta directivas de preprocesador (#include, #define, etc.)."""
        pattern = r"^\s*(#\w+)"
        for match in re.finditer(pattern, content, re.MULTILINE):
            start = f"1.0+{match.start(1)}c"
            end = f"1.0+{match.end(1)}c"
            self.text.tag_add("preprocessor", start, end)

    def _highlight_keywords(self, content):
        """Resalta palabras clave de C++."""
        pattern = r"\b(" + "|".join(re.escape(k) for k in self.KEYWORDS) + r")\b"
        for match in re.finditer(pattern, content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("keyword", start, end)

    def _highlight_types(self, content):
        """Resalta tipos de datos de C++ y la STL."""
        pattern = r"\b(" + "|".join(re.escape(t) for t in self.TYPES) + r")\b"
        for match in re.finditer(pattern, content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("type", start, end)

    def _highlight_namespaces(self, content):
        """Resalta elementos del sistema (std, cout, cin, endl, etc.)."""
        pattern = r"\b(" + "|".join(re.escape(n) for n in self.NAMESPACES) + r")\b"
        for match in re.finditer(pattern, content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("namespace", start, end)

    def _highlight_numbers(self, content):
        """Resalta números (decimales, hexadecimales y con sufijos)."""
        pattern = r"\b(0x[0-9a-fA-F]+|\d+\.?\d*[fFlLuU]*)\b"
        for match in re.finditer(pattern, content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("number", start, end)

    def _highlight_functions(self, content):
        """Resalta llamadas a funciones (identificador seguido de paréntesis)."""
        pattern = r"\b([a-zA-Z_]\w*)\s*(?=\()"
        for match in re.finditer(pattern, content):
            start = f"1.0+{match.start(1)}c"
            end = f"1.0+{match.end(1)}c"
            self.text.tag_add("function", start, end)

    def _highlight_operators(self, content):
        """Resalta operadores compuestos de C++."""
        pattern = r"(==|!=|<=|>=|&&|\|\||<<|>>|\+\+|--|->|::|\+=|-=|\*=|/=|%=|&=|\|=|\^=)"
        for match in re.finditer(pattern, content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("operator", start, end)

    def _highlight_brackets(self, content):
        """Resalta corchetes, llaves y paréntesis."""
        pattern = r"[{}()\[\]]"
        for match in re.finditer(pattern, content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add("bracket", start, end)