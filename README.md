# 🚀 MeriCode C++

Un IDE completo para programar en C++ desarrollado en **Python** con **Tkinter**, con interfaz gráfica moderna en tema oscuro.

**Autor:** MSc. Cristopher Montero Jiménez  
**© 2026 MERIMAD. Todos los derechos reservados.**

## ✨ Características

### Editor de código
- 📝 Editor de texto con **resaltado de sintaxis C++** (palabras clave, tipos, cadenas, comentarios, números, preprocesador, funciones, operadores)
- 🔢 **Números de línea** sincronizados con el editor
- ⌨️ **Autocompletado** de llaves `{}`, paréntesis `()`, corchetes `[]` y comillas
- 📐 **Indentación automática** y uso de 4 espacios para tabulación
- 🖱️ **Resaltado de la línea actual**
- 📑 **Múltiples pestañas** para abrir varios archivos
- ↩️ **Deshacer/Rehacer** ilimitado
- 🔍 **Buscar y reemplazar** con opción de mayúsculas/minúsculas

### Compilación
- 🛠 **Compilar** programas C++ usando `g++`, `clang++` o `c++`
- 📚 Soporte para estándares **C++11, C++14, C++17 y C++20**
- ⚠️ Advertencias habilitadas (`-Wall`) y símbolos de depuración (`-g`)
- 📊 **Salida del compilador** en pestañas separadas (salida/errores)

### Ejecución
- ▶️ **Ejecutar** programas compilados desde el IDE
- ⌨️ **Argumentos de línea de comandos**
- ⏹ **Detener** procesos en ejecución
- 📟 **Consola integrada** con auto-scroll

### Depuración
- 🐛 **Depuración con GDB** incluida
- 🧩 Compilación automática con símbolos de depuración
- 📍 Información de variables locales y backtrace

### Interfaz
- 📁 **Explorador de archivos** lateral con iconos por tipo
- 🎛 **Barra de herramientas** con botones de compilación, ejecución y depuración
- 📊 **Barra de estado** con información del compilador y posición del cursor
- 🎨 **Tema oscuro** estilo VS Code
- ⌨️ **Atajos de teclado** completos

## 📋 Requisitos

- **Python 3.6+** (incluye Tkinter)
- **Compilador C++** (g++ recomendado)
  - Ubuntu/Debian: `sudo apt install g++`
  - Fedora: `sudo dnf install gcc-c++`
  - Arch: `sudo pacman -S gcc`
  - Windows (MSYS2): `pacman -S mingw-w64-x86_64-gcc`
- **GDB** (opcional, para depuración)
  - Ubuntu/Debian: `sudo apt install gdb`

## 🚀 Instalación y uso

```bash
# Ejecutar el IDE
python3 main.py
```

## ⌨️ Atajos de teclado

| Atajo | Acción |
|-------|--------|
| `Ctrl+N` | Nuevo archivo |
| `Ctrl+O` | Abrir archivo |
| `Ctrl+S` | Guardar |
| `Ctrl+Shift+S` | Guardar como |
| `Ctrl+F` | Buscar |
| `Ctrl+H` | Buscar y reemplazar |
| `Ctrl+G` | Ir a línea |
| `Ctrl+Z` / `Ctrl+Y` | Deshacer / Rehacer |
| `F5` | Ejecutar programa |
| `F6` | Compilar y ejecutar |
| `F7` | Compilar |
| `Shift+F5` | Detener proceso |
| `Ctrl++` / `Ctrl+-` | Zoom del editor |

## 📁 Estructura del proyecto

```
MeriCode-Cplusplus/
├── main.py                    # Punto de entrada principal
├── README.md                  # Documentación
├── ide/
│   ├── __init__.py           # Paquete MeriCode C++
│   ├── main_window.py        # Ventana principal e interfaz gráfica
│   ├── editor.py             # Editor con números de línea
│   ├── syntax_highlighter.py # Resaltador de sintaxis C++
│   ├── compiler.py           # Compilación/ejecución/depuración
│   ├── console.py            # Consola de salida con pestañas
│   └── search_dialog.py      # Diálogo de buscar y reemplazar
```

## 🎯 Ejemplo de uso

1. Abre el IDE con `python3 main.py`
2. Escribe tu código C++ en el editor
3. Presiona **F7** para compilar
4. Prensa **F5** para ejecutar
5. Usa **F6** para compilar y ejecutar en un solo paso
6. Usa el botón **🐛 Depurar** para depurar con GDB

## 🤝 Contribuir

Si deseas contribuir al proyecto:

1. Haz fork del repositorio
2. Crea una rama para tu función
3. Haz commit de tus cambios
4. Haz push a la rama
5. Abre un Pull Request

## 📄 Licencia

© 2026 MERIMAD. Todos los derechos reservados.
