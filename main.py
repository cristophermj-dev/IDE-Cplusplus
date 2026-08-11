#!/usr/bin/env python3
"""
IDE C++ - Un IDE completo para programar en C++ con Python y Tkinter.

Punto de entrada principal de la aplicación.
"""

import sys
import os

# Asegurar que el directorio actual esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Función principal de la aplicación."""
    try:
        from ide.main_window import run
        run()
    except ImportError as e:
        print(f"Error al importar módulos: {e}")
        print("Asegúrese de ejecutar este script desde el directorio raíz del proyecto.")
        sys.exit(1)
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()