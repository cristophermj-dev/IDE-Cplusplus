"""
Módulo para compilar, ejecutar y depurar programas C++.
"""

import os
import subprocess
import threading
import tempfile
import shutil
import sys
import platform


class Compiler:
    """Maneja la compilación, ejecución y depuración de código C++."""

    def __init__(self):
        """Inicializa el compilador."""
        self.process = None
        self.is_compiling = False
        self.is_running = False
        self.is_debugging = False
        self._cancel_flag = False
        self._check_compiler()

    def _check_compiler(self):
        """Verifica si hay un compilador C++ disponible."""
        candidates = []
        if platform.system() == "Windows":
            candidates = [
                ("g++", ["g++", "--version"]),
                ("clang++", ["clang++", "--version"]),
                ("cl", ["cl", "/?"]),
            ]
        else:
            candidates = [
                ("g++", ["g++", "--version"]),
                ("clang++", ["clang++", "--version"]),
                ("c++", ["c++", "--version"]),
            ]

        for name, cmd in candidates:
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=5
                )
                if result.returncode in (0, 1):  # cl puede retornar 1
                    self.compiler_name = name
                    self.compiler_cmd = cmd[0]
                    # Extraer versión
                    first_line = result.stdout.split("\n")[0] or result.stderr.split("\n")[0]
                    self.compiler_version = first_line.strip()
                    return
            except (subprocess.SubprocessError, FileNotFoundError):
                continue

        self.compiler_name = None
        self.compiler_cmd = None
        self.compiler_version = "No se encontró compilador"

    def is_available(self):
        """Verifica si hay un compilador disponible."""
        return self.compiler_cmd is not None

    def get_compiler_info(self):
        """Obtiene información del compilador."""
        return {
            "name": self.compiler_name,
            "version": self.compiler_version,
            "available": self.is_available(),
        }

    def compile_source(self, source_file, output_file=None, std="c++17",
                       extra_flags=None, on_output=None, on_done=None):
        """
        Compila un archivo fuente C++ en un hilo separado.

        Args:
            source_file: Ruta del archivo .cpp
            output_file: Ruta del ejecutable de salida
            std: Estándar de C++ (c++11, c++14, c++17, c++20)
            extra_flags: Lista de flags adicionales para el compilador
            on_output: Callback para la salida del proceso
            on_done: Callback al finalizar (recibe el código de retorno)
        """
        if not self.is_available():
            if on_output:
                on_output(
                    "Error: No se encontró un compilador C++.\n"
                    "Instale g++ o clang++ para usar esta función.\n",
                    "error"
                )
            if on_done:
                on_done(1)
            return None

        if not os.path.exists(source_file):
            if on_output:
                on_output(f"Error: No existe el archivo {source_file}\n", "error")
            if on_done:
                on_done(1)
            return None

        if output_file is None:
            base = os.path.splitext(source_file)[0]
            output_file = self._get_executable_name(base)

        flags = [self.compiler_cmd, "-std=" + std, source_file, "-o", output_file]
        if extra_flags:
            flags.extend(extra_flags)

        self.is_compiling = True
        self._cancel_flag = False

        thread = threading.Thread(
            target=self._compile_thread,
            args=(flags, on_output, on_done),
            daemon=True,
        )
        thread.start()
        return thread

    def _compile_thread(self, flags, on_output, on_done):
        """Hilo de compilación."""
        try:
            if on_output:
                on_output("Compilando...\n", "info")

            self.process = subprocess.Popen(
                flags,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            stdout_lines = []
            stderr_lines = []

            for line in self.process.stdout:
                stdout_lines.append(line)
                if on_output:
                    on_output(line, "normal")

            for line in self.process.stderr:
                stderr_lines.append(line)
                if on_output:
                    on_output(line, "error")

            self.process.wait()
            returncode = self.process.returncode

            if returncode == 0:
                if on_output:
                    on_output("✓ Compilación exitosa\n", "success")
            else:
                if on_output:
                    on_output(f"✗ Error de compilación (código {returncode})\n", "error")

            if on_done:
                on_done(returncode)

        except Exception as e:
            if on_output:
                on_output(f"Error: {str(e)}\n", "error")
            if on_done:
                on_done(1)
        finally:
            self.is_compiling = False
            self.process = None

    def run_program(self, executable, args=None, cwd=None,
                    on_output=None, on_done=None):
        """
        Ejecuta un programa compilado.

        Args:
            executable: Ruta del ejecutable
            args: Lista de argumentos para el programa
            cwd: Directorio de trabajo
            on_output: Callback para la salida del proceso
            on_done: Callback al finalizar
        """
        if not os.path.exists(executable):
            if on_output:
                on_output(f"Error: No existe el ejecutable {executable}\n", "error")
            if on_done:
                on_done(1)
            return None

        cmd = [executable]
        if args:
            cmd.extend(args)

        self.is_running = True
        self._cancel_flag = False

        thread = threading.Thread(
            target=self._run_thread,
            args=(cmd, cwd, on_output, on_done),
            daemon=True,
        )
        thread.start()
        return thread

    def _run_thread(self, cmd, cwd, on_output, on_done):
        """Hilo de ejecución."""
        try:
            if on_output:
                on_output(f"$ {' '.join(cmd)}\n", "info")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=cwd,
            )

            # Leer stdout y stderr en hilos separados
            def read_stream(stream, is_error):
                for line in stream:
                    if on_output:
                        on_output(line, "error" if is_error else "normal")

            t1 = threading.Thread(target=read_stream, args=(self.process.stdout, False), daemon=True)
            t2 = threading.Thread(target=read_stream, args=(self.process.stderr, True), daemon=True)
            t1.start()
            t2.start()

            self.process.wait()
            t1.join()
            t2.join()

            returncode = self.process.returncode
            if on_output:
                on_output(f"\nProceso terminado con código {returncode}\n", "info")

            if on_done:
                on_done(returncode)

        except Exception as e:
            if on_output:
                on_output(f"Error: {str(e)}\n", "error")
            if on_done:
                on_done(1)
        finally:
            self.is_running = False
            self.process = None

    def debug_program(self, executable, source_file, on_output=None, on_done=None):
        """
        Inicia una sesión de depuración con GDB.

        Args:
            executable: Ruta del ejecutable
            source_file: Ruta del archivo fuente para símbolos
            on_output: Callback para la salida
            on_done: Callback al finalizar
        """
        # Detectar gdb
        gdb_path = shutil.which("gdb")
        if not gdb_path:
            if on_output:
                on_output(
                    "Error: GDB no está instalado.\n"
                    "Instale gdb para usar la depuración (ej: sudo apt install gdb)\n",
                    "error"
                )
            if on_done:
                on_done(1)
            return None

        if not os.path.exists(executable):
            if on_output:
                on_output(f"Error: No existe el ejecutable {executable}\n", "error")
            if on_done:
                on_done(1)
            return None

        # Crear un script de GDB para modo batch
        script_file = None
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="ide_cpp_")
            script_file = os.path.join(temp_dir, "gdb_script.txt")

            # Compilado con -g para símbolos de depuración
            gdb_script = f"""
set pagination off
set confirm off
file {executable}
break main
run
info locals
bt
quit
"""
            with open(script_file, "w") as f:
                f.write(gdb_script)

            self.is_debugging = True
            cmd = [gdb_path, "-x", script_file, "-batch"]

            if on_output:
                on_output("Iniciando depuración con GDB...\n", "info")

            thread = threading.Thread(
                target=self._debug_thread,
                args=(cmd, on_output, on_done),
                daemon=True,
            )
            thread.start()
            return thread

        except Exception as e:
            if on_output:
                on_output(f"Error al preparar depuración: {str(e)}\n", "error")
            if script_file and os.path.exists(script_file):
                try:
                    os.remove(script_file)
                except OSError:
                    pass
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except OSError:
                    pass
            if on_done:
                on_done(1)
            return None

    def _debug_thread(self, cmd, on_output, on_done):
        """Hilo de depuración."""
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = self.process.communicate()

            if stdout and on_output:
                on_output(stdout, "debug")
            if stderr and on_output:
                on_output(stderr, "error")

            returncode = self.process.returncode
            if on_output:
                on_output(f"\nSesión de depuración finalizada (código {returncode})\n", "info")

            if on_done:
                on_done(returncode)

        except Exception as e:
            if on_output:
                on_output(f"Error: {str(e)}\n", "error")
            if on_done:
                on_done(1)
        finally:
            self.is_debugging = False
            self.process = None

    def compile_and_run(self, source_file, args=None, on_output=None, on_done=None):
        """
        Compila y ejecuta un archivo fuente en secuencia.

        Args:
            source_file: Ruta del archivo .cpp
            args: Argumentos para el programa
            on_output: Callback para la salida
            on_done: Callback al finalizar
        """
        def handle_compile(returncode):
            if returncode == 0:
                base = os.path.splitext(source_file)[0]
                executable = self._get_executable_name(base)
                self.run_program(executable, args, on_output=on_output, on_done=on_done)
            elif on_done:
                on_done(returncode)

        self.compile_source(source_file, on_output=on_output, on_done=handle_compile)

    def _get_executable_name(self, base_path):
        """Obtiene el nombre del ejecutable según la plataforma."""
        if platform.system() == "Windows":
            return base_path + ".exe"
        return base_path

    def stop(self):
        """Detiene el proceso en ejecución."""
        self._cancel_flag = True
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                # En Windows, usar taskkill para matar el proceso y sus hijos
                if platform.system() == "Windows":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                        capture_output=True,
                    )
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

    def is_busy(self):
        """Verifica si el compilador está ocupado."""
        return self.is_compiling or self.is_running or self.is_debugging

    def get_status_message(self):
        """Obtiene un mensaje de estado del compilador."""
        if not self.is_available():
            return "Sin compilador"
        if self.is_compiling:
            return "Compilando..."
        if self.is_running:
            return "Ejecutando..."
        if self.is_debugging:
            return "Depurando..."
        return f"Listo - {self.compiler_name} {self.compiler_version.split()[-1] if self.compiler_version else ''}"