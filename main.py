#!/usr/bin/env python3
"""
MeriCode C++ - Un IDE completo para programar en C++ con Python y Tkinter.

Este es el punto de entrada principal de la aplicación.
Ejecuta la ventana principal del IDE con todos sus componentes:
editor, compilador, depurador, explorador de archivos, etc.
"""

import sys
import os

# Asegurar que el directorio actual esté en el path
# para que los imports del paquete ide funcionen correctamente
# sin importar desde dónde se ejecute el script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Función principal de la aplicación.

    Importa e inicia la ventana principal del IDE.
    Maneja errores de importación y errores generales
    mostrando mensajes claros al usuario.
    """
    try:
        # Importar la función run del módulo main_window
        from ide.main_window import run
        run()
    except ImportError as e:
        # Error si los módulos del IDE no se pueden importar
        print(f"Error al importar módulos: {e}")
        print("Asegúrese de ejecutar este script desde el directorio raíz del proyecto.")
        sys.exit(1)
    except Exception as e:
        # Error general al iniciar la aplicación
        print(f"Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Punto de entrada del script
if __name__ == "__main__":
    main()