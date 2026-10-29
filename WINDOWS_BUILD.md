# 🪟 Generar el ejecutable (.exe) de Windows

Este documento explica cómo generar el **ejecutable** de DevQbo para
Windows y el **instalador** que, además, instala automáticamente todo lo
necesario para compilar (`g++`), depurar (`gdb`) y usar GitHub (`git`).

> ⚠️ **Importante:** un `.exe` de Windows no se puede compilar *desde Linux*
> (PyInstaller no hace compilación cruzada). Por eso hay dos caminos:

---

## Método A (recomendado): generar el .exe en la nube, sin Windows

El repositorio ya está en GitHub, así que puedes compilarlo con **GitHub
Actions** (runner de Windows) y descargar el resultado:

1. Sube estos archivos al repositorio (`git add` + `git commit` + `git push`).
2. En GitHub ve a la pestaña **Actions**.
3. Selecciona el workflow **"Build Windows (.exe + instalador)"**.
4. Pulsa **Run workflow** (rama `Desarrollo` o `main`).
5. Cuando termine, entra al job y descarga el artefacto **DevQbo-Windows**:
   - `DevQbo.exe` → ejecutable portable (no necesita instalación).
   - `DevQbo-Setup.exe` → instalador que instala IDE + compilador + git.

> Alternativa: también se dispara solo al crear un *tag* `v*` (`git tag v1.0.0`
> y `git push origin v1.0.0`).

---

## Método B: compilar en tu propio Windows

### Requisitos
- Windows 10/11 (64 bits).
- **Python 3.10–3.12** instalado y marcado "Add Python to PATH".
  👉 https://www.python.org/downloads/windows/
- (Opcional, para el instalador) **Inno Setup 6**:
  👉 https://jrsoftware.org/isinfo.php

### 1) Generar el ejecutable

Abre una terminal (cmd) en la carpeta del proyecto y ejecuta:

```bat
build_windows.bat
```

Esto instala PyInstaller y genera:

```
dist\DevQbo.exe
```

### 2) Generar el instalador (opcional)

Abre `installer.iss` con Inno Setup 6 y pulsa **Compilar** (o ejecuta
`ISCC.exe installer.iss`). Genera:

```
dist\DevQbo-Setup.exe
```

El instalador:
- Instala el IDE en `C:\Program Files\DevQbo`.
- Descarga e instala **Git para Windows**.
- Descarga e instala **MinGW-w64** (que incluye `g++` y `gdb`).
- Añade el compilador al **PATH** del sistema.
- Crea accesos directos en el menú Inicio y el escritorio.

> La primera instalación descarga ~300 MB (MinGW). Necesita conexión a
> Internet y permisos de administrador.

---

## ¿Qué se corrigió para que funcione bien en Windows?

- `ide/main_window.py`: se sustituyó `subprocess.run(["which","gdb"])`
  (comando de Unix que no existe en Windows) por `shutil.which("gdb")`.
- `ide/compiler.py` y `ide/github_sync.py`: los `subprocess` usan ahora
  `creationflags=CREATE_NO_WINDOW` en Windows, para que no aparezcan ventanas
  de consola parpadeantes al compilar/ejecutar/depurar.

---

## Notas

- El IDE detecta `g++` automáticamente al arrancar (ver barra de estado).
- Si tras instalar no detecta el compilador, cierra y vuelve a abrir el IDE
  (o cierra sesión) para que Windows refresque el `PATH`.
- Para actualizar la versión de Git/MinGW, edita las URLs al inicio de
  `install_toolchain.ps1`.
