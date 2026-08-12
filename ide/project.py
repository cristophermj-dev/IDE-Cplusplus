"""
Gestión de proyectos para MeriCode C++.
Los proyectos se guardan con extensión .cmj (C++ Make/Manage Project).
"""

import os
import json
from datetime import datetime


class Project:
    """Representa un proyecto del IDE."""

    def __init__(self, name="", path="", created=None):
        self.name = name
        self.path = path  # Directorio raíz del proyecto
        self.created = created or datetime.now().isoformat()
        self.std = "c++17"
        self.files = []

    def to_dict(self):
        """Convierte el proyecto a diccionario."""
        return {
            "name": self.name,
            "path": self.path,
            "created": self.created,
            "std": self.std,
            "files": self.files,
        }

    @classmethod
    def from_dict(cls, data):
        """Crea un proyecto desde un diccionario."""
        project = cls(
            name=data.get("name", ""),
            path=data.get("path", ""),
            created=data.get("created"),
        )
        project.std = data.get("std", "c++17")
        project.files = data.get("files", [])
        return project

    def save(self, file_path=None):
        """Guarda el proyecto en un archivo .cmj."""
        if file_path is None:
            file_path = os.path.join(self.path, f"{self.name}.cmj")
        if not file_path.endswith(".cmj"):
            file_path += ".cmj"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return file_path

    @classmethod
    def load(cls, file_path):
        """Carga un proyecto desde un archivo .cmj."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        project = cls.from_dict(data)
        return project

    def scan_files(self):
        """Escanea los archivos del directorio del proyecto."""
        if not self.path or not os.path.isdir(self.path):
            return []

        files = []
        for root, dirs, filenames in os.walk(self.path):
            # Omitir directorios ocultos y build
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
    """Gestiona los proyectos del IDE."""

    def __init__(self):
        self.current_project = None
        self.project_file = None

    def create_project(self, name, directory):
        """Crea un nuevo proyecto."""
        project_dir = os.path.join(directory, name)
        os.makedirs(project_dir, exist_ok=True)

        project = Project(name=name, path=project_dir)
        project_file = project.save()

        # Crear archivo principal main.cpp
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

        self.current_project = project
        self.project_file = project_file
        project.scan_files()
        return project

    def open_project(self, file_path):
        """Abre un proyecto existente."""
        project = Project.load(file_path)
        if not os.path.isdir(project.path):
            # Intentar usar el directorio del archivo .cmj
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
        """Verifica si hay un proyecto abierto."""
        return self.current_project is not None

    def add_class(self, class_name):
        """
        Crea una clase con archivos .h y .cpp.

        Args:
            class_name: Nombre de la clase

        Returns:
            tuple: (header_path, source_path) o None si falla
        """
        if not self.current_project:
            return None

        project_dir = self.current_project.path
        header_path = os.path.join(project_dir, f"{class_name}.h")
        source_path = os.path.join(project_dir, f"{class_name}.cpp")

        # Guardia de inclusión
        guard = class_name.upper() + "_H"

        # Crear archivo .h
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

        # Crear archivo .cpp
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

        with open(header_path, "w", encoding="utf-8") as f:
            f.write(header_content)

        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source_content)

        # Actualizar lista de archivos
        self.current_project.scan_files()
        self.save_project()

        return header_path, source_path

    def save_project(self):
        """Guarda el proyecto actual."""
        if self.current_project:
            self.project_file = self.current_project.save(self.project_file)
            return self.project_file
        return None