"""
Gestión de proyectos para MeriCode C++.
Los proyectos se guardan con extensión .cmj (C++ Make/Manage Project).

Este módulo proporciona las clases Project y ProjectManager para
crear, abrir, guardar y gestionar proyectos del IDE, incluyendo
la creación de clases con archivos .h y .cpp.
"""

import os
import json
from datetime import datetime


class Project:
    """Representa un proyecto del IDE.

    Un proyecto contiene un nombre, una ruta de directorio raíz,
    la fecha de creación, el estándar de C++ utilizado y la lista
    de archivos que lo componen.
    """

    def __init__(self, name="", path="", created=None):
        """
        Inicializa un proyecto.

        Args:
            name: Nombre del proyecto.
            path: Directorio raíz del proyecto.
            created: Fecha de creación (ISO format, opcional).
        """
        self.name = name
        self.path = path  # Directorio raíz del proyecto
        self.created = created or datetime.now().isoformat()
        self.std = "c++17"  # Estándar de C++ por defecto
        self.files = []     # Lista de archivos del proyecto

    def to_dict(self):
        """Convierte el proyecto a diccionario para serialización JSON.

        Returns:
            dict: Diccionario con los datos del proyecto.
        """
        return {
            "name": self.name,
            "path": self.path,
            "created": self.created,
            "std": self.std,
            "files": self.files,
        }

    @classmethod
    def from_dict(cls, data):
        """
        Crea un proyecto desde un diccionario.

        Args:
            data: Diccionario con los datos del proyecto.

        Returns:
            Project: Instancia de Project creada desde el diccionario.
        """
        project = cls(
            name=data.get("name", ""),
            path=data.get("path", ""),
            created=data.get("created"),
        )
        project.std = data.get("std", "c++17")
        project.files = data.get("files", [])
        return project

    def save(self, file_path=None):
        """
        Guarda el proyecto en un archivo .cmj.

        Args:
            file_path: Ruta del archivo .cmj (opcional, usa el directorio del proyecto).

        Returns:
            str: Ruta del archivo guardado.
        """
        # Si no se especifica ruta, usar el directorio del proyecto
        if file_path is None:
            file_path = os.path.join(self.path, f"{self.name}.cmj")
        # Asegurar la extensión .cmj
        if not file_path.endswith(".cmj"):
            file_path += ".cmj"

        # Escribir el proyecto como JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return file_path

    @classmethod
    def load(cls, file_path):
        """
        Carga un proyecto desde un archivo .cmj.

        Args:
            file_path: Ruta del archivo .cmj.

        Returns:
            Project: Instancia de Project cargada desde el archivo.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        project = cls.from_dict(data)
        return project

    def scan_files(self):
        """Escanea los archivos del directorio del proyecto.

        Busca archivos de código fuente C++ (.cpp, .cc, .cxx, .c),
        archivos de cabecera (.h, .hpp, .hh) y archivos de proyecto
        (.cmj), omitiendo directorios ocultos y de build.

        Returns:
            list: Lista de rutas de archivos encontrados.
        """
        # Verificar que el directorio del proyecto exista
        if not self.path or not os.path.isdir(self.path):
            return []

        files = []
        for root, dirs, filenames in os.walk(self.path):
            # Omitir directorios ocultos y de compilación
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("build", "bin", "obj")]
            for filename in filenames:
                if filename.startswith("."):
                    continue
                ext = os.path.splitext(filename)[1].lower()
                if ext in (".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".hh", ".cmj"):
                    full_path = os.path.join(root, filename)
                    files.append(full_path)

        self.files = files
        return files


class ProjectManager:
    """Gestiona los proyectos del IDE.

    Esta clase se encarga de crear, abrir, cerrar y guardar
    proyectos, así como de añadir nuevas clases al proyecto activo.
    """

    def __init__(self):
        """Inicializa el gestor de proyectos."""
        self.current_project = None  # Proyecto actualmente abierto
        self.project_file = None     # Ruta del archivo .cmj del proyecto

    def create_project(self, name, directory):
        """
        Crea un nuevo proyecto.

        Args:
            name: Nombre del proyecto.
            directory: Directorio donde crear el proyecto.

        Returns:
            Project: El proyecto creado.
        """
        # Crear el directorio del proyecto
        project_dir = os.path.join(directory, name)
        os.makedirs(project_dir, exist_ok=True)

        # Crear el objeto Project y guardarlo
        project = Project(name=name, path=project_dir)
        project_file = project.save()

        # Crear el archivo principal main.cpp si no existe
        main_cpp = os.path.join(project_dir, "main.cpp")
        if not os.path.exists(main_cpp):
            with open(main_cpp, "w", encoding="utf-8") as f:
                f.write(
                    '#include <iostream>\n'
                    '\n'
                    'int main() {\n'
                    '    std::cout << "Hola, mundo!" << std::endl;\n'
                    '    return 0;\n'
                    '}\n'
                )

        # Establecer como proyecto actual y escanear archivos
        self.current_project = project
        self.project_file = project_file
        project.scan_files()
        return project

    def open_project(self, file_path):
        """
        Abre un proyecto existente.

        Args:
            file_path: Ruta del archivo .cmj del proyecto.

        Returns:
            Project: El proyecto abierto.
        """
        project = Project.load(file_path)
        # Si la ruta guardada no existe, usar el directorio del archivo .cmj
        if not os.path.isdir(project.path):
            project.path = os.path.dirname(os.path.abspath(file_path))
        project.scan_files()
        self.current_project = project
        self.project_file = file_path
        return project

    def close_project(self):
        """Cierra el proyecto actual."""
        self.current_project = None
        self.project_file = None

    def has_project(self):
        """Verifica si hay un proyecto abierto.

        Returns:
            bool: True si hay un proyecto activo.
        """
        return self.current_project is not None

    def add_class(self, class_name):
        """
        Crea una clase con archivos .h y .cpp.

        Args:
            class_name: Nombre de la clase.

        Returns:
            tuple: (header_path, source_path) o None si falla.
        """
        # Verificar que haya un proyecto abierto
        if not self.current_project:
            return None

        project_dir = self.current_project.path
        header_path = os.path.join(project_dir, f"{class_name}.h")
        source_path = os.path.join(project_dir, f"{class_name}.cpp")

        # Guardia de inclusión para el archivo .h
        guard = class_name.upper() + "_H"

        # Contenido del archivo de cabecera .h
        header_content = (
            f"#ifndef {guard}\n"
            f"#define {guard}\n"
            f"\n"
            f"class {class_name} {{\n"
            f"public:\n"
            f"    {class_name}();\n"
            f"    ~{class_name}();\n"
            f"\n"
            f"private:\n"
            f"}};\n"
            f"\n"
            f"#endif // {guard}\n"
        )

        # Contenido del archivo fuente .cpp
        source_content = (
            f'#include "{class_name}.h"\n'
            f'\n'
            f'{class_name}::{class_name}() {{\n'
            f'    // Constructor\n'
            f'}}\n'
            f'\n'
            f'{class_name}::~{class_name}() {{\n'
            f'    // Destructor\n'
            f'}}\n'
        )

        # Escribir los archivos de la clase
        with open(header_path, "w", encoding="utf-8") as f:
            f.write(header_content)

        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source_content)

        # Actualizar la lista de archivos y guardar el proyecto
        self.current_project.scan_files()
        self.save_project()

        return header_path, source_path

    def save_project(self):
        """Guarda el proyecto actual.

        Returns:
            str: Ruta del archivo guardado, o None si no hay proyecto.
        """
        if self.current_project:
            self.project_file = self.current_project.save(self.project_file)
            return self.project_file
        return None